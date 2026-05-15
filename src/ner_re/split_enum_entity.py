import re
from copy import deepcopy
from src.ner_re.common import get_article_number_from_node_id
def save_current_ref(results, diem_list, khoan, dieu, suffix):
    if diem_list:
        for d in diem_list:
            s = f"điểm {d}"
            if khoan:
                s += f" khoản {khoan}"
            if dieu:
                s += f" điều {dieu}"
            if suffix:
                s += f" {suffix}"
            results.append(s)
    elif khoan and dieu:
        s = f"khoản {khoan} điều {dieu}"
        if suffix:
            s += f" {suffix}"
        results.append(s)
    elif dieu:
        s = f"điều {dieu}"
        if suffix:
            s += f" {suffix}"
        results.append(s)

def expand_legal_refs(text,node_id=None):
    """
    Mở rộng các tham chiếu pháp luật có enumeration
    VD: 'điểm đ và điểm e khoản 1 điều 2 của luật này'
    => ['điểm đ khoản 1 điều 2 của luật này', 'điểm e khoản 1 điều 2 của luật này']
    """
    m = re.search(r"(của .+)$", text, re.I)
    suffix = m.group(1) if m else ""
    main = text[:m.start()].strip() if m else text
    pattern = re.compile(
        r"điểm\s+[a-zđ]"
        r"|khoản\s+\d+[a-z]?"
        r"|điều\s+\d+[a-z]?",
        re.I
    )

    tokens = pattern.findall(main)

    results = []

    diem_list = []
    khoan = None
    dieu = None
    for token in tokens:
        if token.startswith("điểm"):
            value = token.split()[1]
            # điều 18, điểm a ... => lấy điều 18 truoc
            if dieu and not khoan and not diem_list:
                save_current_ref(results, [], None, dieu, suffix)
                diem_list = []
                khoan = None
                dieu = None
            diem_list.append(value)
        elif token.startswith("khoản"):
            value = token.split()[1]
            # khoản 1 điều 18, khoản 2 => dieu -> khoan -> luu cai cu , xu ly cai moi 
            if khoan and dieu:
                save_current_ref(results,diem_list,khoan,dieu,suffix)
                diem_list = []
                khoan = None
                dieu = None
            # điều 18, khoản 1 => luu dieu 18

            elif dieu and not khoan and not diem_list:
                save_current_ref(results,[],None,dieu,suffix)
                dieu = None
            khoan = value

        elif token.startswith("điều"):
            value = token.split()[1]
            if dieu:
                save_current_ref(results,diem_list,khoan,dieu,suffix)
                diem_list = []
                khoan = None
                dieu = None

            dieu = value

    save_current_ref(results,diem_list,khoan,dieu,suffix)
    return results 


def build_full_reference(current, template):
    """
    Xây dựng tham chiếu đầy đủ bằng cách merge current với template
    """
    # Sử dụng giá trị từ current, fallback về template
    merged = {
        'diem': current.get('diem', template.get('diem')),
        'khoan': current.get('khoan', template.get('khoan')),
        'dieu': current.get('dieu', template.get('dieu'))
    }
    
    # Xây dựng chuỗi theo thứ tự: điểm -> khoản -> điều
    parts = []
    
    if merged.get('diem'):
        parts.append(f"điểm {merged['diem']}")
    
    if merged.get('khoan'):
        parts.append(f"khoản {merged['khoan']}")
    
    if merged.get('dieu'):
        parts.append(f"điều {merged['dieu']}")
    
    return " ".join(parts) if parts else ""



def split_non_legal_entity(text):
    # Split text theo 
    # a) b) c) d) . ; : \n => split 
    # thay thế các từ nối

    # split a b c 
    parts = re.split(r'\s*[a-z]\)\s*', text)

    # Nếu không có pattern a) b) c) split theo dau cau 
    if len(parts) <= 1:
        parts = re.split(r'[.:;]', text)

    #Clean và filter
    result = []
    for part in parts:
        cleaned = part.strip().rstrip(';:')  # Loại bỏ dấu ; : ở cuối
        if cleaned:  # Bỏ qua phần rỗng
            result.append(cleaned)

    # clean kể cả ko split 
    if not result:
        cleaned_text = text.strip().rstrip(';:')
        return [cleaned_text] if cleaned_text else []
    
    return result

def normalize_legalref_text(text,node_id):
    # "Điều này" => Điều hiện tại = get từ node id 
    current_article = get_article_number_from_node_id(node_id) if node_id else None

    # thay "Điều này" bằng số điều thực tế trước khi parse
    if current_article:
        text = re.sub(r'điều\s+này', f'điều {current_article}', text)
        
    text = re.sub(r'bộ\s+luật\s+này', 'bộ luật lao động', text, flags=re.I)
    return text


def split_enum_entities(raw_entities):
    splited_entities = deepcopy(raw_entities)
    
    for node in splited_entities:
        new_entities = []
        node_id = node.get("node_id", "") 
        original_sentence = node.get("sentence", "")
        for ent in node["entities"]:

            original_text = ent["text"]

            normalize_text = normalize_legalref_text(original_text,node_id)
            
            # Kiểm tra có phải legal reference không
            is_legal_ref = (ent["type"] == "LEGAL_REF" and re.search(r'(điều|khoản|điểm)\s+[\w\dđ]+', normalize_text))
            
            if is_legal_ref:
                # Expand legal references
                expanded_refs = expand_legal_refs(normalize_text,node_id)
                
                # Tạo entity mới cho mỗi reference
                for ref in expanded_refs:
                    new_ent = {
                        "type": ent["type"],
                        "text": ref,
                        "span": ent["span"],  # Giữ span gốc
                        "source": ent["source"]
                    }
                    new_entities.append(new_ent)
            else:
                # Split non-legal entities theo enumeration pattern
                sub_texts = split_non_legal_entity(normalize_text)
                
                for sub_text in sub_texts:
                    # Tìm vị trí của sub_text trong sentence gốc
                    span_start = original_sentence.find(sub_text)
                    if span_start != -1:
                        span_end = span_start + len(sub_text)
                        new_span = [span_start, span_end]
                    else:
                        new_span = ent["span"].copy()
                    new_ent = {
                        "type": ent["type"],  # Giữ nguyên type gốc
                        "text": sub_text, 
                        "span": new_span, #Span mới tương ứng với sub_text
                        "source": ent["source"]
                    }

                    new_entities.append(new_ent)    
        node["entities"] = new_entities
    
    return splited_entities



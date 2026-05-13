import re
from copy import deepcopy

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

def expand_legal_refs(text):
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



# def expand_legal_references(text):
#     """
#     Mở rộng các tham chiếu pháp luật có enumeration
#     VD: 'điểm đ và điểm e khoản 1 điều 2 của luật này'
#     => ['điểm đ khoản 1 điều 2 của luật này', 'điểm e khoản 1 điều 2 của luật này']
#     """
#     # Tách suffix (của ... cuối câu)
#     suffix_match = re.search(r'(của\s+.+?)$', text)
#     suffix = suffix_match.group(1) if suffix_match else ""
    
#     # Phần chính (loại bỏ suffix)
#     main_text = text[:text.rfind(suffix)].strip() if suffix else text.strip()
    
#     # Tách theo dấu phẩy và "và"
#     parts = re.split(r',\s*(?:và\s+)?|\s+và\s+', main_text)
    
#     # Tìm template đầy đủ nhất (có nhiều từ khóa nhất)
#     # VD: "điểm đ" vs "điểm e khoản 1 điều 2" => chọn cái sau làm template
#     template = max(parts, key=lambda p: len(re.findall(r'(điều|khoản|điểm)', p)))
    
#     # Parse template để lấy cấu trúc đầy đủ
#     structure = parse_legal_structure(template)
    
#     results = []
#     for part in parts:
#         part = part.strip()
#         if not part:
#             continue
        
#         # Parse phần hiện tại
#         current_structure = parse_legal_structure(part)
        
#         # Merge với template để tạo tham chiếu đầy đủ
#         full_ref = build_full_reference(current_structure, structure)
        
#         # Thêm suffix
#         if suffix:
#             full_ref += " " + suffix
        
#         results.append(full_ref)
    
#     return results if len(results) > 1 else [text]


# def parse_legal_structure(text):
#     """
#     Parse cấu trúc tham chiếu pháp luật
#     VD: 'điểm e khoản 1 điều 2' => {'diem': 'e', 'khoan': '1', 'dieu': '2'}
#     """
#     structure = {}
    
#     # Tìm điều
#     dieu_match = re.search(r'điều\s+(\d+[a-z]?)', text)
#     if dieu_match:
#         structure['dieu'] = dieu_match.group(1)
    
#     # Tìm khoản
#     khoan_match = re.search(r'khoản\s+(\d+[a-z]?)', text)
#     if khoan_match:
#         structure['khoan'] = khoan_match.group(1)
    
#     # Tìm điểm
#     diem_match = re.search(r'điểm\s+([a-zđ])', text)
#     if diem_match:
#         structure['diem'] = diem_match.group(1)
    
#     return structure


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



def split_enum_entities(raw_entities):
    splited_entities = deepcopy(raw_entities)
    
    for node in splited_entities:
        new_entities = []
        original_sentence = node.get("sentence", "")
        for ent in node["entities"]:

            original_text = ent["text"]
            
            # Kiểm tra có phải legal reference không
            is_legal_ref = (ent["type"] == "LEGAL_REF" and re.search(r'(điều|khoản|điểm)\s+[\w\dđ]+', original_text))
            
            if is_legal_ref:
                # Expand legal references
                expanded_refs = expand_legal_refs(original_text)
                
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
                sub_texts = split_non_legal_entity(original_text)
                
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



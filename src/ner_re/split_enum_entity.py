import re
from copy import deepcopy

def expand_legal_references(text):
    """
    Mở rộng các tham chiếu pháp luật có enumeration
    VD: 'điểm đ và điểm e khoản 1 điều 2 của luật này'
    => ['điểm đ khoản 1 điều 2 của luật này', 'điểm e khoản 1 điều 2 của luật này']
    """
    # Tách suffix (của ... cuối câu)
    suffix_match = re.search(r'(của\s+.+?)$', text)
    suffix = suffix_match.group(1) if suffix_match else ""
    
    # Phần chính (loại bỏ suffix)
    main_text = text[:text.rfind(suffix)].strip() if suffix else text.strip()
    
    # Tách theo dấu phẩy và "và"
    parts = re.split(r',\s*(?:và\s+)?|\s+và\s+', main_text)
    
    # Tìm template đầy đủ nhất (có nhiều từ khóa nhất)
    # VD: "điểm đ" vs "điểm e khoản 1 điều 2" => chọn cái sau làm template
    template = max(parts, key=lambda p: len(re.findall(r'(điều|khoản|điểm)', p)))
    
    # Parse template để lấy cấu trúc đầy đủ
    structure = parse_legal_structure(template)
    
    results = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Parse phần hiện tại
        current_structure = parse_legal_structure(part)
        
        # Merge với template để tạo tham chiếu đầy đủ
        full_ref = build_full_reference(current_structure, structure)
        
        # Thêm suffix
        if suffix:
            full_ref += " " + suffix
        
        results.append(full_ref)
    
    return results if len(results) > 1 else [text]


def parse_legal_structure(text):
    """
    Parse cấu trúc tham chiếu pháp luật
    VD: 'điểm e khoản 1 điều 2' => {'diem': 'e', 'khoan': '1', 'dieu': '2'}
    """
    structure = {}
    
    # Tìm điều
    dieu_match = re.search(r'điều\s+(\d+[a-z]?)', text)
    if dieu_match:
        structure['dieu'] = dieu_match.group(1)
    
    # Tìm khoản
    khoan_match = re.search(r'khoản\s+(\d+[a-z]?)', text)
    if khoan_match:
        structure['khoan'] = khoan_match.group(1)
    
    # Tìm điểm
    diem_match = re.search(r'điểm\s+([a-zđ])', text)
    if diem_match:
        structure['diem'] = diem_match.group(1)
    
    return structure


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


def split_enumeration(text):
    """Tách enumeration thông thường (không phải legal reference)"""
    text = text.replace(" và ", ",")
    text = text.replace(" hoặc ", ",")
    text = text.replace(", bao gồm cả", ",")
    text = text.replace('a)', ',')
    text = text.replace('b)', ',')
    text = text.replace('c)', ',')
    text = text.replace(";", ",")
    text = text.strip()
    
    parts = text.split(",")
    result = []
    for part in parts:
        cleaned = part.strip()
        if cleaned:
            result.append(cleaned)
    return result


def split_enum_entities(raw_entities):
    splited_entities = deepcopy(raw_entities)
    
    for node in splited_entities:
        new_entities = []
        
        for ent in node["entities"]:
            original_text = ent["text"]
            
            # Kiểm tra có phải legal reference không
            is_legal_ref = (ent["type"] == "LEGAL_REF" and re.search(r'(điều|khoản|điểm)\s+[\w\dđ]+', original_text))
            
            if is_legal_ref:
                # Expand legal references
                expanded_refs = expand_legal_references(original_text)
                
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
                # Non-legal reference - dùng logic cũ
                parts = split_enumeration(original_text)
                
                if len(parts) == 1:
                    new_entities.append(ent)
                else:
                    parent_start = ent["span"][0]
                    search_pos = 0
                    
                    for part in parts:
                        idx = original_text.find(part, search_pos)
                        if idx == -1:
                            continue
                        
                        start = parent_start + idx
                        end = start + len(part)
                        
                        new_ent = {
                            "type": ent["type"],
                            "text": part,
                            "span": [start, end],
                            "source": ent["source"]
                        }
                        new_entities.append(new_ent)
                        search_pos = idx + len(part)
        
        node["entities"] = new_entities
    
    return splited_entities



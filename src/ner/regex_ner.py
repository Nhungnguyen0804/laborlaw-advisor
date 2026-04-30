import re 
from src.utils.file_utils import load_json, save_json
from src.utils.paths import LABORLAW_CHUNKS_JSON, LABORLAW_ENTITIES_JSON
import unicodedata
from src.ner.patterns import PATTERNS
# Compile patterns
COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]

def clean_condition(text):
    text = text.strip()
    if text.endswith("thì"):
        return text[:-3].rstrip()
    return text

def clean_legal_role(text):
    return text


def remove_leading_thi(text):
    text = text.lstrip()
    if text.startswith("thì"):
        return text[3:].lstrip()
    return text



def clean_right(text):
    """
    Làm sạch text đã match:
    - Bỏ câu bắt đầu bằng "quy định"
    - Bỏ phần sau: "nhưng", "khi", "trường hợp", "trừ trường hợp"
    """
    text = text.strip()
    text = remove_leading_thi(text)
    # Bỏ nếu bắt đầu bằng "quy định"
    if text.startswith('quy định'):
        return None
    
    # Tìm vị trí cắt sớm nhất (KHÔNG BẮT BUỘC dấu phẩy)
    stop_patterns = [
        r'\s+trước\s+và\s+sau\s+khi\b', 
        r'\s+trừ\s+trường\s+hợp\b',
        r'\s+trường\s+hợp\b',
        r'\s+nhưng\b',
        r'\s+(trước\s+khi|sau\s+khi)\b',
        r'\s+khi\b',
        
        
    ]
    
    earliest_pos = len(text)
    for pattern in stop_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()
    
    # Cắt text
    cleaned = text[:earliest_pos].strip()
    
    # Loại bỏ dấu phẩy/chấm cuối
    cleaned = cleaned.rstrip('.,')
    
    return cleaned if cleaned else None


def clean_obligation(text):
    """
    Làm sạch text đã match:
    - Bỏ câu bắt đầu bằng "quy định"
    - Bỏ phần sau: "nhưng", "khi", "trường hợp", "trừ trường hợp"
    """
    text = text.strip()
    text =remove_leading_thi(text)
    # Bỏ nếu bắt đầu bằng "quy định"
    if text.startswith('quy định'):
        return None
    
    # Tìm vị trí cắt sớm nhất (KHÔNG BẮT BUỘC dấu phẩy)
    stop_patterns = [
        r'\s+trước\s+và\s+sau\s+khi\b', 
        r'\s+trừ\s+trường\s+hợp\b',
        r'\s+(?:hoặc\s+về\s+)?trường\s+hợp\b',
        r'\s+trường\s+hợp\b',
        r'\s+nhưng\b',
        r'\s+(trước\s+khi|sau\s+khi)\b',
        r'\s+khi\b',
        
        
    ]
    
    earliest_pos = len(text)
    for pattern in stop_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()
    
    # Cắt text
    cleaned = text[:earliest_pos].strip()
    
    # Loại bỏ dấu phẩy/chấm cuối
    cleaned = cleaned.rstrip('.,')
    
    return cleaned if cleaned else None

  

def remove_leading_thi(text):
    text = text.lstrip()
    if text.startswith("thì"):
        return text[3:].lstrip()
    return text

def clean_prohibition(text):
    """
    Làm sạch text đã match:
    - Bỏ câu bắt đầu bằng "quy định"
    - Bỏ phần sau: "nhưng", "khi", "trường hợp", "trừ trường hợp"
    """
    text = text.strip()
    text = remove_leading_thi(text)
    # Bỏ nếu bắt đầu bằng "quy định"
    if text.startswith('quy định'):
        return None
    
    # Tìm vị trí cắt sớm nhất (KHÔNG BẮT BUỘC dấu phẩy)
    stop_patterns = [
        r'\s+trước\s+và\s+sau\s+khi\b', 
        r'\s+trừ\s+trường\s+hợp\b',
        r'\s+(?:hoặc\s+về\s+)?trường\s+hợp\b',
        r'\s+trường\s+hợp\b',
        r'\s+nhưng\b',
        r'\s+(trước\s+khi|sau\s+khi)\b',
        r'\s+khi\b',
        
        
    ]
    
    earliest_pos = len(text)
    for pattern in stop_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()
    
    # Cắt text
    cleaned = text[:earliest_pos].strip()
    
    # Loại bỏ dấu phẩy/chấm cuối
    cleaned = cleaned.rstrip('.,')
    
    return cleaned if cleaned else None

 

def clean_time_period(text):
    return text

def clean_action(text):
    return text 


def clean_legal_concept(text):
    return text 

def clean_event(text):
    return text 

def clean_penalty(text):
    text = text.strip()
    if text.endswith(","):
        return text[:-1].rstrip()
    return text

def clean_purpose(text):
    return text 

def clean_procedure(text):
    return text

def clean_legal_ref(text):
    return text 

# Mapping entity_type -> cleaning function
CLEANERS = {
    "LEGAL_ROLE": clean_legal_role,
    "RIGHT": clean_right,
    "OBLIGATION": clean_obligation,
    "PROHIBITION": clean_prohibition,
    "TIME_PERIOD": clean_time_period,
    "CONDITION": clean_condition,
    "ACTION": clean_action,
    "LEGAL_CONCEPT": clean_legal_concept,
    "EVENT": clean_event,
    "PENALTY": clean_penalty,
    "PURPOSE": clean_purpose,
    "PROCEDURE": clean_procedure,
    "LEGAL_REF": clean_legal_ref,
}

def extract_entity(text: str, entity_type: str, pattern) -> list[dict]:
    """
    Extract 1 loại entity với pattern cụ thể, áp dụng cleaner tương ứng
    """
    matches = []
    cleaner = CLEANERS.get(entity_type, lambda x: x.strip())  # default cleaner
    
    for match in pattern.finditer(text):
        matched_text = match.group().strip()
        
        # Áp dụng cleaner riêng cho entity_type
        cleaned_text = cleaner(matched_text)
        
        if cleaned_text and match.start() != match.end():
            matches.append({
                "entity_type": entity_type,
                "text": cleaned_text,
                "start": match.start(),
                "end": match.end(),
            })
    
    return matches

def extract_entities(text: str) -> list[dict]:
    """Extract tất cả entities - giữ nguyên format output"""
    # Chuẩn hóa text
    text = text.lower()
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'[\u00A0\u200B\u200C\u200D\uFEFF]', ' ', text)
    text = re.sub(r' +', ' ', text)
    
    all_matches = []
    
    # Duyệt qua từng entity type
    for entity_type, compiled_patterns in COMPILED.items():
        for pattern in compiled_patterns:
            # Gọi hàm extract_entity để xử lý riêng
            matches = extract_entity(text, entity_type, pattern)
            all_matches.extend(matches)
    
    return all_matches

def get_entity_summary(chunk):
    """Extract entities và tạo summary"""
    content = chunk.get("content", "")
    entities = extract_entities(content)
    
    # Gom theo loại (giữ nguyên tất cả, kể cả trùng)
    entity_summary = {}
    for e in entities:
        e_type = e["entity_type"]
        if e_type not in entity_summary:
            entity_summary[e_type] = []
        entity_summary[e_type].append(e["text"])
    
    return {
        "chunk_id": chunk["chunk_id"],
        "chunk_type": chunk["chunk_type"],
        "content": content,
        "entities": entities,
        "entity_summary": entity_summary,
        "entity_count": len(entities),
    }


def run_ner():
    """Chạy NER cho toàn bộ chunks"""
    data = load_json(LABORLAW_CHUNKS_JSON)
    chunks = data["chunks"]
    
    results = []
    for chunk in chunks:
        result = get_entity_summary(chunk)
        results.append(result)
    
    total_entities = sum(r["entity_count"] for r in results)
    print(f"Xử lý {len(results)} chunk, tìm được {total_entities} entities")
    
    output = {
        "metadata": data.get("metadata", {}),
        "total_chunks_processed": len(results),
        "total_entities_found": total_entities,
        "results": results,
    }
    
    save_json(output, LABORLAW_ENTITIES_JSON)
    return results


if __name__ == "__main__":
    run_ner()
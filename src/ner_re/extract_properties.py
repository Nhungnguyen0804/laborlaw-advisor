BASE_ROLES = [
    "người sử dụng lao động",
    "hội đồng trọng tài lao động",
    "người lao động",
    "tòa án nhân dân",
    "bên tranh chấp",
    "doanh nghiệp",
    "cơ quan",
    "cá nhân",
    "tổ chức",
    "đơn vị sử dụng lao động",
]


ATTRIBUTES = [
    "đang nghỉ thai sản",
    "nghỉ thai sản",
    "nuôi con dưới 12 tháng tuổi",
    "không phải là cá nhân",
    "không phải cá nhân",
    "chấm dứt hoạt động",
    "mang thai",
    "người nước ngoài",
    "nước ngoài",
    "khuyết tật",
    "cao tuổi",
    "chưa thành niên",
    "không trọn thời gian",
    "trọn thời gian",
    "thuê lại",
    "nhập ngũ",
    "nữ",
    "nam",
]

ATTRIBUTE_PATTERNS = [
    r"đủ\s*\d+\s*tuổi",
    r"chưa\s*đủ\s*\d+\s*tuổi",
    r"từ\s*đủ\s*\d+\s*tuổi\s*đến\s*chưa\s*đủ\s*\d+\s*tuổi",
    r"có\s*hợp\s*đồng\s*lao\s*động",
]

CONDITION_PREFIXES = [
    "khi",
    "nếu",
    "kể từ ngày",
    "sau khi",
    "trong trường hợp",
    "trường hợp",
    'trừ trường hợp',
    "mà",
    "nhưng",
]

MODALITY_KEYWORDS = [
    "phải",
    "có trách nhiệm",
    "không được",
    "có quyền",
    "được",
]


import re
def normalize_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def extract_base_role(text):

    # sort dài -> ngắn để match chính xác hơn
    for role in sorted(BASE_ROLES, key=len, reverse=True):
        if role in text:
            return role

    return None


def extract_attributes(text, base_role):

    attributes = []

    remaining = text

    if base_role:
        remaining = remaining.replace(base_role, "", 1).strip()

    # match phrase trước
    for attr in sorted(ATTRIBUTES, key=len, reverse=True):

        if attr in remaining:

            normalized_attr = attr

            # normalize
            if attr == "không phải là cá nhân":
                normalized_attr = "không phải cá nhân"

            attributes.append(normalized_attr)

            remaining = remaining.replace(attr, "", 1).strip()

    # regex attributes
    for pattern in ATTRIBUTE_PATTERNS:

        matches = re.findall(pattern, text)

        for m in matches:
            attributes.append(m.strip())

    # remove duplicate giữ nguyên thứ tự
    seen = set()
    unique_attributes = []

    for attr in attributes:

        if attr not in seen:
            seen.add(attr)
            unique_attributes.append(attr)

    return unique_attributes


def extract_role_properties(text):

    text = normalize_text(text)

    base_role = extract_base_role(text)

    attributes = extract_attributes(text, base_role)

    return {
        "base_role": base_role,
        "attributes": attributes
    }



def extract_condition_properties(text):
    """Extract condition properties with remaining content"""
    text = normalize_text(text)
    
    result = {}
    remaining_text = text  # Giữ phần còn lại
    
    # prefix (khi, nếu, trường hợp, ...)
    for prefix in sorted(CONDITION_PREFIXES, key=len, reverse=True):
        if remaining_text.startswith(prefix):
            result["prefix"] = prefix
            remaining_text = remaining_text[len(prefix):].strip(" ,:")
            break
    
    # Lưu phần content còn lại sau khi bỏ prefix
    if remaining_text:
        result["content"] = remaining_text
    
    # Modality (phải, không được, có quyền, ...) - tìm trong remaining_text
    for keyword in sorted(MODALITY_KEYWORDS, key=len, reverse=True):
        if keyword in remaining_text:
            result["modality"] = keyword
            break
    
    # 3. Numeric conditions - tìm trong remaining_text
    numeric = []
    
    # Range: từ X đến Y
    for m in re.finditer(r"từ\s+(\d+)\s*(%|ngày|tháng|năm)?\s+đến\s+(dưới\s+)?(\d+)\s*(%|ngày|tháng|năm)?", remaining_text):
        numeric.append({
            "range": [int(m.group(1)), int(m.group(4))],
            "unit": m.group(2) or m.group(5)
        })
    
    # >= : từ, ít nhất, tối thiểu
    for m in re.finditer(r"(từ|ít nhất|tối thiểu)\s+(\d+)\s*(%|ngày|tháng|năm)?", remaining_text):
        numeric.append({
            "min": int(m.group(2)),
            "unit": m.group(3)
        })
    
    # <= : không quá, tối đa
    for m in re.finditer(r"(không quá|tối đa|không được quá)\s+(\d+)\s*(%|ngày|tháng|năm)?", remaining_text):
        numeric.append({
            "max": int(m.group(2)),
            "unit": m.group(3)
        })
    
    if numeric:
        result["numeric"] = numeric
    
    return result if result else {}



def normalize_time_period(text):
    text = text.strip().lower()
    result = {
        "value": None,
        "unit": None,
        "type": None,
        "constraint": None,
        "direction": None,
        "anchor": None,
        "raw": text
    }

    # Recurring patterns
    recurring_patterns = {
        r"hằng\s*năm": "năm",
        r"hằng\s*tháng": "tháng",
        r"hằng\s*tuần": "tuần",
        r"hằng\s*ngày": "ngày",
        r"mỗi\s*năm": "năm",
        r"mỗi\s*tháng": "tháng",
        r"mỗi\s*tuần": "tuần",
        r"mỗi\s*ngày": "ngày",
    }

    for pattern, unit in recurring_patterns.items():
        if re.search(pattern, text):
            result["type"] = "recurring"
            result["unit"] = unit
            return result

    # Range: từ X đến Y
    m = re.search(r"từ\s+(\d+)\s+(\w+).*?đến\s+(\d+)\s+(\w+)", text)
    if m:
        result["type"] = "range"
        result["value"] = [int(m.group(1)), int(m.group(3))]
        result["unit"] = m.group(2)
        return result

    # Constraints
    if re.search(r"trở lên|ít nhất|tối thiểu", text):
        result["constraint"] = "min"
    if re.search(r"không quá|không được quá|tối đa", text):
        result["constraint"] = "max"

    # Direction
    if "trong thời hạn" in text:
        result["direction"] = "forward"
    if text.startswith("sau"):
        result["direction"] = "after"

    # Extract value + unit
    m = re.search(r"(\d+)\s*(giờ|ngày|tháng|năm|tuần|phút)", text)
    if m:
        result["value"] = int(m.group(1))
        result["unit"] = m.group(2)

    # Anchor
    anchor_match = re.search(r"(kể từ ngày|kể từ khi|kể từ)\s+(.+)", text)
    if anchor_match:
        result["anchor"] = {
            "keyword": anchor_match.group(1),
            "text": anchor_match.group(2).strip()
        }
        result["direction"] = "forward"

    # Default type
    if result["type"] is None:
        result["type"] = "duration"

    return result

def extract_time_properties(text):
    text = normalize_text(text)
    normalized = normalize_time_period(text)
    return {
        "value":      normalized["value"],
        "unit":       normalized["unit"],
        "type":       normalized["type"],
        "constraint": normalized["constraint"],
        "direction":  normalized["direction"],
        "anchor":     normalized["anchor"],
    }



def extract_properties(entity_type, text):

    if entity_type == "LEGAL_ROLE":
        return extract_role_properties(text)

    elif entity_type == "CONDITION":
        return extract_condition_properties(text)

    elif entity_type == "TIME_PERIOD":
        return extract_time_properties(text)

    return {}


from copy import deepcopy

def process_extract_properties(split_ents):
    processed_entities = deepcopy(split_ents)

    for node in processed_entities:

        for ent in node.get("entities", []):

            entity_type = ent.get("type")
            text = ent.get("text", "")

            ent["properties"] = extract_properties(
                entity_type,
                text
            )

    return processed_entities




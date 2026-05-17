import re


def roman_to_int(roman):
    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev = 0
    for ch in reversed(roman):
        value = roman_map.get(ch, 0)
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    return total

def get_article_id(node_id) :
    """
    ch1_d2_k1 -> ch1_d2
    ch1_m1_d2_k1 -> ch1_m1_d2
    """
    m = re.match(r"(.+_d\d+)", node_id)
    return m.group(1) if m else node_id


def get_chapter_id(node_id):
    return node_id.split("_")[0]


def get_article_number_from_node_id(node_id) :
    """
    Lấy số điều từ node_id
    'ch3_muc1_d20_k2' => '20'
    """
    m = re.search(r'_d(\d+)', node_id)
    return m.group(1) if m else None


def get_law_id_from_text(text):
    text = text.lower().strip()
    # tìm 
    dieu = re.search(r"điều\s+(\d+)", text)
    khoan = re.search(r"khoản\s+(\d+)", text)
    diem = re.search(r"điểm\s+([a-z])", text)
    result = []
    if dieu:
        result.append(f"d{dieu.group(1)}")
    if khoan:
        result.append(f"k{khoan.group(1)}")
    if diem:
        result.append(diem.group(1))
    return "_".join(result)


def node_id_to_text(node_id):
    result = []

    # chương
    ch = re.search(r'ch(\d+)', node_id)
    if ch:
        result.append(f"Chương {ch.group(1)}")

    # mục
    muc = re.search(r'm(\d+)', node_id)
    if muc:
        result.append(f"Mục {muc.group(1)}")

    # điều
    dieu = re.search(r'd(\d+)', node_id)
    if dieu:
        result.append(f"Điều {dieu.group(1)}")

    # khoản
    khoan = re.search(r'k(\d+)', node_id)
    if khoan:
        result.append(f"Khoản {khoan.group(1)}")

    # điểm
    diem = re.search(r'_([a-z])$', node_id)
    if diem:
        result.append(f"Điểm {diem.group(1)}")

    return " ".join(result)
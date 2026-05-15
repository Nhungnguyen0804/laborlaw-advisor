import re
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

import re
def split_segments(text):
    # tach theo dau phay or 'và'
    # điểm a, điểm b khoản 2 => ['điểm a', 'điểm b khoản 2']
    
    parts = re.split(r",|\bvà\b", text, flags=re.I)
    return [p.strip() for p in parts if p.strip()]

def parse_segment(segment):
    #điểm a khoản 2
    #{'diem': ['a'], 'khoan': '2', 'dieu': None}
    result = {'diem': [], 'khoan': None, 'dieu': None}
    for m in re.finditer(r"(điểm|khoản|điều)\s+(\S+)", segment, re.I):
        keyword = m.group(1).lower()
        value   = m.group(2)
        if keyword == 'điểm':
            result['diem'].append(value)
        elif keyword == 'khoản':
            result['khoan'] = value
        elif keyword == 'điều':
            result['dieu'] = value

    return result

def fill_missing_suffix(parsed_list):
    # ['điểm a', 'điểm b khoản 2 điều 10']
    # segment 0 thiếu khoản, thiếu điều
    # lấy khoản=2, điều=10 từ segment cuối
    last = parsed_list[-1]
    ref_khoan = last['khoan']
    ref_dieu  = last['dieu']

    filled = []
    for p in parsed_list:
        item = dict(p)  # copy 
        if item['khoan'] is None and ref_khoan:
            item['khoan'] = ref_khoan
        if item['dieu'] is None and ref_dieu:
            item['dieu'] = ref_dieu
        filled.append(item)

    return filled

def format_ref(item):
    # dict => list string 
    # {'diem': ['a', 'b'], 'khoan': '2', 'dieu': '10'}
    # ['điểm a khoản 2 điều 10', 'điểm b khoản 2 điều 10']

    refs = []
    suffix = ""
    if item['khoan']:
        suffix += f" khoản {item['khoan']}"
    if item['dieu']:
        suffix += f" điều {item['dieu']}"

    if item['diem']:
        for d in item['diem']:
            refs.append(f"điểm {d}{suffix}")
    else:
        # Không có điểm, chỉ có khoản/điều
        if item['khoan'] or item['dieu']:
            refs.append(suffix.strip())

    return refs

def split_legal_ref(text):
   
    segments = split_segments(text)
    parsed_list = [parse_segment(s) for s in segments]
    filled_list = fill_missing_suffix(parsed_list)
    
    results = []
    for item in filled_list:
        results.extend(format_ref(item))
    return results


# # Test
# cases = [
#     "điểm a, điểm b khoản 2 điều 134",
#     "điểm a và điểm b khoản 2 điều 134",
#     "khoản 1 và khoản 2 điều 5 của luật này",
#     "điểm a khoản 1, điểm b khoản 2 điều 10",
#     "điều 5 và điều 6 của bộ luật lao động",
#     "điểm đ và điểm e khoản 1 điều 2 của luật này",
#     "điểm a khoản 1 và khoản 2 điều 10",
#     "điểm a khoản 2 điều 134 của bộ luật hình sự",
# ]

# for c in cases:
#     print(f"Input : {c}")
#     print(f"Output: {split_legal_ref(c)}")
#     print()
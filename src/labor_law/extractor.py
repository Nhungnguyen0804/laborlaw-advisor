import re

def extract_blocks(processed_lines, regex, keyword):
    # Chia danh sách lines thành các block dựa theo regex
    # K split khi đang trong quote  

    
    sections = []
    current_block = []
    is_regex = isinstance(regex, re.Pattern)

    # quote_count > 0 = đang trong quote => không split
    # quote_count == 0 = bình thường => có thể split
    quote_count = 0

    
    for line in processed_lines:
        if not isinstance(line, str):
            continue
        # luu count quote trước khi đọc line này 
        if quote_count > 0: 
            in_quote = True
        else:
            in_quote = False

       
        for char in line:
            if char in ('"', '\u201c', '\u00ab'):
                quote_count += 1
            elif char in ('"', '\u201d', '\u00bb'):
                quote_count = max(0, quote_count - 1)


        # Kiểm tra khớp với regex
        if is_regex:
            match = regex.search(line)
            # line bắt đầu là Chương, Khoản, Điều, Mục
            # keyword rỗng thì ko check startswith nữa
            if keyword:
                is_match = bool(match) and line.strip().startswith(keyword)
            else:
                is_match = bool(match) and bool(regex.match(line.strip()))
        else:
            # is_match = line.startswith(keyword)
            is_match = False 
            print('ko match regex!')
        # chỉ split khi khớp regex và ko nằm trong quote 
        need_split = is_match and not in_quote
 
        if need_split:
            # Lưu block cũ lại
            if current_block:
                sections.append(current_block)
            # Bắt đầu block mới
            current_block = [line]
        else:
            # Thêm vào block hiện tại
            if current_block:
                current_block.append(line)
            # chưa có block thì bỏ qua vì k khớp regex
    
    if current_block:
        sections.append(current_block)
    
    return sections


def test():
    a1 = [
        'Mục 1 Luật abc', 
        'Phần 1 luat lao dong',
        'Đieu 1 luat lao dong luat lao dong',
        'Khoan 5 luat lao dong', 
        'Diem a ve thoi han',
        'Mục 3 Bảo hiểm' 
        ]
    section_pattern = re.compile(r"Mục\s+(\d+)")
    a2 = extract_blocks(a1, section_pattern, 'Mục ')
    for item in a2:
        print(item)
    
# test()
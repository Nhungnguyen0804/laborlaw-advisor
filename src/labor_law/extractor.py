import re

def extract_sections(processed_lines, regex, keyword):
    sections = []
    current_section = []
    is_regex = isinstance(regex, re.Pattern)

    
    for line in processed_lines:
        if not isinstance(line, str):
            continue
            
        # Kiểm tra khớp với regex
        if is_regex:
            match = regex.search(line)
            # line bắt đầu là Chương, Khoản, Điều, Mục
            is_match = bool(match) and line.strip().startswith(keyword)
        else:
            match = None
            # is_match = line.startswith(keyword)
            is_match = None
            print('ko match regex!')
        
        if is_match:
            if current_section:
                sections.append(current_section)
            current_section = [line]
        else:
            if current_section:
                current_section.append(line)
    
    if current_section:
        sections.append(current_section)
    
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
    a2 = extract_sections(a1, section_pattern, 'Mục ')
    for item in a2:
        print(item)
    
# test()
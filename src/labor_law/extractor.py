
import re

def extract_sections(processed_lines, keyword):
    """
    chia tách các phần dữ liệu theo từ khóa 
    input là string và keyword 
    """
    # Xử lý input là string
    if isinstance(processed_lines, str):
        processed_lines = [processed_lines]
    
    sections = []
    current_section = []
    is_regex = isinstance(keyword, re.Pattern)
    
    for line in processed_lines:
        if not isinstance(line, str):
            continue
            
        # Kiểm tra khớp với keyword
        is_match = keyword.match(line) if is_regex else line.startswith(keyword)
        
        if is_match:
            if current_section:
                sections.append('\n'.join(current_section))
            current_section = [line]
        else:
            if current_section:
                current_section.append(line)
    
    if current_section:
        sections.append('\n'.join(current_section))
    
    return sections


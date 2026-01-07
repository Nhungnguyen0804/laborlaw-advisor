import re 

#Xử lý xuống dòng, chỉ giữ xuống dòng sau dấu chấm hoặc từ khóa cấu trúc


def format_newlines_after_dot(full_text):
    #Xử lý xuống dòng, chỉ giữ xuống dòng sau dấu chấm hoặc từ khóa cấu trúc
    lines = full_text.split('\n')
    processed_lines = []
    temp_line = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Kiểm tra từ khóa cấu trúc
        starts_with_structure = line.startswith(('Điều ', 'Chương ', 'Mục ')) or re.match(r'^\d+\.\s', line)
        
        if temp_line:
            if temp_line.endswith('.') or starts_with_structure:
                processed_lines.append(temp_line)
                temp_line = line
            else:
                temp_line += ' ' + line
        else:
            temp_line = line

    if temp_line:
        processed_lines.append(temp_line)

    return processed_lines
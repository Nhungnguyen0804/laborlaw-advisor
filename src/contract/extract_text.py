import re
import pdfplumber
import unicodedata
from src.labor_law.extractor import extract_blocks

# hàm tu extract law ============================================

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
        starts_with_structure = (
            line.startswith(('Chương ', 'Mục ')) or
            re.match(r'^\d+\.\s', line) or
            re.match(r'^Điều\s+\d+\.', line)  # phải có dấu chấm sau số như:Điều 54. 
             # lọc đi trường hợp "Điều 169 của..."
        )
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



def read_pdf_pdfplumber(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text = unicodedata.normalize('NFC', text)
                pages.append(text)
    return pages


# ==================================================================
SIGNATURE_PATTERNS = re.compile(
    r"(Ký,\s*ghi rõ họ tên)", 
    re.IGNORECASE
)
def remove_signature_lines(block):
    result = []
    for line in block:
        if SIGNATURE_PATTERNS.search(line):
            break  # bỏ từ line này trở đi
        result.append(line)
    return result

def extract_text_from_contract(input_file):
    pages = read_pdf_pdfplumber(input_file)

    full_text = '\n'.join(pages)
    processed_lines = format_newlines_after_dot(full_text)
    print(f"Tổng {len(processed_lines)} dòng")
    articles = []
    article_pattern = re.compile(r"Điều\s+(\d+)")
    article_blocks  = extract_blocks(processed_lines, article_pattern,'Điều ')
    # print(article_blocks)
    articles = [remove_signature_lines(block) for block in article_blocks]
    # print(articles)
    result = []
    for block in articles:
        if not block:
            continue
        match = re.match(r"(Điều\s+\d+)", block[0])
        if not match:
            continue
        
        dieu_id = match.group(1)  # "Điều 1"
        # Gộp toàn bộ block thành 1 string
        full_content = ' '.join(line.strip() for line in block if line.strip())
        
        # Xoá "Điều 1." hoặc "Điều 1 " khỏi đầu string
        content = re.sub(r"Điều\s+\d+\.\s*", "", full_content, count=1)
        
        result.append({
            'id': dieu_id,
            'content': content
        })
    return result

# extract_text_from_contract(HD_INPUT)
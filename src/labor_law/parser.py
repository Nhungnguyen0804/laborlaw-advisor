
import re
from PyPDF2 import PdfReader
import unicodedata
import pdfplumber
import time
import json
from pathlib import Path
from src.labor_law.extractor import extract_sections

# preprocessing 

def remove_pdf_headers(full_text):
    # tách theo enter
    lines = full_text.split('\n')

    # clean header 
    removed_header = "CÔNG BÁO/Số 993 + 994/Ngày 26-12-2019"
    cleaned_lines = []
    for line in lines:
        if removed_header not in line:
            cleaned_lines.append(line)
    
    # ghép lại enter  
    return '\n'.join(cleaned_lines)

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

# normalize ko dấu + lower
def normalize_to_noformat_text(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower()
    text = text.replace('đ', 'd')
    return text

def get_law_code(law_name):
    normalized = normalize_to_noformat_text(law_name)
    if "bo luat lao dong" in normalized:
        return "labor_law"
    elif "bo luat dan su" in normalized:
        return "civil_law"
    elif "bo luat hinh su" in normalized:
        return "criminal_law"
    return normalized.replace(" ", "_")

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
def read_first_page_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        if pdf.pages:
            return pdf.pages[0].extract_text() or ""
    return ""

def read_pdf_pdfplumber(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text = unicodedata.normalize('NFC', text)
                pages.append(text)
    return pages


def read_multiple_pdfs(pdf_dir):
    #Loop qua folder PDF
    pdf_dir = Path(pdf_dir)
    results = {}
    for pdf_file in pdf_dir.glob("*.pdf"):
        pages = read_pdf_pdfplumber(pdf_file)
        results[pdf_file.name] = '\n'.join(pages)
    return results

# parser
# metadata là thông tin chung của bộ luật 
def parse_general_metadata(pdf_path):
    # đọc trang đầu 
    first_page_text = read_first_page_pdf(pdf_path)
    if not first_page_text:
        return {}

    # tách theo enter 
    raw_lines = [line.strip() for line in first_page_text.split("\n") if line.strip()]
    # xác định header 
    top_lines = raw_lines[:7]



    metadata = {
        "law_code": None,
        "law_name": None,
        "issuing_authority": None
    }

    # authority
    for line in top_lines:
        if "QUỐC HỘI" in line.upper():
            metadata["issuing_authority"] = "QUỐC HỘI"
            break

    # law name
    for i, line in enumerate(raw_lines):
        if line.upper() == "BỘ LUẬT":
            if i + 1 < len(raw_lines):
                law_name = f"BỘ LUẬT {raw_lines[i+1].upper()}"
                metadata["law_name"] = law_name
                metadata["law_code"] = get_law_code(law_name)
                break

    return metadata



def parse_legal_document(processed_lines):
 
    result = {"chapters": []}
    
    
    # Trích xuất chương
    chapter_blocks  = extract_sections(processed_lines, "Chương ")
    
    for chapter_block in chapter_blocks:
        chapter_lines = format_newlines_after_dot(chapter_block)
        
        # Lấy số chương
        pattern = r"Chương\s+([IVXLCDM]+)"
        roman_chapter = re.findall(pattern, chapter_lines[0])
        
        if not roman_chapter:
            continue
        chapter_num = roman_to_int(roman_chapter[0])
        chapter_key = f"chuong_{chapter_num}"
        chapter_obj = {
            "chapter_id": chapter_key,
            "chapter_number": roman_chapter[0], # dạng roman
            # "chapter_title": chapter_info['title']
        }
        
        chapter_key = f"chuong_{chapter_num}"
        
        # # Parse điều từ chương
        # articles = parse_articles(chapter_lines)
        
        # all_chapters[chapter_key] = {
        #     'info': chapter_lines[0],
        #     'articles': articles
        # }

        # thử parse mục trước
        # sections = parse_sections(chapter_lines)
        sections = parse_sections(chapter_lines, chapter_obj['chapter_id'])
        if sections:
            # có mục , điều nằm trong mục
            chapter_obj['sections'] = sections

        else:
            # k có mục => parse điều
            articles = parse_articles(chapter_lines, chapter_obj['chapter_id'])
            chapter_obj['articles'] = articles
        result['chapters'].append(chapter_obj)
    return result


#Mục 
def parse_sections(chapter_lines,chapter_id):
 
    # Thử tìm mục
    section_blocks = extract_sections(chapter_lines, "Mục ")
    
    if not section_blocks:
        return []  # Chương này không có mục thì rỗng
    
    sections = []
    section_pattern = r"Mục\s+(\d+)"
    
    for section_block  in section_blocks:
        section_lines = format_newlines_after_dot(section_block )
        section_num = re.findall(section_pattern, section_lines[0])
        
        if not section_num:
            continue
        
        section_key = f"{section_num[0]}"
        section_obj = {
            "section_id": f"{chapter_id}_muc_{section_key}",
            "section_number": str(section_key),
            # "section_title": 
        }
        # Parse điều từ mục này
        articles = parse_articles(section_lines,section_obj['section_id'])
        section_obj['articles'] = articles
        sections.append(section_obj)
    
    return sections


def parse_articles(chapter_lines,parent_id):

    articles = []
    article_blocks  = extract_sections(chapter_lines, 'Điều ')
    
    for article_block  in article_blocks :
        article_lines = format_newlines_after_dot(article_block )
        
        # Lấy số điều
        article_pattern = r'Điều\s+(\d+)'
        article_num = re.findall(article_pattern, article_lines[0])
        
        if not article_num:
            continue
        
        article_key = f"{article_num[0]}" # dieu 1, dieu 2

        article_obj = {
            "article_id": f"{parent_id}_dieu_{article_key}",
            "article_number": str(article_key),
            # "article_title": article_info['title'],
            "article_content": "\n".join(article_lines)
        }
        
        # Parse khoản từ điều này
        clauses = parse_clauses(article_lines[1:],article_obj['article_id']) #:1 để bỏ dòng Dieu ...
        article_obj['clauses'] = clauses
        articles.append(article_obj)
     
    
    return articles


def parse_clauses(lines,article_id):

    clauses = []
    current_clause = None
    current_clause_lines = []
    for line in lines:
        line = line.strip()
        if not line: continue
        # Kiểm tra xem có phải dòng bắt đầu khoản mới k như 1. Nội dung
        clause_match = re.match(r"^(\d+)\.\s+(.*)", line)
        if clause_match:
            # lưu khoản trc
            if current_clause:
                current_clause['clause_content'] = "\n".join(current_clause_lines)
                current_clause['points'] = parse_points(
                    current_clause['clause_content'],
                    current_clause['clause_id']
                )
                clauses.append(current_clause)
            # Tạo khoản mới
            clause_num = int(clause_match.group(1))
            current_clause = {
                "clause_id": f"{article_id}_khoan_{clause_num}",
                "clause_number": str(clause_num)
            }
            current_clause_lines = [line]
        else:
            # Tiếp tục nội dung khoản hiện tại
            if current_clause :
                current_clause_lines.append(line)
            else:
                # dieu la doan van 
                # ko co số khoản
                current_clause = {
                    "clause_id": f"{article_id}_khoan_1",
                    "clause_number": "1"
                }
                current_clause_lines = [line]
    
    # Lưu khoản cuối cùng
    if current_clause:
        # truyen str 
        current_clause['clause_content'] = "\n".join(current_clause_lines).strip()
        current_clause['points'] = parse_points(
            current_clause['clause_content'], # dùng str k dùng list 
            current_clause['clause_id']
        )
        clauses.append(current_clause)
    
    return clauses





def parse_points(clause_content,clause_id):
    # clause_content chứa a) b) c d cùng 1 dòng 
    if isinstance(clause_content, list):
        text = "\n".join(clause_content)  # list thành str
    elif isinstance(clause_content, str):
        text = clause_content  # giữ str
    else:
        return []
    points = []

    pattern = r'([a-zđ])\)\s*([^a-zđ\)]*(?:[a-zđ](?!\))[^a-zđ\)]*)*)'

    matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)

    for match in matches:
        point_letter = match.group(1).lower()
        point_content = match.group(2).strip()
        
        # Loại bỏ dấu ; cuối 
        point_content = point_content.rstrip(';').strip()
        
        if point_content:  
            points.append({
                "point_id": f"{clause_id}_diem_{point_letter}",
                "point_letter": point_letter,
                "point_content": point_content
            })
    
    return points


def test():
    INPUT_FILE_PATH = 'src/data/raw/laborlaw.pdf'
    pdf_path = INPUT_FILE_PATH
    a = parse_general_metadata(pdf_path)
    print(a)
    print(type(a))
    print('done')
    print(get_law_code('BỘ LUẬT LAO ĐỘNG'))

test()
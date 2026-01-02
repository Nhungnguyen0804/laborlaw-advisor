from PyPDF2 import PdfReader
import unicodedata
import pdfplumber
import re
import json


def read_pdf_pdfplumber(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text = unicodedata.normalize('NFC', text)
                pages.append(text)
    return pages


def clean_header(full_text):
    lines = full_text.split('\n')
    filtered_lines = [line for line in lines if "CÔNG BÁO/Số 993 + 994/Ngày 26-12-2019" not in line]
    return '\n'.join(filtered_lines)


def format_newlines_after_dot(full_text):
    """Xử lý xuống dòng, chỉ giữ xuống dòng sau dấu chấm hoặc từ khóa cấu trúc"""
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


def extract_sections(processed_lines, keyword):
    """
    Trích xuất các phần theo từ khóa (string và regex)
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

import re

def parse_points(clause_text):
    points = {}
    unmatched_lines = []
    
    # Pattern để tìm các điểm: a), b), c) hoặc 1), 2), 3)...
    point_pattern = r'([\w]|\d+)\)\s+'
    
    # Tách văn bản thành các phần dựa trên pattern
    parts = re.split(f'({point_pattern})', clause_text, flags=re.UNICODE | re.IGNORECASE)
    
    # parts[0]: phần text trước điểm đầu tiên 
    if parts[0].strip():
        unmatched_lines.append(parts[0].strip())
    
    # Xử lý các phần còn lại (cặp: match_group, point_id, whitespace, content)
    i = 1
    while i < len(parts):
        if i + 2 < len(parts):
            # parts[i]: toàn bộ match ("a) ")
            # parts[i+1]: point_id ("a")
            # parts[i+2]: content sau point
            point_id = parts[i+1]
            point_content = parts[i+2].strip()
            
            if point_content:
                point_key = f"diem_{point_id}"
                cleaned_point_content = re.sub(r'^([a-zA-Z]|\d+)\)\s*', '', point_content).strip()
                # Lưu cả ký hiệu và nội dung
                points[point_key] = f"{point_id}) {point_content}"
                # points[point_key] = f"{cleaned_point_content}"
            
            i += 3
        else:
            i += 1
    
    # Ghép unmatched text với xuống dòng
    full_unmatched_text = '\n'.join(unmatched_lines)
    
    return full_unmatched_text, points


def parse_clauses(article_lines):
    """
    Parse khoản từ điều (1., 2., 3., ...)
    dict {khoan_1: {"info": "...", "points": {...}}}
    """
    clauses = {}
    
    # Pattern cho khoản: 1., 2., 3., ...
    clause_pattern = re.compile(r'^\d+\.\s')
    clause_sections = extract_sections(article_lines, clause_pattern)
    
    if not clause_sections:
        return {}
    
    for clause in clause_sections:
        # Lấy số khoản
        match = re.match(r'^(\d+)\.\s', clause)
        if match:
            clause_num = match.group(1)
            clause_key = f"khoan_{clause_num}"
    
            # Parse điểm từ khoản này
            unmatched_text,points = parse_points(clause)
            info_cleaned = re.sub(r'^\d+\.\s*', '', unmatched_text).strip()
            clauses[clause_key] = {
                "info": unmatched_text,
                "points": points
            }
    
    return clauses


def parse_articles(chapter_lines):
    """
    Parse điều từ chương
    dict {dieu_1: {"info": "...", "clauses": {...}}}
    """
    articles = {}
    article_sections = extract_sections(chapter_lines, 'Điều ')
    
    for article in article_sections:
        article_lines = format_newlines_after_dot(article)
        
        # Lấy số điều
        article_pattern = r'Điều\s+(\d+)'
        article_num = re.findall(article_pattern, article_lines[0])
        
        if not article_num:
            continue
        
        article_key = f"dieu_{article_num[0]}"
        
        # Parse khoản từ điều này
        clauses = parse_clauses(article_lines)
        
        #xóa điều
        info =  article_lines[0]
        info_cleaned = re.sub(r'Điều\s+\d+\.?\s*', '',info).strip()
        articles[article_key] = {
            "info": info, 
            "clauses": clauses
        }
    
    return articles


def parse_legal_document(processed_lines):
    """
    Parse toàn bộ văn bản pháp luật theo cấu trúc Chương > Điều > Khoản > Điểm
    Dict với cấu trúc đầy đủ
    """
    all_chapters = {}
    
    # Trích xuất chương
    chapters = extract_sections(processed_lines, "Chương ")
    
    for chapter in chapters:
        chapter_lines = format_newlines_after_dot(chapter)
        
        # Lấy số chương
        pattern = r"Chương\s+([IVXLCDM]+)"
        roman_chapter = re.findall(pattern, chapter_lines[0])
        
        if not roman_chapter:
            continue
        
        chapter_num = roman_to_int(roman_chapter[0])
        chapter_key = f"chuong_{chapter_num}"
        
        # Parse điều từ chương
        articles = parse_articles(chapter_lines)
        
        all_chapters[chapter_key] = {
            'info': chapter_lines[0],
            'articles': articles
        }
    
    return all_chapters



if __name__ == "__main__":
    pdf_path = 'test/test1.pdf'
    
    try:
        # Đọc PDF
        pages = read_pdf_pdfplumber(pdf_path)
        print(f"Đọc được {len(pages)} trang")
        
        # Xử lý text
        full_text = '\n'.join(pages)
        full_text = clean_header(full_text)
        processed_lines = format_newlines_after_dot(full_text)
        print(f"Xử lý xong {len(processed_lines)} dòng")
        
        # Parse cấu trúc
        result = parse_legal_document(processed_lines)
       
        
        # Lưu ra file JSON
        output_file = 'output_structure.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nĐã lưu kết quả vào: {output_file}")
        
    except FileNotFoundError:
        print("Không tìm thấy file PDF!")
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
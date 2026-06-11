from src.utils.file_utils import save_txt
from pathlib import Path
from docx import Document
import re

def extract_docx_text(docx_path):
    doc = Document(docx_path)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return lines

def test_content_doc(docx_files,i):
    doc_file_path = docx_files[i]
    print(f"File thứ {i}: {doc_file_path}")
    lines = extract_docx_text(doc_file_path)
    save_txt(lines,f"src/labor_law/vbhd/text_doc_{i}.txt")
    return doc_file_path

# ****************************************************************
def filter_blld_year_outdate(docx_files):
    filtered_files = []
    for docx_path in docx_files:
        lines = extract_docx_text(docx_path)
        header = "\n".join(lines[:100]).lower()
        can_delete = False 
        patterns = [
            r'bộ luật lao động[^.]{0,80}năm\s+(\d{4})',
            r'căn cứ bộ luật lao động[^.]{0,80}năm\s+(\d{4})'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, header)
            for year_str in matches:
                year = int(year_str)
                if year < 2019:  # BLLĐ 2019 có hiệu lực từ 1/1/2021
                    can_delete = True
                    print(f"Loại: {docx_path} (BLLĐ năm {year})")
                    break
            if can_delete:
                break
        if not can_delete:
            filtered_files.append(docx_path)
      
    return filtered_files




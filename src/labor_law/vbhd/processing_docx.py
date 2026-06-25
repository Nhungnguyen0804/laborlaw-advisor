from src.utils.file_utils import save_txt
from pathlib import Path
from docx import Document
import re
import json
from src.labor_law.extractor import extract_blocks
from src.labor_law.parser import (
    format_newlines_after_dot,
    normalize_to_noformat_text,
    roman_to_int,
    parse_clauses,
    parse_points,
)
from src.labor_law.vbhd.vbhd_function import (
    filter_blld_year_outdate,
    test_content_doc,
    extract_docx_text,
    build_json,
    debug_null_files,

)



print('PROCESSING DOCX ==========================================')
doc_file_dir = Path("data/raw/collected_vbhd")
# tìm file docx
# rglob() sẽ tự động đi vào all
docx_files = sorted(doc_file_dir.rglob("*.docx"))
print('Số docx đang có: ',    len(docx_files))

filted_blld_files = filter_blld_year_outdate(docx_files)
print('Số docx còn lại sau khi lọc lần 1: ',    len(filted_blld_files))

build_json(filted_blld_files, 'src/labor_law/vbhd/lan1.json')
# test_content_doc(docx_files,0)
# test_content_doc(docx_files,10)

test_content_doc(docx_files, 50)

null_files = debug_null_files(docx_files)


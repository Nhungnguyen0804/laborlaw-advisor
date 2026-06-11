from collections import Counter
from pathlib import Path
from docx import Document

def extract_docx_text(docx_path):
    doc = Document(docx_path)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return lines


doc_files = sorted(Path("data/raw/collected_vbhd").rglob("*.docx"))

first_lines = []

for path in doc_files:
    try:
        lines = extract_docx_text(path)
        if not lines:
            print("EMPTY:", path)
            continue
        first_line = lines[0]
        if "Rar!" in first_line:
            continue
        first_lines.append(lines[0])

        
    except Exception:
        continue
counter = Counter(first_lines)
for line, count in counter.most_common():
    print(count, "|", line)
from src.utils.file_utils import save_txt

from pathlib import Path
from docx import Document


def save_txt(lines, output_path, mode="w"):
    output_path = Path(output_path)

    # tạo folder nếu chưa có
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode, encoding="utf-8") as f:
        if isinstance(lines, list):
            f.write("\n".join(lines))
        else:
            f.write(lines)

    print(f"Lưu tại {output_path}")


def extract_docx_text(docx_path):
    doc = Document(docx_path)

    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)

    return lines

def test_content_doc(i):
    doc_file_dir = Path("data/raw/collected_vbhd")
    doc_files = list(doc_file_dir.rglob("*.doc"))
    doc_file_path = doc_files[i]
    print(f"File thứ {i}: {doc_file_path}")
    lines = extract_docx_text(doc_file_path)
    save_txt(
        lines,
        f"src/labor_law/vbhd/text_doc_{i}.txt"
    )
    return doc_file_path


test_content_doc(0)
test_content_doc(10)
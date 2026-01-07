from PyPDF2 import PdfReader
import unicodedata
import pdfplumber
from pathlib import Path

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

from win32com.client import Dispatch
from pathlib import Path


def convert_all_doc_to_docx(folder, doc_to_docx_path):
    folder = Path(folder)
    doc_to_docx_path = Path(doc_to_docx_path)
    doc_to_docx_path.mkdir(exist_ok=True)
    doc_files = folder.rglob("*.doc")

    word = Dispatch("Word.Application")
    word.Visible = False

    for doc_path in doc_files:
        try:
            doc = word.Documents.Open(str(doc_path.resolve()))
            docx_path = doc_to_docx_path / f"{doc_path.stem}.docx"
            doc.SaveAs(str(docx_path.resolve()), FileFormat=16)
            doc.Close(False)

            print(f"OK: {doc_path.name}")

        except Exception as e:
            print(f"ERROR: {doc_path.name} - {e}")

    word.Quit()

input_path = "data/raw/collected_vbhd"
output_path = "data/raw/collected_vbhd/doc_to_docx"
convert_all_doc_to_docx(input_path,output_path)
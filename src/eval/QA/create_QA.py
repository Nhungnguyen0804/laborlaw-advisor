from src.utils.file_utils import save_json
def create_QA(txt_files, output_path):
    qa_data = []
    current_id = 1

    for question_type, file_path in txt_files.items():
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            question = line.strip()
            # Bỏ dòng rỗng
            if not question:
                continue
            qa_item = {
                "id": current_id,
                "question": question,
                "answer": "",
                "question_type": question_type
            }

            qa_data.append(qa_item)
            current_id += 1
    print(f'Có {len(qa_data)} câu hỏi')
    save_json(qa_data,output_path)

txt_files = {
    "structural": "data/question/structural.txt",
    "content": "data/question/content.txt",
    "rel": "data/question/rel.txt",
    "composite": "data/question/composite.txt",
    "real": "data/question/real.txt"
}

create_QA(txt_files,'src/eval/QA/qa.json')

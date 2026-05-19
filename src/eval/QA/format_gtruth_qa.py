import json
from src.utils.file_utils import save_json,load_json
def convert_to_groundtruth(input_data):
    return [
        {
            **item,
            "answer": item["gemini_answer"]
        }
        for item in input_data
    ]


# Đọc file nguồn
data = load_json('src/eval/QA/gemini_qa_v4.json')

# Chuyển đổi dữ liệu
output = convert_to_groundtruth(data)

# Ghi file mới
gtruth_qa_path = 'src/eval/QA/gtruth_qa.json'
save_json(output,gtruth_qa_path)


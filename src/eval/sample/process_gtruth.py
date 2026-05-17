from src.utils.file_utils import load_json,save_json
import re
def load_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    return content

def process_gtruth(file_path,text_to_node_id):
    results = []
    content = load_txt(file_path)
    # Tách từng block
    blocks = content.split("==================================================")
    for block in blocks:
        block = block.strip()
        if block == "":
            continue
        lines = block.split("\n")

        # Câu đầu tiên là text gốc
        original_text = lines[0].strip()

        current_entities = []
        is_entity_section = False
        for line in lines:
            line = line.strip()
            # Bắt đầu phần entity
            if line == "Các thực thể:":
                is_entity_section = True
                continue

            # Gặp phần cạnh thì dừng
            if line == "Các cạnh:":
                break

            # Đọc entity
            if is_entity_section and line.startswith("("):
                line = line.replace("(", "").replace(")", "")
                parts = line.split('|')
                ent_text = parts[0].strip()
                ent_type = parts[1].strip()

                current_entities.append({
                    "text": ent_text,
                    "type": ent_type
                    })

        node_id = text_to_node_id.get(original_text, "")
        results.append({
            "node_id": node_id,
            "text": original_text,
            "entities": current_entities
        })

    return results

GTRUTH_PATH = "src/eval/sample/gtruth.txt"
GTRUTH_JSON = "src/eval/sample/gtruth.json"
nodes = load_json('src/eval/sample/sample_with_nodeid.json')

text_to_node_id = {}

for node in nodes:
    text = node["text"]
    node_id = node["node_id"]

    text_to_node_id[text] = node_id

processed_gtruth = process_gtruth(GTRUTH_PATH,text_to_node_id)
save_json(processed_gtruth,GTRUTH_JSON)

NODE_IDS = []

for node in processed_gtruth:
    NODE_IDS.append(node["node_id"])

print(f'Số lượng node id sample: {len(NODE_IDS)}')
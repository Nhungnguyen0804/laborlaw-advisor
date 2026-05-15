from src.utils.paths import STRUCTURAL_NODES_JSON
from src.utils.file_utils import load_json
import json


def recover_samples(sample_txt_path, output_json_path):
    # đọc sample txt
    with open(sample_txt_path, "r", encoding="utf-8") as f:
        sample_texts = [line.strip() for line in f if line.strip()]

    # load structural nodes
    s_nodes_data = load_json(STRUCTURAL_NODES_JSON)

    recovered = []
    not_found = []

    nodes = s_nodes_data["nodes"]

    for text in sample_texts:
        matched = False

        for node in nodes:
            node_type = node.get("type")
            props = node.get("properties", {})

            content = None

            if node_type == "CLAUSE":
                content = props.get("clause_content")

            elif node_type == "POINT":
                content = props.get("point_content")

            if not content:
                continue

            if content.strip() == text:
                recovered.append({
                    "node_id": node.get("id"),
                    "node_type": node_type,
                    "text": text
                })

                matched = True
                break

        if not matched:
            not_found.append(text)

    # save recovered
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(recovered, f, ensure_ascii=False, indent=2)

    print(f"Recovered: {len(recovered)}")
    print(f"Not found: {len(not_found)}")

    if not_found:
        print("\nCác text không tìm thấy:")
        for t in not_found[:10]:
            print("-", t[:100])


recover_samples(
    "src/eval/sample/sample.txt",
    "src/eval/sample/sample_with_nodeid.json"
)
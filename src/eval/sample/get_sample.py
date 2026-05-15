import json
import random
from src.utils.paths import PROPERTY_ENTITES_JSON,STRUCTURAL_NODES_JSON
from src.utils.file_utils import load_json,save_txt

def get_random_node_ids(p_ents_data, sample_size=100):
  
    #Lấy random node_id từ file entity
    #chỉ lấy node_type = clause hoặc point
    
    valid_node_ids = []

    for item in p_ents_data:
        if item.get("node_type") in ["clause", "point"]:
            valid_node_ids.append(item["node_id"])

    # tránh sample lớn hơn số lượng thực tế
    sample_size = min(sample_size, len(valid_node_ids))

    return random.sample(valid_node_ids, sample_size)


def extract_texts_by_node_ids(s_nodes_data,selected_node_ids,output_txt_path):

    #Từ file structure:
    #- tìm node theo id
    #- lấy clause_content hoặc point_content
    #- lưu mỗi text 1 dòng

    nodes = s_nodes_data["nodes"]
    id_set = set(selected_node_ids)
    extracted_texts = []
    for node in nodes:
        node_id = node.get("id")
        if node_id not in id_set:
            continue
        node_type = node.get("type")
        props = node.get("properties", {})
        text = None
        if node_type == "CLAUSE":
            text = props.get("clause_content")
        elif node_type == "POINT":
            text = props.get("point_content")
        if text:
            extracted_texts.append(text.strip())

    save_txt(extracted_texts,output_txt_path)
    print(f"Đã lưu {len(extracted_texts)} dòng")

def get_100_sample():
    p_ents_data = load_json(PROPERTY_ENTITES_JSON)
    s_nodes_data = load_json(STRUCTURAL_NODES_JSON)
    output_txt_path = 'src/eval/sample/sample.txt'
    # bước 1: random node ids
    random_node_ids = get_random_node_ids(p_ents_data,sample_size=100)

    # # bước 2: extract text
    extract_texts_by_node_ids(s_nodes_data,random_node_ids,output_txt_path)

get_100_sample()
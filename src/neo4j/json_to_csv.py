import json
import pandas as pd
import os

INPUT_JSON = "src/ner/ner_re.json"
OUTPUT_DIR = "src/neo4j/data_dir"


# gán id (text,type): "n_00001"
node_map = {}
count_node = 0

def get_node_id(text, entity_type):
    global count_node
    key = (text.strip(), entity_type)
    if key not in node_map:
        count_node += 1
        node_map[key] = f"n_{count_node:05d}"
    return node_map[key]

edge_map = {}
count_edge = 0

def get_edge_id(subject_id, pred, object_id):
    global count_edge
    key = (subject_id, pred, object_id)
    if key not in edge_map:
        count_edge += 1
        edge_map[key] = f"e_{count_edge:05d}"
    return edge_map[key]


def create_node(text, entity_type, chunk_id, sentence_id):
    node_id = get_node_id(text, entity_type)

    return {
        "node_id": node_id,
        "text": text.strip(),
        "entity_type": entity_type,
        "first_chunk": chunk_id,
        "first_sentence": sentence_id,
        "node_frequency": 1,
    }


def get_node(text, entity_type, chunk_id, sentence_id, nodes):
    node_id = get_node_id(text, entity_type)

    # chưa có node thì tạo mới
    if node_id not in nodes:
        nodes[node_id] = create_node(
            text=text,
            entity_type=entity_type,
            chunk_id=chunk_id,
            sentence_id=sentence_id,
        )
    else:
        nodes[node_id]["node_frequency"] += 1

    return node_id

def process_relation(rel, chunk_id, sentence_id, nodes, edges):
    subject_id = get_node(
        rel.get("subject", ""),
        rel.get("subject_type", "UNKNOWN"),
        chunk_id,
        sentence_id,
        nodes,
    )
    
    object_id = get_node(
        rel.get("object", ""),
        rel.get("object_type", "UNKNOWN"),
        chunk_id,
        sentence_id,
        nodes,
    )
    
    relation_type = rel.get("relation_type", "")
    edge_id = get_edge_id(subject_id, relation_type, object_id)
    
    # check tồn tại của edge
    edge_exists = False

    for e in edges:
        if e["edge_id"] == edge_id:
            edge_exists = True
            break
    
    if not edge_exists:
        edges.append({
            "edge_id": edge_id,
            "source_id": subject_id,
            "target_id": object_id,
            "relation_type": relation_type,
            "confidence": rel.get("confidence", 0.5), # ko có thì mặc định 0.5
            "chunk_id": chunk_id,
            "sentence_id": sentence_id,
        })


def export_csv(nodes, edges):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    nodes_df = pd.DataFrame(list(nodes.values()))
    edges_df = pd.DataFrame(edges)
    
    nodes_df.to_csv(os.path.join(OUTPUT_DIR, "nodes.csv"), index=False)
    edges_df.to_csv(os.path.join(OUTPUT_DIR, "edges.csv"), index=False)
    
    print(f"Đã tạo {len(nodes)} nodes")
    print(f"Đã tạo {len(edges)} edges")
    print(f"Lưu tại: {OUTPUT_DIR}")

def convert_json_to_csv():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    chunks = data.get("results", data) if "results" in data else data
    
    nodes = {}
    edges = []
    
    for chunk_idx, chunk in enumerate(chunks):
        chunk_id = chunk.get("chunk_id", f"chunk_{chunk_idx:05d}")
        
        for sentence in chunk.get("sentences", []):
            sentence_id = sentence.get("sentence_id", "s0")
            
            for rel in sentence.get("relations", []):
                process_relation(
                    rel,
                    chunk_id,
                    sentence_id,
                    nodes,
                    edges,
                )
    
    export_csv(nodes, edges)



def main():
    convert_json_to_csv()

main()
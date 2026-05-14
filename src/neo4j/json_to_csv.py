import json
import os
import pandas as pd
from src.utils.file_utils import load_json

STRUCTURAL_NODES_PATH = "data/graph/structural_nodes.json"
STRUCTURAL_EDGES_PATH = "data/graph/structural_edges.json"
SEMANTIC_NODES_PATH   = "data/graph/all_semantic_nodes.json"
SEMANTIC_EDGES_PATH   = "data/graph/all_semantic_edges.json"


OUTPUT_DIR = "data/graph/import_neo4j"

def get_structural_label(node):
    properties = node.get("properties", {})
    sentences = node.get("sentences", [])

    priority_fields = ["point_content","clause_content", "article_title","section_title","chapter_title"]

    for field in priority_fields:
        value = properties.get(field)
        if value:
            return value
    # k co title /content 
    if sentences:
        s = sentences[0]
        return s
    return node.get("type", "")
  
def process_structural_nodes(data):

    nodes = data["nodes"]

    rows = []

    for node in nodes:

        properties = node.get("properties", {})
        sentences = node.get("sentences", [])

        row = {
            "node_id": node.get("id"),
            "node_type": node.get("type"),
            "graph_type": "structural",
            "sentences": json.dumps(sentences,ensure_ascii=False), # lưu dạng json string 
        }
        row["label"] = get_structural_label(node)

        for key, value in properties.items():
            if isinstance(value, list): # value la list => luu dạng json string 
                row[key] = json.dumps(value, ensure_ascii=False)
            else:
                row[key] = value
        rows.append(row)
    dataframe = pd.DataFrame(rows)
    return dataframe

def process_structural_edges(data):
    edges = data["edges"]
    rows = []
    for edge in edges:
        row = {
            "edge_id": edge.get("id"),
            "source_id": edge.get("source"),
            "target_id": edge.get("target"),
            "relation_type": edge.get("type"),
            "graph_type": "structural",
        }
        rows.append(row)
    dataframe = pd.DataFrame(rows)
    return dataframe

def process_semantic_nodes(data):
    rows = []
    for node in data:
        properties = node.get("properties", {})
        span = node.get("span", [])
        text = node.get("text", "")
        row = {
            "node_id": node.get("id"),
            "node_type": node.get("type"),
            "text": node.get("text"),
            "label": text if text else node.get("type", ""), 
            "source": node.get("source"),
            "graph_type": "semantic",
            "span_start": None,
            "span_end": None,
        }
        # span start
        if len(span) > 0:
            row["span_start"] = span[0]
        # span end
        if len(span) > 1:
            row["span_end"] = span[1]

        
        for key, value in properties.items():
            # list -> json string
            if isinstance(value, list):
                row[key] = json.dumps(value,ensure_ascii=False)
            else:
                row[key] = value
        rows.append(row)
    dataframe = pd.DataFrame(rows)
    return dataframe

def process_semantic_edges(data):
    rows = []
    for edge in data:
        row = {
            "edge_id": edge.get("id"),
            "source_id": edge.get("source"),
            "target_id": edge.get("target"),
            "relation_type": edge.get("type"),
            "graph_type": "semantic",
        }
        rows.append(row)
    dataframe = pd.DataFrame(rows)
    return dataframe

def export_csv(dataframe, filename):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR,filename)
    dataframe.to_csv(output_path,index=False,encoding="utf-8-sig")
    print(f"Saved: {output_path}")

def convert_json_to_csv():
    structural_nodes_json = load_json(STRUCTURAL_NODES_PATH)
    structural_edges_json = load_json(STRUCTURAL_EDGES_PATH)
    semantic_nodes_json = load_json(SEMANTIC_NODES_PATH)
    semantic_edges_json = load_json(SEMANTIC_EDGES_PATH)

    structural_nodes_df = process_structural_nodes(structural_nodes_json)
    structural_edges_df = process_structural_edges(structural_edges_json)
    semantic_nodes_df = process_semantic_nodes(semantic_nodes_json)
    semantic_edges_df = process_semantic_edges(semantic_edges_json)

    export_csv(structural_nodes_df,'structural_nodes.csv')
    export_csv(structural_edges_df,'structural_edges.csv')
    export_csv(semantic_nodes_df,'semantic_nodes.csv')
    export_csv(semantic_edges_df,'semantic_edges.csv')

    #merge
    nodes_df = pd.concat([structural_nodes_df,semantic_nodes_df],ignore_index=True) # bỏ idx cu tao lai index moi 
    edges_df = pd.concat([structural_edges_df,semantic_edges_df],ignore_index=True)
    export_csv(nodes_df,'nodes.csv')
    export_csv(edges_df,'edges.csv')


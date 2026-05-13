from src.utils.file_utils import save_json
from src.ner_re.load_input import load_input
from src.ner_re.extract_structural_nodes import extract_structural_nodes
from src.ner_re.build_structural_edges import build_structural_edges
from src.ner_re.patterns import PATTERNS
from src.ner_re.extract_entity import process_article
from src.ner_re.split_enum_entity import split_enum_entities
from src.ner_re.ent_text_normalization import normalize_entities
from src.ner_re.rel_extraction import run_re
import re


def split_structural_text_into_sentences(text):
    # split dieu khoan diem thanh cau 
    # Replace delimiters
    text = text.replace('\n', '<SPLIT>')
    text = text.replace(';', '<SPLIT>')
    text = text.replace('.', '<SPLIT>')

    # Split và clean
    sentences = [s.strip() for s in text.split('<SPLIT>') if s.strip()]
    
    return sentences


def add_sentences_to_nodes(structural_nodes):
    """
    Thêm field 'sentences' cho mỗi node
    """

    nodes = structural_nodes.get("nodes", [])

    for node in nodes:

        props = node.get("properties", {})

        # lấy text từ nhiều field có thể có
        text = (
            props.get("clause_content", "")
            or props.get("article_title", "")
            or props.get("chapter_title", "")
            or props.get("law_name", "")
        )

        if text.strip():
            node["sentences"] = split_structural_text_into_sentences(text)
        else:
            node["sentences"] = []

    return structural_nodes


COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]

law_data,structure,chapters = load_input()

structural_nodes = extract_structural_nodes(law_data)
structural_nodes = add_sentences_to_nodes(structural_nodes)
structural_edges = build_structural_edges(structural_nodes)
# print(type(structural_nodes)) # dict
# print(structural_nodes)
save_json(structural_nodes, 'src/ner_re/structural_nodes.json')
save_json(structural_edges, 'src/ner_re/structural_edges.json')

raw_entities = []
for chapter in law_data['structure']['chapters']:
    for article in chapter.get("articles", []):
        article_results  = process_article(article,COMPILED)
        raw_entities.extend(article_results)

    for section in chapter.get("sections", []):

        for article in section.get("articles", []):
            article_results  = process_article(article,COMPILED)
            raw_entities.extend(article_results)
        
save_json(raw_entities,'src/ner_re/raw_entities.json')


normalized_entities = normalize_entities(raw_entities)
save_json(normalized_entities,'src/ner_re/normalized_entities.json')

splited_entities = split_enum_entities(normalized_entities)
save_json(splited_entities,'src/ner_re/splited_entities.json')

from src.ner_re.extract_properties import process_extract_properties
property_entities = process_extract_properties(splited_entities)
save_json(property_entities,'src/ner_re/property_entities.json')

from src.ner_re.test.extract_ent_text import test_ent_text
from src.ner_re.test.extract_split import test_split
test_ent_text()
test_split()

counter = 1

def make_entity_id():
    global counter
    entity_id = f"ent_{counter}"
    counter += 1
    return entity_id

def add_entity_ids(property_entities):
    for item in property_entities:
        for ent in item["entities"]:
            ent["id"] = make_entity_id()

    return property_entities

property_entities = add_entity_ids(property_entities)
save_json(property_entities,'src/ner_re/property_entities.json')


all_semantic_edges = run_re(property_entities,structural_nodes)
save_json(all_semantic_edges,'src/ner_re/all_semantic_edges.json')

def extract_entities(data):
    all_entities = []
    for doc in data:
        for ent in doc.get('entities', []):
            all_entities.append(ent)
    return all_entities 

all_semantic_nodes = extract_entities(property_entities)
print(f'TẤT CẢ SEMANTIC NODES LÀ {len(all_semantic_nodes)} NODE')
save_json(all_semantic_nodes,'src/ner_re/all_semantic_nodes.json')
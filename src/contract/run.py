import re
from src.contract.extract_text import extract_text_from_contract
from src.ner_re.patterns import PATTERNS
from src.neo4j.connection import init_driver, close_driver
from src.models.qwen import load_qwen,generate_answer
from src.neo4j.test_connect import test_connection
from src.ner_re.extract_entity import extract_entities_from_question
from src.retrieval.run import run_retrieval
from src.utils.file_utils import save_json
from src.neo4j.query_neo4j import query_node_direct
HD_INPUT = 'src/contract/hd1.pdf'

import json

def extract_ids_in_graph(data):
    result_ids = []
    for item in data:
        graph = item.get("graph", {})
        best_id = (graph.get("point_id") or graph.get("clause_id") or graph.get("article_id"))
        if best_id:
            result_ids.append(best_id)
    return result_ids

def get_content_from_law_id(driver,ids):
    content_list =[]
    for id in ids:
        content = query_node_direct(driver,id)
        content_list.extend(content)
    return content_list
# ================================================== 

def format_relations(relations):
    """
    Convert triples thành câu tự nhiên
    Input: [["subject", "predicate", "object"], ...]
    Output: "- subject [predicate] object\n- ..."
    """
    if not relations:
        return ""
    
    formatted = []
    for triple in relations:
        if len(triple) == 3:
            subject, predicate, obj = triple
            # Chuyển thành câu dễ đọc
            formatted.append(f"- {subject} --> {predicate} --> {obj}")
    
    return "\n".join(formatted)


def format_context_for_llm(chunks, is_rag = False):
    chunks = chunks[:3]  # top 3cai thien toc do
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        # Lấy nội dung chính
        
        # Lấy metadata
        if is_rag:
            content = chunk.get("content", "")
            context_parts.append(content)
        else:
            content = chunk.get("content_with_context", "")
            article_title = chunk["graph"].get("article_title", "")
            entities = [e.get("label", "") for e in chunk["graph"].get("entities", [])]
            relations = chunk["graph"].get("rels", [])
        
            # Format thành text
            part = f"""
            [Đoạn {i}] {article_title}
            Nội dung: {content}
            Entities liên quan: {', '.join(entities)}
            """
            if relations:
                part += f"Quan hệ:\n{format_relations(relations)}\n"
            
            context_parts.append(part)
    
    return "\n---\n".join(context_parts)

def format_graph_result(nodes):
    if not nodes:
        return "Không tìm thấy thông tin."

    lines = []  
    for node in nodes:
        title = node["text"]
        content = node["content"] if node["content"] else node["text"]
        lines.append(f"{title}: {content}")
    return "\n\n".join(lines)

COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]

driver = init_driver()
test_connection()
# ===================================================
# dieu khoan contract 
contract_provisions = extract_text_from_contract(HD_INPUT)
try:
    for prov in contract_provisions:
        content = prov.get('content')
        print('len content --> ',len(content))
        ents = extract_entities_from_question(content,COMPILED)
        context = run_retrieval(driver,content,ents) #chunk_with_ents_rels
        # print('type context --> ',type(context))
        prov['context'] = format_context_for_llm(context)
        law_ids = extract_ids_in_graph(context[:3])
        print(law_ids)
        prov['law_ids'] = law_ids
        # ----------------------------
        law_list = get_content_from_law_id(driver,law_ids)
        prov['law_list'] = law_list
    
    save_json(contract_provisions, 'src/contract/contract.json')
    
    for prov in contract_provisions:
        law_list = prov['law_list']
        res = 'Danh sách luật liên quan:'
        res += '\n'
        for law in law_list:
            law_title = law['text']
            law_content = law['content']
            law_res = f'{law_title}: {law_content}'
            res += law_res
            res += '\n'
        prov['related_law'] = res
        res = ''
    save_json(contract_provisions, 'src/contract/contract_v1.json')


    for prov in contract_provisions:
        prov_id = prov['id']
        prov_content = prov['content']
        contract_text = f'{prov_id}: {prov_content}'
        print("CONTRACT: ",contract_text)

        print(prov['related_law'])
except Exception as e:
    print("LOI:", e)

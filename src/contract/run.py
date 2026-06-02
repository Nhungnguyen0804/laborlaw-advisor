import re
from src.contract.extract_text import extract_text_from_contract
from src.ner_re.patterns import PATTERNS
from src.neo4j.connection import init_driver, close_driver
from src.models.qwen import load_qwen,generate_answer
from src.models.gem import make_client
from src.contract.analyze import analyze_contract
from src.neo4j.test_connect import test_connection
from src.ner_re.extract_entity import extract_entities_from_question
from src.retrieval.run import run_retrieval
from src.utils.file_utils import save_json
from src.neo4j.query_neo4j import query_node_direct
import os
from dotenv import load_dotenv
import json

# HD_INPUT = 'src/contract/hd1.pdf'


COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]

driver = init_driver()
test_connection()
# ===================================================

index = 1
API_KEYS = []
load_dotenv()

while True:
    key = os.getenv(f"G_KEY_{index}")
    if key is None:
        break
    API_KEYS.append(key)
    index += 1

print("Đã load", len(API_KEYS), "key")


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



import time

# --------------------------------------------------------
# dieu khoan contract 
def run_contract_pipeline(HD_INPUT):
    
    contract_items = extract_text_from_contract(HD_INPUT)
    for item in contract_items:
        content = item.get('content')
        print('len content --> ',len(content))
        ents = extract_entities_from_question(content,COMPILED)
        context = run_retrieval(driver,content,ents) #chunk_with_ents_rels
        # print('type context --> ',type(context))
        item['context'] = format_context_for_llm(context)
        law_ids = extract_ids_in_graph(context[:3])
        print(law_ids)
        item['law_ids'] = law_ids
        # ----------------------------
        law_list = get_content_from_law_id(driver,law_ids)
        item['law_list'] = law_list
    
    save_json(contract_items, 'test/contract/contract.json')
    
    for item in contract_items:
        law_list = item['law_list']
        res = 'Danh sách luật liên quan:'
        res += '\n'
        for law in law_list:
            law_title = law['text']
            law_content = law['content']
            law_res = f' - {law_title}: {law_content}'
            res += law_res
            res += '\n'
        item['related_law'] = res
        res = ''
    save_json(contract_items, 'test/contract/contract_v1.json')
    per_item_display = ''
    overall_risk_display =''
    for key in API_KEYS:
        time.sleep(10)
        try:
            client = make_client(key)
            results, total_score, overall_risk = analyze_contract(key,client, contract_items)
           
            for item, res in zip(contract_items, results):
                item['score'] = res['score']
                item['risk'] = res['risk']
                item['issues'] = res['issues']
                
                 
                item_id = item['id']
                item_content = item['content']

                # === Nội dung điều khoản ===
                contract_text = f'**📄 Nội dung hợp đồng {item_id}:** {item_content}'
                per_item_display += contract_text
                per_item_display  +='\n'

                # ===============================
                per_item_display += '⚖️ '
                per_item_display  += item['related_law']
                per_item_display  += f"\n**Độ rủi ro item:** {res['risk']}"
                per_item_display  += '\n**Vấn đề:** \n'
                issues_text = ''
                for issue in res['issues']:
                    severity = issue.get('severity', 'N/A')
                    reason = issue.get('reason', '')
                    
                    issues_text += f"  ⚠️ Lý do: {reason} ==> Mức độ nghiêm trọng: {severity}\n" 
                if len(issues_text) == 0:
                    issues_text ='Không tìm thấy vấn đề.'
                 
                    
                per_item_display += issues_text
                per_item_display +='\n'
            
            # ==============================
            overall_risk_display += f'===> Tổng quan rủi ro: {overall_risk}'
            save_json(contract_items, 'test/contract/contract_with_result.json')
            return {
                'success': True,
                'per_item':per_item_display,
                'overall_risk': overall_risk_display
            }
        except Exception as e:
            err_str = str(e)
            if any(code in err_str for code in ["401", "403", "429", "API_KEY", "quota"]):     
                print(f"Key lỗi, thử key tiếp: {e}")
                continue
            else:
                print(f"Lỗi không xác định: {e}")
                continue
    return {'success': False, 'error': 'Lỗi LLM, hãy thử lại!'}

        
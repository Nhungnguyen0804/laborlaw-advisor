from src.retrieval.run import run_retrieval
from src.utils.file_utils import save_json,load_json
from src.neo4j.connection import init_driver, close_driver
from src.neo4j.test_connect import test_connection
from src.ner_re.patterns import PATTERNS
from src.ner_re.extract_entity import extract_entities_from_question
from src.models.qwen import load_qwen, generate_answer
from src.retrieval.graph import run_retrieval_graph
from src.process_question import split_legal_ref
from copy import deepcopy
import time
import re
load_qwen()
# Compile regex 1 lần
COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [
        re.compile(p, re.IGNORECASE)
        for p in pattern_list
    ]


def laborlaw_graphrag(driver, question):

    start_time = time.perf_counter()
    answer = ""
    context_text = ""
    try:
        subquestions = split_legal_ref(question)
   
        if len(subquestions) > 0:
            for sub_question in subquestions:
                result = run_retrieval_graph(driver, sub_question)
                if result is not None:
                    answer += result
                    answer += "\n"
        else:
            answer = run_retrieval_graph(driver, question)

        if not answer:
            test_connection()
            
            query_entities = extract_entities_from_question(question,COMPILED)
            chunk_with_ents_rels = run_retrieval(driver, question, query_entities)
            context_text, answer = generate_answer(question,chunk_with_ents_rels)

        end_time = time.perf_counter()
        totalTime = round(end_time - start_time, 4)
        print(totalTime)
        return context_text, answer, totalTime

    except Exception as e:
        print(e)
        return None, None, 0 
    
def run_eval_GRAG(input_file, output_file):
    qa_dataset =load_json(input_file)
    graphrag_qa = deepcopy(qa_dataset)
    driver = init_driver()
    try:
        for index, item in enumerate(graphrag_qa):
            print(f'Câu hỏi {index +1}')
            question = item["question"]
            context_text, answer, totalTime = laborlaw_graphrag(driver,question)

            item["context_text"] = context_text if context_text else ""
            item["answer"] = answer if answer else ""
            item["totalTime"] = totalTime
        
        save_json(graphrag_qa, output_file)
    finally:
        close_driver()




# RETRY_IDS = [18,21,23,
#             30,32,33,
#             43,44,45,46,
#             52,56,58,
#             61,66,68,69,
#             74,75,79,
#             84,89,
#             90,91,94,99
#              ]
RETRY_IDS = [74]
def run_eval_GRAG_with_id(input_file, output_file,RETRY_IDS):
    qa_dataset =load_json(input_file)
    graphrag_qa = load_json(output_file)
    retry_set = set(RETRY_IDS)
    # Index graphrag_qa theo id để tìm đúng vị trí
    grag_index = {item['id']: i for i, item in enumerate(graphrag_qa)}

    driver = init_driver()
    try:
        for item in qa_dataset:
            if item['id'] not in retry_set:
                print(f"Bỏ qua id {item['id']}")
                continue

            print(f"Chạy lại id {item['id']}")
            question = item["question"]
            context_text, answer, totalTime = laborlaw_graphrag(driver, question)

            # Cập nhật đúng vị trí trong graphrag_qa
            if item['id'] in grag_index:
                pos = grag_index[item['id']]
                graphrag_qa[pos]["context_text"] = context_text or ""
                graphrag_qa[pos]["answer"] = answer or ""
                graphrag_qa[pos]["totalTime"] = totalTime
            else:
                # id mới chưa có trong output → append
                new_item = deepcopy(item)
                new_item["context_text"] = context_text or ""
                new_item["answer"] = answer or ""
                new_item["totalTime"] = totalTime
                graphrag_qa.append(new_item)
                grag_index[item['id']] = len(graphrag_qa) - 1

        save_json(graphrag_qa, output_file)
    finally:
        close_driver()

QA_DATASET = 'src/eval/QA/qa.json'
GRAG_QA = 'src/eval/QA/graphrag_qa.json'
# run_eval_GRAG(QA_DATASET,GRAG_QA)
run_eval_GRAG_with_id(QA_DATASET,GRAG_QA,RETRY_IDS)
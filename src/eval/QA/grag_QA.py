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
            load_qwen()
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

QA_DATASET = 'src/eval/QA/qa.json'
GRAG_QA = 'src/eval/QA/graphrag_qa.json'
run_eval_GRAG(QA_DATASET,GRAG_QA)
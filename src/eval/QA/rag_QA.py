from src.retrieval.run import run_retrieval_rag
from src.utils.file_utils import save_json,load_json
from src.neo4j.connection import init_driver, close_driver
from src.neo4j.test_connect import test_connection
from src.ner_re.patterns import PATTERNS
from src.ner_re.extract_entity import extract_entities_from_question
from src.models.qwen import load_qwen,generate_answer
from src.retrieval.graph import run_retrieval_graph
from src.process_question import split_legal_ref
import time
import re 
from copy import deepcopy
def rag(driver, question):
    start_time = time.perf_counter()
    answer = ""
    context_text = ""
    try: 
        test_connection()
        load_qwen()
        res = run_retrieval_rag(driver,question)
        context_text,answer = generate_answer(question,res,True) # is rag True
        end_time = time.perf_counter()
        totalTime = round(end_time - start_time, 4)
        print(totalTime)
        return context_text, answer, totalTime
    except Exception as e:
        print(e)
        return None, None, 0 

def run_eval_rag(input_file, output_file):
    qa_dataset =load_json(input_file)
    rag_qa = deepcopy(qa_dataset)
    driver = init_driver()
    try:
        for index, item in enumerate(rag_qa):
            print(f'Câu hỏi {index +1}')
            question = item["question"]
            context_text, answer, totalTime = rag(driver,question)

            item["context_text"] = context_text if context_text else ""
            item["answer"] = answer if answer else ""
            item["totalTime"] = totalTime
        
        save_json(rag_qa, output_file)
    finally:
        close_driver()

QA_DATASET = 'src/eval/QA/qa.json'
RAG_QA = 'src/eval/QA/rag_qa.json'
run_eval_rag(QA_DATASET,RAG_QA)


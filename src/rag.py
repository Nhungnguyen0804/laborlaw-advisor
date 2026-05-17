from src.retrieval.run import run_retrieval_rag
from src.utils.file_utils import save_json
from src.neo4j.connection import init_driver, close_driver
from src.neo4j.test_connect import test_connection
from src.ner_re.patterns import PATTERNS
from src.ner_re.extract_entity import extract_entities_from_question
from src.models.qwen import load_qwen,generate_answer
from src.retrieval.graph import run_retrieval_graph
from src.process_question import split_legal_ref
import time
import re 

question ='điểm a và điểm b khoản 3 điều 18 là gì '



driver = init_driver()

try:
    start_time = time.perf_counter()
    test_connection()
    load_qwen()
    # start_time = time.perf_counter()
    res = run_retrieval_rag(driver,question)
    context_text,answer = generate_answer(question,res, True) # is_rag True
    end_time = time.perf_counter()
    print("\nQUESTION:")
    print(question)

    print("\nANSWER:")
    print(answer)
    print(f"\nTotal time: {end_time - start_time:.4f} seconds")
finally:
    close_driver()

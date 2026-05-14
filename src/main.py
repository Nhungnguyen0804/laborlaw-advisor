from src.retrieval.run import run_retrieval
from src.utils.file_utils import save_json
from src.neo4j.connection import init_driver, close_driver
from src.neo4j.test_connect import test_connection
from src.ner_re.patterns import PATTERNS
from src.ner_re.extract_entity import extract_entities_from_question
from src.models.qwen import load_qwen,generate_answer
import time
import re 
COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]

question = "người lao động được nghỉ phép bao nhiêu ngày"
driver = init_driver()


try:
    test_connection()
    load_qwen()

    start_time = time.perf_counter()
    query_entities = extract_entities_from_question(question,COMPILED)
    save_json(query_entities,'test/query_entities.json')
    chunk_with_ents_rels = run_retrieval(driver,question,query_entities)
    answer = generate_answer(question,chunk_with_ents_rels)

    end_time = time.perf_counter()
    print("\nQUESTION:")
    print(question)

    print("\nANSWER:")
    print(answer)
    print(f"\nTotal time: {end_time - start_time:.4f} seconds")
finally:
    close_driver()

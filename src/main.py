from src.retrieval.run import run_retrieval
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
COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]

# question = "Điều 113 gồm những khoản nào?"
question = 'Người lao động được nghỉ phép bao nhiêu ngày'
# question ='Nội dung của điều 113'
# question ='điểm a và điểm b khoản 3 điều 18 là gì '
# question = 'Thời gian làm việc tối đa là bao nhiêu'
# question = 'Khi người lao động làm mất dụng cụ, thiết bị của doanh nghiệp thì phải xử lý như thế nào'
# question = 'điều 90 thuộc chương nào'
# question = 'luật lao động gồm bao nhiêu chương'


driver = init_driver()

try:
    start_time = time.perf_counter()
    subquestions = split_legal_ref(question)
    answer = ''
    if len(subquestions) > 1:
        for sub_question in subquestions:
            result = run_retrieval_graph(driver, sub_question)
            if result is not None:
                answer += result
                answer += '\n'
    else: 
        answer = run_retrieval_graph(driver, question)

    if not answer:

        test_connection()
        load_qwen()

        # start_time = time.perf_counter()
        query_entities = extract_entities_from_question(question,COMPILED)
        save_json(query_entities,'test/query_entities.json')
        chunk_with_ents_rels = run_retrieval(driver,question,query_entities)
        context_text,answer = generate_answer(question,chunk_with_ents_rels)

    end_time = time.perf_counter()
    print("\nQUESTION:")
    print(question)

    print("\nANSWER:")
    print(answer)
    print(f"\nTotal time: {end_time - start_time:.4f} seconds")
finally:
    close_driver()

from src.retrieval.run import run_retrieval
from src.utils.file_utils import save_json
from src.neo4j.connection import init_driver, close_driver
from src.neo4j.test_connect import test_connection
from src.ner_re.patterns import PATTERNS
from src.ner_re.extract_entity import extract_entities_from_question
from src.models.qwen import load_qwen,generate_answer
from src.utils.file_utils import save_json
import time
import re 
COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]

question = "người lao động được nghỉ phép bao nhiêu ngày"

QUESTIONS = [
    # cơ bản
    "Người lao động được nghỉ phép bao nhiêu ngày?",
    "Người lao động làm thêm giờ được trả lương như thế nào?",
    "Người lao động nữ được nghỉ thai sản bao lâu?",
    "Người lao động có được nghỉ lễ hưởng lương không?",
    "Người sử dụng lao động được giữ CCCD của người lao động không?",

    # trung bình
    "Người lao động nghỉ việc có phải báo trước không?",
    "Khi nào người lao động được đơn phương chấm dứt hợp đồng?",
    "Người lao động thử việc tối đa bao nhiêu ngày?",
    "Lương làm ban đêm được tính như thế nào?",
    "Người lao động chưa đủ 18 tuổi được làm công việc gì?",

    #  dễ hallucinate
    "Người lao động có được nghỉ 42 ngày phép không?",
    "Làm việc 2 công ty có được hưởng gấp đôi bảo hiểm xã hội không?",
    "Người lao động làm 5 năm được cộng thêm bao nhiêu ngày phép?",
    "Nghỉ thai sản có được hưởng cả lương công ty và bảo hiểm xã hội không?",

    # khó hơn cho RAG
    "Người lao động tự ý nghỉ việc 5 ngày liên tục có bị sa thải không?",
    "Hợp đồng lao động bằng miệng có hợp pháp không?",
    "Người lao động bị tai nạn lao động được bồi thường thế nào?",
    "Người sử dụng lao động được phép phạt tiền nhân viên không?",

    # Anti-hallucination
    "Người lao động được nghỉ phép 12 ngày và thêm 14 ngày đúng không?",

    # Retrieval test
    "Người lao động làm việc trong điều kiện đặc biệt nặng nhọc được nghỉ bao nhiêu ngày?"
]
def save_txt(results, path):
    with open(path, "w", encoding="utf-8") as file:

        for result in results:
            question_id = result["id"]
            question = result["question"]
            answer = result.get("answer", "N/A")
            time_taken = result.get("time_seconds", "N/A")

            file.write(f"Question {question_id}\n")
            file.write(f"Q:{question}\n")
            file.write(f"A:{answer}\n")
            file.write(f"Time: {time_taken}s\n")
            file.write("----------------------------\n")

def run_test(questions):
    results = []
    driver = init_driver()
    try:
        test_connection()
        load_qwen()

        total_start = time.perf_counter()
        for idx, question in enumerate(questions, 1):
            print(f"[{idx}/{len(questions)}] QUESTION: {question}")
            result = {
                "id": idx,
                "question": question,
                "answer": None,  
                "time_seconds": None,
            }
            try:
                start_time = time.perf_counter()
                query_entities = extract_entities_from_question(question,COMPILED)
                save_json(query_entities,'test/query_entities.json')
                chunk_with_ents_rels = run_retrieval(driver,question,query_entities)
                answer = generate_answer(question,chunk_with_ents_rels)

                end_time = time.perf_counter()
                elapsed = end_time - start_time
                result["answer"] = answer
                result["entities"] = query_entities
                result["time_seconds"] = round(elapsed, 4)

                print(f"ANSWER: {answer}")
                print(f"Time: {elapsed:.4f}s")
            except Exception as e:
                print(f"ERROR: {e}")
            results.append(result)
        total_end = time.perf_counter()
        total_elapsed = total_end - total_start

     
        output = {
            "total_questions": len(questions),
            "results": results,
        }
           
        save_json(output, 'test/test_main.json')
        save_txt(results, "test/test_main.txt")
    finally:
        close_driver()

run_test(QUESTIONS)
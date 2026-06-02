import re
import time
import chainlit as cl
from chainlit import Text
import asyncio
from src.retrieval.run import run_retrieval
from src.utils.file_utils import save_json
from src.neo4j.connection import init_driver, close_driver
from src.neo4j.test_connect import test_connection
from src.ner_re.patterns import PATTERNS
from src.ner_re.extract_entity import extract_entities_from_question
from src.models.qwen import load_qwen, generate_answer
from src.retrieval.graph import run_retrieval_graph
from src.process_question import split_legal_ref
from src.contract.run import run_contract_pipeline
import os 
import shutil
import textwrap

load_qwen() 
driver = None
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]
@cl.on_chat_start
async def on_chat_start():
    global driver
    if driver is None:
        driver = init_driver()
    # load_qwen()
    # await cl.Message(content="Xin chào! Hãy đặt câu hỏi về Luật Lao động.").send()



#reply
# @cl.on_message
# async def on_message(message: cl.Message):
#     await cl.Message(content="Xin chào!").send()

@cl.on_message

async def on_message(message: cl.Message):
    question = message.content.strip()
    thinking = cl.Message(content="Đang suy nghĩ...")
    await thinking.send()
    start_time = time.perf_counter()
    # Xử lý nếu có file đính kèm
    if message.elements:
        for element in message.elements:
            # Chỉ PDF
            if not element.name.lower().endswith(".pdf"):
                thinking.content=f"File '{element.name}' không phải PDF. Chỉ nhận file pdf !"
                await thinking.update()
                return

            # Lưu file 
            save_path = os.path.join(UPLOAD_DIR, element.name)
            shutil.copy(element.path, save_path)
            
            thinking.content=f"Phân tích hợp đồng"
            await thinking.update()

            try:
                # doi gem ma ko block UI 
                result  = await asyncio.to_thread(run_contract_pipeline, save_path)
                elapsed = time.perf_counter() - start_time
                if not result['success']:
                    thinking.content = result['error']
                else:              
                    thinking.content = (
                        f"## 🔍 Kết quả phân tích hợp đồng như sau:\n\n"
                        f"{result['per_item']}\n"
                        f"### Đánh giá rủi ro tổng thể\n{result['overall_risk']}\n"
                        f"{elapsed:.2f}s"
                    )
                    
                await thinking.update()
            except Exception as e:
                thinking.content = f"Lỗi khi phân tích: {e}"
                await thinking.update()
            return
    
    # Hệ thống tư vấn =================================================================================
    start_time = time.perf_counter()
    answer = ""
    subquestions = split_legal_ref(question)
    if len(subquestions) > 1:
        for sub_q in subquestions:
            result = run_retrieval_graph(driver, sub_q)
            if result:
                answer += result + "\n"
    else:
        answer = run_retrieval_graph(driver, question) or ""

    if not answer:
        test_connection()
        # load_qwen()
        query_entities = extract_entities_from_question(question, COMPILED)
        save_json(query_entities, "test/query_entities.json")
        chunk_with_ents_rels = run_retrieval(driver, question, query_entities)

        thinking.content = "Đang sinh câu trả lời (có thể mất ít thời gian)..."
        await thinking.update()
        # _, answer = generate_answer(question, chunk_with_ents_rels)
        _, answer = await asyncio.to_thread(generate_answer, question, chunk_with_ents_rels)

    elapsed = time.perf_counter() - start_time
    thinking.content = f"{answer}\n{elapsed:.2f}s"
    await thinking.update()


@cl.on_chat_end
async def on_chat_end():
    global driver
    if driver:
        close_driver()
        driver = None
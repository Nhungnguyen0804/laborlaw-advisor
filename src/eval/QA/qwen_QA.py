
from src.utils.file_utils import save_json,load_json
import time
import re 
from copy import deepcopy

import os
import time
import json
from pathlib import Path

os.environ["HF_HOME"] = "E:/huggingface"
os.environ["HUGGINGFACE_HUB_CACHE"] = "E:/huggingface/hub"
os.environ["TRANSFORMERS_CACHE"] = "E:/huggingface/transformers"


from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
GEN_CONFIG = {
    "max_new_tokens": 512, # 1000 180
    "temperature": 0.1, # 0.3
    "do_sample": True, #True
    "top_p": 0.85,
    "repetition_penalty": 1.15,
}

tokenizer = None
model = None
def load_qwen():

    global tokenizer, model

    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME,cache_dir="E:/huggingface")

    if model is None:
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
            device_map="cpu",
            cache_dir="E:/huggingface"
        )

    print("Done load Qwen model!")



def build_messages(question):


    system_prompt = """
You are a Vietnamese labor law assistant.

ANSWERING RULES:

1. Answer in Vietnamese only
2. Only use information from the provided legal articles
3. DO NOT copy the law text verbatim
4. MUST summarize concisely (maximum 10 lines)
5. Answer directly to the question
6. Only include directly relevant information
7. Always start with: 'Theo Điều ...'
8. If multiple cases exist --> list them briefly using bullet points
9. Do not mention sources like 'provided text' or 'I found'

LOGIC RULES (IMPORTANT):
10. If multiple values represent alternatives --> use 'hoặc', DO NOT sum them
11. Only sum values if they are explicitly additive (example: base + additional)
12. Do not perform any calculations unless clearly required
13. If unsure whether to sum or not --> DO NOT sum

"""

    return  [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""
                CÂU HỎI:
                {question}
                TRẢ LỜI:
                """
        }
    ]

def generate_answer(question):

    messages = build_messages(question)

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt"
    )

    outputs = model.generate(
        **inputs,
        **GEN_CONFIG,
        pad_token_id=tokenizer.eos_token_id
    )

    raw = tokenizer.decode(
        outputs[0][len(inputs.input_ids[0]):],
        skip_special_tokens=True
    )

    answer = raw

    return answer

def qwen( question):
    start_time = time.perf_counter()
    answer = ""
    context_text = ""
    try: 
        load_qwen()
        answer = generate_answer(question) 
        end_time = time.perf_counter()
        totalTime = round(end_time - start_time, 4)
        print(totalTime)
        return  answer, totalTime
    except Exception as e:
        print(e)
        return None, None, 0 

def run_eval_qwen(input_file, output_file):
    qa_dataset =load_json(input_file)
    qwen_qa = deepcopy(qa_dataset)
   
    
    for index, item in enumerate(qwen_qa):
        print(f'Câu hỏi {index +1}')
        question = item["question"]
        answer, totalTime = qwen(question)

        item["context_text"] = ""
        item["answer"] = answer if answer else ""
        item["totalTime"] = totalTime
        
    save_json(qwen_qa, output_file)
   

QA_DATASET = 'src/eval/QA/qa.json'
qwen_qa = 'src/eval/QA/qwen_qa.json'
run_eval_qwen(QA_DATASET,qwen_qa)


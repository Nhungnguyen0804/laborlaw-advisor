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


def format_context_for_llm(chunks):
    chunks = chunks[:3]  # top 3cai thien toc do
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        # Lấy nội dung chính
        content = chunk.get("content_with_context", "")
        
        # Lấy metadata
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

def build_messages(question, chunks):

    context_text = format_context_for_llm(chunks)

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

    return [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": f"""
                THÔNG TIN PHÁP LUẬT:
                {context_text}
                CÂU HỎI:
                {question}
                TRẢ LỜI:
                """
        }
    ]

def generate_answer(question, chunks):

    messages = build_messages(question, chunks)

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

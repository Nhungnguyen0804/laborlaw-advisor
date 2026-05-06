import os
import time
import json
from pathlib import Path

os.environ["HF_HOME"] = "E:/huggingface"
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
GEN_CONFIG = {
    "max_new_tokens": 1000,
    "temperature": 0.3,
    "do_sample": True,
    "top_p": 0.85,
    "repetition_penalty": 1.15,
}


def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_relevant_contexts(data, question, top_k=5):

    question_lower = question.lower()
    keywords = set(question_lower.split())
    
    scored_contexts = []
    
    # Duyệt qua nodes_with_context
    for node in data.get("nodes_with_context", []):
        node_text = node.get("text", "").lower()
        entity_type = node.get("entity_type", "")
        
        # Tính điểm relevance 
        score = 0
        for keyword in keywords:
            if keyword in node_text:
                score += 2
        
        # Ưu tiên các entity type quan trọng
        if entity_type in ["OBLIGATION", "RIGHT", "TIME_PERIOD", "CONDITION"]:
            score += 1
        
        # Lấy legal contexts
        for ctx in node.get("legal_contexts", []):
            scored_contexts.append({
                "score": score,
                "article": ctx.get("article", ""),
                "article_title": ctx.get("article_title", ""),
                "content": ctx.get("content", ""),
                "entity_text": node.get("text", ""),
                "entity_type": entity_type
            })
    
    # Sắp xếp theo score và lấy top_k
    scored_contexts.sort(key=lambda x: x["score"], reverse=True)
    return scored_contexts[:top_k]


def build_qa_prompt(question: str, contexts: list) -> list:

    
    # Loại bỏ duplicate articles
    seen_articles = set()
    unique_contexts = []
    for ctx in contexts:
        article_id = f"{ctx['article']}-{ctx['article_title']}"
        if article_id not in seen_articles:
            seen_articles.add(article_id)
            unique_contexts.append(ctx)
    
    # Format contexts
    context_parts = []
    for i, ctx in enumerate(unique_contexts, 1):
        article_info = f"Điều {ctx['article']}: {ctx['article_title']}" if ctx['article'] else "Quy định"
        content = ctx['content'].strip()
        
        context_parts.append(
            f"{i}. {article_info}\n"
            f"   Nội dung: {content}\n"
            f"   (Liên quan: {ctx['entity_text']} - {ctx['entity_type']})"
        )
    
    context_text = "\n\n".join(context_parts)
    prompt_require = '''

"You are a Vietnamese labor law assistant.\\n\\n"

"ANSWERING RULES:\\n"
"1. Answer in Vietnamese only\\n"
"2. Only use information from the provided legal articles\\n"
"3. DO NOT copy the law text verbatim\\n"
"4. MUST summarize concisely (maximum 10 lines)\\n"
"5. Answer directly to the question\\n"
"6. Only include directly relevant information\\n"
"7. Always start with: 'Theo Điều ...'\\n"
"8. If multiple cases exist → list them briefly using bullet points\\n"
"9. Do not mention sources like 'provided text' or 'I found'\\n"

"LOGIC RULES (IMPORTANT):\\n"
"10. If multiple values represent alternatives → use 'hoặc', DO NOT sum them\\n"
"11. Only sum values if they are explicitly additive (e.g., base + additional)\\n"
"12. Do not perform any calculations unless clearly required\\n"
"13. If unsure whether to sum or not → DO NOT sum\\n"

'''

    return [
        {
            "role": "system",
            "content": prompt_require
        },
        {
            "role": "user",
            "content": (
                f"THÔNG TIN TỪ PHÁP LUẬT:\n"
                f"{context_text}\n\n"
                f"CÂU HỎI: {question}\n\n"
                f"TRẢ LỜI (dựa trên các điều luật trên):"
            )
        }
    ]

def clean_answer(text: str) -> str:
    """Làm sạch câu trả lời"""
    text = text.strip()
    
    # Loại bỏ các câu lặp lại cuối
    lines = text.split('\n')
    unique_lines = []
    seen = set()
    for line in lines:
        line_clean = line.strip()
        if line_clean and line_clean not in seen:
            unique_lines.append(line)
            seen.add(line_clean)
    
    return '\n'.join(unique_lines)


def main():
    import json
    import os
    import sys

    log_path = os.path.join(os.path.dirname(__file__), "qwen.txt")
    log_file = open(log_path, "w", encoding="utf-8")
    sys.stdout = log_file

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
        device_map="cpu"
    )
    print("done load model!\n")
    
    data_path = 'src/kg/enrich.json' 
    
    if not Path(data_path).exists():
        print(f"File not found: {data_path}")
        return
    
 
    enriched_data = load_data(data_path)
    
    # print(f"Total entities: {enriched_data['metadata']['total_entities']}")
    # print(f"Total relations: {enriched_data['metadata']['total_relations']}")
    # print(f"Chunks processed: {enriched_data['metadata']['total_chunks_processed']}")
    
   
    test_questions = [
        "người lao động được nghỉ phép bao nhiêu ngày",
        "nghỉ phép hằng năm tăng thêm như thế nào",
        "thời gian làm việc tối đa trong 1 tuần là bao nhiêu"
    ]
    
    for question in test_questions:
    
        # Extract contexts
        contexts = extract_relevant_contexts(enriched_data, question, top_k=5)
        
        if not contexts:
            print(f"question: {question}\n ---> llm answer: Không tìm thấy dữ liệu phù hợp\nsource used:\n")
            continue
        
        # Build prompt
        messages = build_qa_prompt(question, contexts)
        
        prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Generate
        start = time.perf_counter()
        
        outputs = model.generate(
            **inputs,
            **GEN_CONFIG,
            pad_token_id=tokenizer.eos_token_id
        )
        
        gen_time = time.perf_counter() - start
        
        raw = tokenizer.decode(
            outputs[0][len(inputs.input_ids[0]):],
            skip_special_tokens=True
        )
        
        answer = clean_answer(raw)
        
        print(f"question: {question}")
        print(f" ---> llm answer: {answer}")
        print("source used:")
        
        for ctx in contexts:
            article = ctx['article']
            title = ctx['article_title']
            print(f"Điều {article}: {title}")
        
        print()  
    sys.stdout.flush()
    log_file.close()
    sys.stdout = sys.__stdout__
    print(f"save {log_path}")

if __name__ == "__main__":
    main()
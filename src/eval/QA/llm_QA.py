import json
import time
import os
from copy import deepcopy
 
from google import genai
from src.utils.file_utils import save_json,load_json
key = 'api'
API_KEY =  key
MODEL_NAME = "models/gemini-2.5-flash"

QA_INPUT = "src/eval/QA/qa.json"
GEMINI_QA_OUTPUT= "src/eval/QA/gemini_qa.json"
CHECKPOINT_FILE = "src/eval/QA/gemini_checkpoint.json"

# START_ID = 0
# START_ID = 15
# START_ID = 36
# START_ID = 57
# START_ID = 77
START_ID = 98
RETRY_SLEEP = 10
MAX_RETRIES = 3
BETWEEN_CALLS = 4

def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        try:
            cp = load_json(CHECKPOINT_FILE)
            return cp.get("next_id", 0)
        except Exception:
            pass
    return 0

def save_checkpoint(next_id):
    os.makedirs(os.path.dirname(CHECKPOINT_FILE) or ".", exist_ok=True)
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"next_id": next_id}, f)

def load_or_init_output(qa_dataset):
    """
    Nếu output file đã tồn tại → load lại.
    Nếu chưa → tạo mới từ qa_dataset.
    """
    if os.path.exists(GEMINI_QA_OUTPUT):
        try:
            existing = load_json(GEMINI_QA_OUTPUT)
            if len(existing) == len(qa_dataset):
                print(f"Đọc output cũ: {GEMINI_QA_OUTPUT}")
                return existing
        except Exception:
            pass
    fresh = deepcopy(qa_dataset)
    for item in fresh:
        item.setdefault("gemini_context", "")
        item.setdefault("gemini_answer", "")
        item.setdefault("gemini_time", 0)
    return fresh


def build_prompt(question):
    return (
        "Bạn là trợ lý pháp lý chuyên về luật lao động Việt Nam. "
        "Hãy trả lời câu hỏi sau một cách chính xác và súc tích.\n\n"
        f"Câu hỏi: {question}\n\n"
        "Trả lời:"
    )


def is_quota_error(e):
    """Nhận diện lỗi hết quota / rate-limit."""
    # ClientError có status_code
    print(f"  [DEBUG error] type={type(e).__name__}, detail={e}") 
    if hasattr(e, "status_code") and e.status_code == 429:
        return True
    msg = str(e).lower()
    return any(k in msg for k in ("429", "quota", "resource_exhausted", "toomanyrequests", "rate limit"))

def is_config_error(e):
    if hasattr(e, "status_code") and e.status_code in (400, 401, 403, 404):
        return True
    msg = str(e).lower()
    return any(k in msg for k in ("404", "not found", "invalid", "api_key", "permission denied"))
def call_gemini(client, question):
    prompt = build_prompt(question)
    last_exc = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            t0 = time.perf_counter()
            response = client.models.generate_content(model=MODEL_NAME,contents=prompt,)
            elapsed = round(time.perf_counter() - t0, 4)
            answer = response.text.strip() if response.text else ""
            return prompt, answer, elapsed
 
        except Exception as e:
            last_exc = e
            if is_quota_error(e) or is_config_error(e):
                raise   # không retry
            print(f"  [warn] lần {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_SLEEP)
 
    raise last_exc

def run_eval_gemini():
    client = genai.Client(api_key=API_KEY)

    if START_ID is not None:
        start = START_ID
        print(f"START_ID override = {start}")
    else:
        start = load_checkpoint()
        print(f"Tiếp tục từ câu index {start}")


    qa_dataset = load_json(QA_INPUT)
    results    = load_or_init_output(qa_dataset)
    total      = len(qa_dataset)
    print(f"Tổng số câu: {total}, bắt đầu từ: {start}\n")
 
    for idx in range(start, total):
        item     = results[idx]
        question = item["question"]
        print(f"Câu {idx + 1}/{total}: {question[:80]}...")
 
        try:
            context_text, answer, elapsed = call_gemini(client, question)

            item["gemini_context"] = context_text
            item["gemini_answer"]  = answer
            item["gemini_time"]    = elapsed
 
            # Lưu sau mỗi câu
            save_json(results, GEMINI_QA_OUTPUT)
            save_checkpoint(idx + 1)          # next_id = câu tiếp theo
 
            print(f"{elapsed}s | saved => {GEMINI_QA_OUTPUT}")
 
        except Exception as e:
            err_str = str(e).lower()
            if is_quota_error(e):
                print(f"\nHết quota tại câu {idx + 1} (index {idx}).")
                print(f"Đổi API_KEY mới, để START_ID = {idx}\n")
                # Checkpoint đã lưu idx (câu hiện tại chưa xong) → resume đúng chỗ
                save_checkpoint(idx)
                break
            elif is_config_error(e):
                print(f"\nLỗi cấu hình – dừng hẳn: {e}")
                save_checkpoint(idx)
                break
            else:
                # Lỗi khác → ghi rỗng và đi tiếp, không dừng cả pipeline
                print(f"bỏ qua câu {idx + 1}: {e}")
                item["gemini_context"] = ""
                item["gemini_answer"]  = f"[ERROR] {e}"
                item["gemini_time"]    = 0
                save_json(results, GEMINI_QA_OUTPUT)
                save_checkpoint(idx + 1)
 
        time.sleep(BETWEEN_CALLS)
 
    else:
        # Chạy hết vòng lặp (không bị break bởi quota)
        print(f"\ndone, kết quả: {GEMINI_QA_OUTPUT}")
        # Xóa checkpoint vì đã xong
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            print("Đã xóa checkpoint.")

run_eval_gemini()


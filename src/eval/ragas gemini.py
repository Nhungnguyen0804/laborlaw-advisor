import json
import csv
import os
import time
import sys
from tqdm import tqdm
import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential

GTRUTH_FILE   = "src/eval/QA/gtruth_qa.json"
RAG_FILE  = "src/eval/QA/rag_qa.json"
GRAPHRAG_FILE = "src/eval/QA/graphrag_qa.json"
LLMONLY_FILE  = "src/eval/QA/qwen_qa.json"
 
JUDGE_MODEL = "gemini-2.0-flash"
EMBEDDING_MODEL = "models/text-embedding-004"
import random
BATCH_SIZE  = 5     # số sample mỗi lần gửi RAGAS
SLEEP_BETWEEN_BATCHES  = random.uniform(3, 6)   # giây nghỉ giữa các batch
SLEEP_BETWEEN_PIPELINES  = 15    # giây nghỉ giữa các pipeline
SLEEP_ON_QUOTA_ERROR  = 60    # giây nghỉ khi bị quota
 
CHECKPOINT_FILE  = "src/eval/ragas_checkpoint.json"
PARTIAL_CSV  = "src/eval/partial_results.csv"
SUMMARY_JSON  = "src/eval/results_summary.json"
DETAIL_CSV  = "src/eval/results_detail.csv"
 
METRIC_KEYS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]


load_dotenv()

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("Không tìm thấy GOOGLE_API_KEY.")

    sys.exit(1)

llm = LangchainLLMWrapper(
    ChatGoogleGenerativeAI(
        model=JUDGE_MODEL,
        temperature=0,
        google_api_key=GOOGLE_API_KEY,
        # Tự động retry khi bị rate limit ở cấp độ LangChain
        max_retries=3,
    )
)

embeddings = LangchainEmbeddingsWrapper(
    GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY,
    )
)

 
metrics = [
    Faithfulness(),       # answer có bịa ngoài context không?
    AnswerRelevancy(),    # answer có trả lời đúng câu hỏi không?
    ContextPrecision(),   # context retrieve có trúng không?
    ContextRecall(),      # context có đủ info để trả lời không?
]

def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
 
 
def is_quota_error(exception):
    msg = str(exception).lower()
    return any(keyword in msg for keyword in ["429", "quota", "resource exhausted", "rate limit"])
 
 
def load_checkpoint():
    if not os.path.exists(CHECKPOINT_FILE):
        return None
    with open(CHECKPOINT_FILE, encoding="utf-8") as f:
        return json.load(f)
 
 
def save_checkpoint(pipeline_name, next_index):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump({"pipeline": pipeline_name, "next_index": next_index}, f)
 
 
def clear_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
 
 
def append_to_partial_csv(df_batch):
    write_header = not os.path.exists(PARTIAL_CSV)
    df_batch.to_csv(PARTIAL_CSV, mode="a", header=write_header, index=False, encoding="utf-8-sig")
 
 
def format_eta(seconds):
    minutes = int(seconds // 60)
    secs    = int(seconds % 60)
    return f"{minutes}p {secs}s"

gtruth_map = {d["id"]: d for d in read_json(GTRUTH_FILE)}
 
def build_rows(path, pipeline_name):
    rows = []
    for d in read_json(path):
        if d.get("id") not in gtruth_map:
            continue
 
        # LLM-only không có context thì dùng list rỗng, không phải "N/A"
        if pipeline_name == "LLM_only":
            contexts = []
        else:
            ctx = d.get("context_text") or ""
            contexts = [ctx] if ctx else []
 
        rows.append({
            "id":  d["id"],
            "question": d["question"],
            "answer":  d["answer"],
            "contexts":  contexts,
            "ground_truth": gtruth_map[d["id"]]["answer"],
            "question_type": d.get("question_type", "unknown"),
        })
    return rows
 
 
pipelines = {
    "RAG": build_rows(RAG_FILE, "RAG"),
    "GraphRAG": build_rows(GRAPHRAG_FILE, "GraphRAG"),
    "LLM_only": build_rows(LLMONLY_FILE,  "LLM_only"),
}
 
print("\nSố câu hỏi mỗi pipeline:")
for name, rows in pipelines.items():
    print(f"  {name}: {len(rows)} câu")
def eval_batch(batch_rows, pipeline_name, batch_index):
    dataset = Dataset.from_list([
        {
            "question": r["question"],
            "answer":  r["answer"],
            "contexts": r["contexts"],
            "ground_truth": r["ground_truth"],
        }
        for r in batch_rows
    ])
 
    max_retries = 4
    for attempt in range(max_retries):
        try:
            result = evaluate(
                dataset,
                metrics=metrics,
                llm=llm,
                embeddings=embeddings,
                raise_exceptions=False
            )
            return result
 
        except Exception as e:
            if is_quota_error(e):
                print(f"\n  [QUOTA] Batch {batch_index} bị giới hạn API. Nghỉ {SLEEP_ON_QUOTA_ERROR}s rồi thử lại...")
                time.sleep(SLEEP_ON_QUOTA_ERROR)
            else:
                print(f"\n  [LỖI] Batch {batch_index} lỗi không phải quota: {e}")
                if attempt == max_retries - 1:
                    print(f"  Bỏ qua batch {batch_index} sau {max_retries} lần thử.")
                    return None
                time.sleep(10)
 
    return None
 

checkpoint = load_checkpoint()
if checkpoint:
    print(f"\n[RESUME] Tiếp tục từ pipeline '{checkpoint['pipeline']}', sample #{checkpoint['next_index']}")
 
all_dfs = {}
 
pipeline_names = list(pipelines.keys())
 
for pipeline_name in pipeline_names:
    rows = pipelines[pipeline_name]
 
    # Xác định bắt đầu từ đâu (resume hay từ đầu)
    start_index = 0
    if checkpoint and checkpoint["pipeline"] == pipeline_name:
        start_index = checkpoint["next_index"]
        print(f"\n[RESUME] Pipeline {pipeline_name}: tiếp tục từ sample {start_index}/{len(rows)}")
    elif checkpoint and list(pipeline_names).index(pipeline_name) < list(pipeline_names).index(checkpoint["pipeline"]):
        print(f"\n[SKIP] Pipeline {pipeline_name} đã hoàn thành trước đó, bỏ qua.")
        continue
 
    print(f"\n{'='*60}")
    print(f"Pipeline: {pipeline_name}  ({len(rows)} câu, bắt đầu từ #{start_index})")
    print(f"{'='*60}")
 
    pipeline_dfs   = []
    processed      = 0
    time_per_batch = []
 
    batches = range(start_index, len(rows), BATCH_SIZE)
 
    for start in tqdm(batches, desc=f"{pipeline_name}", unit="batch"):
        batch_rows   = rows[start : start + BATCH_SIZE]
        batch_index  = start // BATCH_SIZE
        t0  = time.time()
 
        result = eval_batch(batch_rows, pipeline_name, batch_index)
 
        if result is None:
            print(f"  Batch {batch_index} thất bại, tiếp tục batch tiếp theo.")
            save_checkpoint(pipeline_name, start + BATCH_SIZE)
            continue
 
        # Gắn metadata vào dataframe
        df_batch = result.to_pandas()
        df_batch["question_type"] = [r["question_type"] for r in batch_rows]
        df_batch["id"]    = [r["id"]  for r in batch_rows]
        df_batch["pipeline"] = pipeline_name
 
        pipeline_dfs.append(df_batch)
        append_to_partial_csv(df_batch)
 
        # Tính ETA
        elapsed = time.time() - t0
        time_per_batch.append(elapsed)
        avg_time  = sum(time_per_batch) / len(time_per_batch)
        remaining_batches = (len(rows) - (start + BATCH_SIZE)) / BATCH_SIZE
        eta_seconds = avg_time * remaining_batches
        processed  += len(batch_rows)
 
        tqdm.write(f"  Batch {batch_index}: {len(batch_rows)} sample | {elapsed:.1f}s | ETA: {format_eta(eta_seconds)}")
 
        # Cập nhật checkpoint
        save_checkpoint(pipeline_name, start + BATCH_SIZE)
 
        # Nghỉ ngẫu nhiên để tránh rate limit
        time.sleep(random.uniform(3, 6))
 
    if pipeline_dfs:
        all_dfs[pipeline_name] = pd.concat(pipeline_dfs, ignore_index=True)
        print(f"\n  Hoàn thành {pipeline_name}: {len(all_dfs[pipeline_name])} sample.")
 
    # Nghỉ giữa các pipeline
    if pipeline_name != pipeline_names[-1]:
        print(f"\n  Nghỉ {SLEEP_BETWEEN_PIPELINES}s trước pipeline tiếp theo...")
        time.sleep(SLEEP_BETWEEN_PIPELINES)
 
clear_checkpoint()
 

if not all_dfs:
    print("\n[LỖI] Không có pipeline nào thành công.")
    sys.exit(1)
 
col_names = list(all_dfs.keys())
 
summary = {}
for name, df in all_dfs.items():
    summary[name] = {k: round(float(df[k].mean()), 4) for k in METRIC_KEYS if k in df.columns}
 
print("\n" + "=" * 70)
print("KẾT QUẢ TỔNG:")
print("=" * 70)
print(f"{'Metric':<25}" + "".join(f"{n:>15}" for n in col_names))
print("-" * 70)
for metric in METRIC_KEYS:
    row = f"{metric:<25}"
    for name in col_names:
        val = summary.get(name, {}).get(metric, float("nan"))
        row += f"{val:>15.4f}"
    print(row)
print("=" * 70)
 
print("\nBREAKDOWN THEO LOẠI CÂU HỎI:")
for name in col_names:
    print(f"\n  [{name}]")
    print(all_dfs[name].groupby("question_type")[METRIC_KEYS].mean().round(3).to_string())

output = {
    "judge_model":  JUDGE_MODEL,
    "embedding_model": EMBEDDING_MODEL,
    "summary": summary,
    "breakdown_by_type": {
        name: all_dfs[name].groupby("question_type")[METRIC_KEYS].mean().round(4).to_dict()
        for name in col_names
    },
}
 
with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
 
combined_df = pd.concat(list(all_dfs.values()), ignore_index=True)
combined_df.to_csv(DETAIL_CSV, index=False, encoding="utf-8-sig")
 
print(f"\nĐã lưu: {SUMMARY_JSON} + {DETAIL_CSV}")
print(f"(File tạm từng batch: {PARTIAL_CSV})")
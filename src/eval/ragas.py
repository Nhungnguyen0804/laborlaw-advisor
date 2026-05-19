import json
import csv
import os
import time
import sys
import random
from tqdm import tqdm
import pandas as pd
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_ollama import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from ragas import evaluate, RunConfig

run_config = RunConfig(
    max_workers=1,        # chạy tuần tự, không parallel
    timeout=300,          # tăng timeout lên 120s mỗi request
    max_retries=3,
)
#  Cấu hình file đầu vào 
GTRUTH_FILE   = "src/eval/QA/gtruth_qa.json"
RAG_FILE      = "src/eval/QA/rag_qa.json"
GRAPHRAG_FILE = "src/eval/QA/graphrag_qa.json"
LLMONLY_FILE  = "src/eval/QA/qwen_qa.json"

#  Cấu hình model 
JUDGE_MODEL     = "qwen2.5:7b"      # model đã pull bằng ollama
EMBEDDING_MODEL = "nomic-embed-text"       
OLLAMA_BASE_URL = "http://localhost:11434"

#  Cấu hình batch & sleep 
BATCH_SIZE  = 2
SLEEP_BETWEEN_BATCHES  = random.uniform(1, 3)   # Ollama local, không cần nghỉ nhiều

SLEEP_ON_ERROR  = 15

#  File checkpoint / output 
CHECKPOINT_FILE = "src/eval/ragas_checkpoint.json"
PARTIAL_CSV     = "src/eval/partial_results.csv"
SUMMARY_JSON    = "src/eval/results_summary.json"
DETAIL_CSV      = "src/eval/results_detail.csv"

METRIC_KEYS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

#  Khởi tạo LLM & Embeddings 
llm = LangchainLLMWrapper(
    ChatOllama(
        model=JUDGE_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )
)

embeddings = LangchainEmbeddingsWrapper(
    OllamaEmbeddings(
        model=EMBEDDING_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
)

metrics = [
    # Faithfulness(),
    AnswerRelevancy(),
    # ContextPrecision(),
    # ContextRecall(),
]

#  Helper functions 
def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_error(exception):
    """ Ollama local, chủ yếu bắt lỗi kết nối hoặc timeout."""
    msg = str(exception).lower()
    return any(k in msg for k in ["connection", "timeout", "refused", "500"])


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
    secs = int(seconds % 60)
    return f"{minutes}p {secs}s"


ground_truth_list = read_json(GTRUTH_FILE)

gtruth_map = {}

for item in ground_truth_list:
    doc_id = item["id"]
    gtruth_map[doc_id] = item

def build_rows(path, pipeline_name):
    rows = []
    for d in read_json(path):
        if d.get("id") not in gtruth_map:
            continue
        if pipeline_name == "LLM_only":
            contexts = []
        else:
            ctx = d.get("context_text") or ""
            contexts = [ctx] if ctx else []

        rows.append({
            "id": d["id"],
            "question": d["question"],
            "answer": d["answer"],
            "contexts": contexts,
            "ground_truth":  gtruth_map[d["id"]]["answer"],
            "question_type": d.get("question_type", "unknown"),
        })
    return rows


pipelines = {
    "RAG":  build_rows(RAG_FILE, "RAG"),
    "GraphRAG": build_rows(GRAPHRAG_FILE, "GraphRAG"),
    "LLM_only": build_rows(LLMONLY_FILE, "LLM_only"),
}

print("\nSố câu hỏi mỗi pipeline:")
for name, rows in pipelines.items():
    print(f"  {name}: {len(rows)} câu")


#  Eval một batch 
def eval_batch(batch_rows, pipeline_name, batch_index):
    dataset = Dataset.from_list([
        {
            "question": r["question"],
            "answer": r["answer"],
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
                run_config=run_config,
                raise_exceptions=False,
            )
            return result
        except Exception as e:
            print(f"\nLỖI-->Batch {batch_index} (lần {attempt+1}): {e}")
            if attempt == max_retries - 1:
                print(f"  Bỏ qua batch {batch_index} sau {max_retries} lần thử.")
                return None
            time.sleep(SLEEP_ON_ERROR)

    return None


#  Main loop 
checkpoint     = load_checkpoint()
if checkpoint:
    print(f"\n--->Tiếp tục từ pipeline '{checkpoint['pipeline']}', sample #{checkpoint['next_index']}")

all_dfs  = {}
pipeline_names = list(pipelines.keys())

for pipeline_name in pipeline_names:
    rows = pipelines[pipeline_name]

    start_index = 0
    if checkpoint and checkpoint["pipeline"] == pipeline_name:
        start_index = checkpoint["next_index"]
        print(f"\n[-->Pipeline {pipeline_name}: tiếp tục từ sample {start_index}/{len(rows)}")
    elif checkpoint and pipeline_names.index(pipeline_name) < pipeline_names.index(checkpoint["pipeline"]):
        print(f"\nSKIP--> Pipeline {pipeline_name} đã hoàn thành trước đó, bỏ qua.")
        continue

    print(f"\n==================================")
    print(f"Pipeline: {pipeline_name}  ({len(rows)} câu, bắt đầu từ #{start_index})")
    print(f"====================================")

    pipeline_dfs = []
    time_per_batch = []

    for start in tqdm(range(start_index, len(rows), BATCH_SIZE), desc=pipeline_name, unit="batch"):
        batch_rows  = rows[start : start + BATCH_SIZE]
        batch_index = start // BATCH_SIZE
        t0 = time.time()

        result = eval_batch(batch_rows, pipeline_name, batch_index)

        if result is None:
            save_checkpoint(pipeline_name, start + BATCH_SIZE)
            continue

        df_batch = result.to_pandas()
        df_batch["question_type"] = [r["question_type"] for r in batch_rows]
        df_batch["id"] = [r["id"] for r in batch_rows]
        df_batch["pipeline"]  = pipeline_name

        pipeline_dfs.append(df_batch)
        append_to_partial_csv(df_batch)

        elapsed = time.time() - t0
        time_per_batch.append(elapsed)
        avg_time          = sum(time_per_batch) / len(time_per_batch)
        remaining_batches = (len(rows) - (start + BATCH_SIZE)) / BATCH_SIZE
        eta_seconds       = avg_time * max(remaining_batches, 0)

        tqdm.write(f"  Batch {batch_index}: {len(batch_rows)} sample | {elapsed:.1f}s | ETA: {format_eta(eta_seconds)}")
        save_checkpoint(pipeline_name, start + BATCH_SIZE)
       

    if pipeline_dfs:
        all_dfs[pipeline_name] = pd.concat(pipeline_dfs, ignore_index=True)
        print(f"\n  Hoàn thành {pipeline_name}: {len(all_dfs[pipeline_name])} sample.")

   

clear_checkpoint()

if not all_dfs:
    print("\nKhông có pipeline nào thành công.")
    sys.exit(1)

#  Tổng hợp kết quả
col_names = list(all_dfs.keys())

summary = {}

for name, df in all_dfs.items():
    summary[name] = {}

    for k in METRIC_KEYS:
        if k in df.columns:
            avg_value = float(df[k].mean())
            summary[name][k] = round(avg_value, 4)

print("\n" + "==============================================" )
print("KẾT QUẢ TỔNG:")
print("=" * 70)
print(f"{'Metric':<25}" + "".join(f"{n:>15}" for n in col_names))
print("------------------------------------------------------------")
for metric in METRIC_KEYS:
    row = f"{metric:<25}"
    for name in col_names:
        val = summary.get(name, {}).get(metric, float("nan"))
        row += f"{val:>15.4f}"
    print(row)
print("============================================================" )

print("\nBREAKDOWN THEO LOẠI CÂU HỎI:")
for name in col_names:
    print(f"\n  [{name}]")
    print(all_dfs[name].groupby("question_type")[METRIC_KEYS].mean().round(3).to_string())

output = {
    "judge_model": JUDGE_MODEL,
    "embedding_model": EMBEDDING_MODEL,
    "summary":  summary,
    "breakdown_by_type": {
        name: all_dfs[name].groupby("question_type")[METRIC_KEYS].mean().round(4).to_dict()
        for name in col_names
    },
}

os.makedirs(os.path.dirname(SUMMARY_JSON), exist_ok=True)
with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

combined_df = pd.concat(list(all_dfs.values()), ignore_index=True)
combined_df.to_csv(DETAIL_CSV, index=False, encoding="utf-8-sig")

print(f"\nĐã lưu: {SUMMARY_JSON} + {DETAIL_CSV}")
print(f"(File tạm từng batch: {PARTIAL_CSV})")
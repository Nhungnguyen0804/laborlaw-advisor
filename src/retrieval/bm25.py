import json
import numpy as np
from pathlib import Path
from rank_bm25 import BM25Okapi
from src.utils.paths import LABORLAW_CHUNKS_JSON
from underthesea import word_tokenize

#bm25 -> top chunk lien quan
CHUNKS_FILE = LABORLAW_CHUNKS_JSON

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

chunks = data["chunks"]


# build bm25 

tokenized = []

for chunk in chunks:
    text = chunk["content"].lower()
    tokens = word_tokenize(text)
    tokenized.append(tokens)

bm25 = BM25Okapi(tokenized)

def bm25_search(question, top_k=10): 
    tokenized_query = word_tokenize(question.lower())
    scores = bm25.get_scores(tokenized_query)

    top_indexs = np.argsort(scores)[-top_k:][::-1]

    results = []

    for i,idx in enumerate(top_indexs, 1):
        chunk = chunks[idx]

        results.append({
            "chunk_id": chunk.get("chunk_id"),
            "rank": i,    
            "score": float(scores[idx]),
            "content": chunk["content"],
            "article": chunk["metadata"]["article_num"],
            "chapter": chunk["metadata"]["chapter_num"]
        })

    return results



# run 

# question = "người lao động được nghỉ phép bao nhiêu ngày"
# print(question)
# results = bm25_search(question)

# for res in results:
#     print(res)


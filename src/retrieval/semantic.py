import json
import numpy as np
from sentence_transformers import SentenceTransformer

from src.utils.paths import EMB_JSON

# semantic -> top chunk liên quan
CHUNKS_FILE = EMB_JSON
MODEL_NAME = "BAAI/bge-m3"


# load chunks
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    chunks = json.load(f)


# load embeddings
embeddings = []

for chunk in chunks:
    embeddings.append(chunk["embedding"])

embeddings = np.array(embeddings)

# load model
model = SentenceTransformer(MODEL_NAME)


def semantic_search(question, top_k=10):

    # embed query
    query_embedding = model.encode(
        question,
        normalize_embeddings=True
    )

    # cosine similarity
    scores = np.dot(embeddings, query_embedding)

    # lấy top_k score cao nhất
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

# results = semantic_search(question)

# print(results)
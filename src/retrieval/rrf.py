from collections import defaultdict
def get_score(item):
    return item[1]

def rrf(rankings, k=60):
    scores = defaultdict(float)
    
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            chunk_id = doc["chunk_id"]
            scores[chunk_id] += 1 / (k + rank + 1)  # rank +1 vì bắt đầu từ 1
    
    return dict(scores)

def rrf_fusion(bm25_results, semantic_results):
    if not bm25_results and not semantic_results:
        print("kết quả bm25 và semantic đang rỗng")
        return []
    
    if not bm25_results:
        print("bm25 results rỗng!")
    
    if not semantic_results:
        print("semantic results rỗng!")

    doc_map = {}
    
    for doc in bm25_results:
        chunk_id = doc["chunk_id"]
        if chunk_id not in doc_map:
            doc_map[chunk_id] = doc.copy()
            if "score" in doc:
                doc_map[chunk_id]["bm25_score"] = doc["score"]
        else:
            if "score" in doc:
                doc_map[chunk_id]["bm25_score"] = doc["score"]
    
    for doc in semantic_results:
        chunk_id = doc["chunk_id"]
        if chunk_id not in doc_map:
            doc_map[chunk_id] = doc.copy()
            if "score" in doc:
                doc_map[chunk_id]["semantic_score"] = doc["score"]
        else:
            if "score" in doc:
                doc_map[chunk_id]["semantic_score"] = doc["score"]
    
    rankings = [bm25_results, semantic_results]
    
    scores = rrf(rankings)
    
    # sort doc theo score giảm dần 
    reranked = sorted(scores.items(), key=get_score, reverse=True)
    
    final_results = []
    for chunk_id, rrf_score in reranked:
        doc = doc_map[chunk_id].copy()
        doc["rrf_score"] = rrf_score
        final_results.append(doc)
    

    # lấy top 10 rff 
    len_res = len(final_results)
    return final_results[:10] # lấy top 10 first 



from src.retrieval.bm25 import bm25_search
from src.retrieval.semantic import semantic_search

bm25_topk = 50
semantic_topk = 50


question = "người lao động được nghỉ phép bao nhiêu ngày"
bm25_results = bm25_search(question)
semantic_results = semantic_search(question)
rrf_results = rrf_fusion(bm25_results, semantic_results)


output_path = 'src/retrieval/rrf.txt'

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(question + '\n')
    
    for doc in rrf_results:
        line = f"chunk_id: {doc['chunk_id']}'\n'-->rrf_score: {doc['rrf_score']}\n -->content {doc['content']}\n"
        f.write(line)

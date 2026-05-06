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

def rrf_fusion(bm25_results, semantic_results,topk):
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
            # Xóa score và rank của bm25 ban đầu
            doc_map[chunk_id].pop("score", None)
            doc_map[chunk_id].pop("rank", None)
            if "score" in doc:
                doc_map[chunk_id]["bm25_score"] = doc["score"]
           
        else:
            if "score" in doc:
                doc_map[chunk_id]["bm25_score"] = doc["score"]
              
    
    for doc in semantic_results:
        chunk_id = doc["chunk_id"]
        if chunk_id not in doc_map:
            doc_map[chunk_id] = doc.copy()
            # Xóa score và rank của sematic ban dau
            doc_map[chunk_id].pop("score", None)
            doc_map[chunk_id].pop("rank", None)
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
    return final_results[:topk] # lấy top 10 first 


def run_rrf():
    print('run rrf!')
    from src.retrieval.bm25 import bm25_search
    from src.retrieval.semantic import semantic_search

    bm25_topk = 50
    semantic_topk = 50


    question = "người lao động được nghỉ phép bao nhiêu ngày"
    bm25_results = bm25_search(question,bm25_topk)
    semantic_results = semantic_search(question,semantic_topk)
    rrf_results = rrf_fusion(bm25_results, semantic_results)


    output_path = 'src/retrieval/rrf.txt'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(question + '\n')
        
        for doc in rrf_results:
            line = f"chunk_id: {doc['chunk_id']}'\n'-->rrf_score: {doc['rrf_score']}\n -->content {doc['content']}\n"
            f.write(line)

# run_rrf()

def rrf_with_ner():
    # rrf --> top k --> ner ---> ent 
    from src.retrieval.bm25 import bm25_search
    from src.retrieval.semantic import semantic_search
    from src.ner.ner_re import process_chunk
    from src.utils.file_utils import save_json

    bm25_topk = 50
    semantic_topk = 50
    rrf_topk = 10

    question = "người lao động được nghỉ phép bao nhiêu ngày"
    bm25_results = bm25_search(question,bm25_topk)
    semantic_results = semantic_search(question,semantic_topk)
    rrf_results = rrf_fusion(bm25_results, semantic_results,rrf_topk) 

    # NER trên từng chunk
    ner_results = []
    for doc in rrf_results:
        # dict theo format process_chunk()
        chunk = {
            'chunk_id': doc['chunk_id'],
            'chunk_type': doc.get('chunk_type', 'unknown'),
            'content': doc['content']
        }
        
        # Xử lý NER + RE
        ner_result = process_chunk(chunk)
        ner_result['rrf_score'] = doc['rrf_score']  
        ner_results.append(ner_result)


    #save results
    output = {
        'question': question,
        'total_results': len(ner_results),
        'results': ner_results
    }

    save_json(output, 'src/retrieval/rrf_ner.json')

    print(question)

    for r in rrf_results:
        print(r)
    return ner_results


rrf_with_ner()
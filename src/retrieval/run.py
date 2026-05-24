from src.retrieval.bm25 import bm25_search
from src.retrieval.semantic import semantic_search
from src.retrieval.rrf import rrf_fusion
from src.utils.file_utils import save_json,load_json
from src.neo4j.query_neo4j import get_chunk_context_from_graph,query_find_rel_in_ents
from src.retrieval.graph import run_retrieval_graph
bm25_topk = 50
semantic_topk = 50
rrf_topk = 10

def get_labels(entity_list):
    labels = set()

    if not entity_list:
        return labels

    first_item = entity_list[0]

    # Nếu list là string
    if isinstance(first_item, str):
        for item in entity_list:
            label = item.lower().strip()
            labels.add(label)

    # Nếu list là dict
    elif isinstance(first_item, dict):
        for item in entity_list:
            label = (
                item.get("label")
                or item.get("node_id")
                or ""
            )

            label = label.lower().strip()

            if label != "":
                labels.add(label)

    return labels


def calculate_entity_match_score(query_labels, chunk_labels):
    if len(query_labels) == 0:
        return 0
    matched_count = 0
    for label in query_labels:
        if label in chunk_labels:
            matched_count += 1
    return matched_count / len(query_labels)

def sort_by_rrf_score(item):
    return item["rrf_score"]

def get_relations_in_chunk(driver, chunk_data):
    # Lấy list các entity id từ data đầu vào
    for chunk in chunk_data:
        entity_ids = [e["id"] for e in chunk["graph"]["entities"]]
        triples = query_find_rel_in_ents(driver,entity_ids)
        chunk["graph"]["rels"] = triples
    return chunk_data


def add_prefix_blldvn(chunks):
    prefix="Bộ luật Lao động Việt Nam 2019 "
    for chunk in chunks:
        chunk["content_with_context"] = prefix + chunk["content_with_context"]
    return chunks

def run_retrieval(driver,question,query_entities):
    
    bm25_results = bm25_search(question,bm25_topk)
    semantic_results = semantic_search(question,semantic_topk)
    rrf_results = rrf_fusion(bm25_results, semantic_results,rrf_topk) 
    query_labels = get_labels(query_entities)

    #enrich vs graph context (chunk với ents)
    chunk_with_ents = []
    for doc in rrf_results:
        graph_context = get_chunk_context_from_graph(driver,doc['chunk_id'])
        # labels từ entities của chunk
        chunk_entities = graph_context.get("entities", [])

        chunk_labels = get_labels(chunk_entities)
        # Entity xuất hiện cả trong question và chunk
        # question co 4 thuc the, chunk match 2 => score = 2/4
        entity_match_score = calculate_entity_match_score(query_labels,chunk_labels)
        
        chunk_with_ents.append({
            "chunk_id": doc["chunk_id"],
            "chunk_type": graph_context.get("chunk_type", []),
            "content_with_context": graph_context.get("content_with_context", []),
            # "content": doc["content"],
            "rrf_score": doc["rrf_score"]+ 0.3 * entity_match_score,

            "graph": {
                "article_id": graph_context.get("article_id"),
                "article_title": graph_context.get("article_title"),
                "clause_id": graph_context.get("clause_id"),
                "entities": chunk_entities,
            }
        })
        
    # Sort lại sau khi đã boost
    chunk_with_ents.sort(key=sort_by_rrf_score, reverse=True)
    save_json(chunk_with_ents,'test/chunk_with_ents.json')

    chunk_with_ents_rels = get_relations_in_chunk(driver,chunk_with_ents)
    save_json(chunk_with_ents_rels,'test/chunk_with_ents_rels.json')
    return add_prefix_blldvn(chunk_with_ents_rels)
    



def run_retrieval_rag(driver,question):  
    semantic_results = semantic_search(question,semantic_topk)
    #enrich vs graph context (chunk với ents)
    chunks_res = []
    for doc in semantic_results:
        chunks_res.append({
            "chunk_id": doc["chunk_id"],
         
            "score": doc["score"],
            "content": doc["content"],
            "article": doc["article"],
            "chapter": doc["chapter"],
        })
        
    return chunks_res
    

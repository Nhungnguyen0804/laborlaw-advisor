from src.retrieval.bm25 import bm25_search
from src.retrieval.semantic import semantic_search
from src.retrieval.rrf import rrf_fusion
from src.utils.file_utils import save_json
from src.ner_re.extract_entity import extract_entities_from_question
from src.neo4j.connection import init_driver, close_driver
from src.neo4j.test_connect import test_connection
from src.neo4j.query_neo4j import get_chunk_context_from_graph
bm25_topk = 50
semantic_topk = 50
rrf_topk = 10

question = "người lao động được nghỉ phép bao nhiêu ngày"


from src.ner_re.patterns import PATTERNS
import re 
COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]

def run_retrieval(driver,question,COMPILED):
    bm25_results = bm25_search(question,bm25_topk)
    semantic_results = semantic_search(question,semantic_topk)
    rrf_results = rrf_fusion(bm25_results, semantic_results,rrf_topk) 
    query_entities = extract_entities_from_question(question,COMPILED)
    save_json(query_entities,'src/retrieval/test/query_entities.json')

    #enrich vs graph context (chunk với ents)
    chunk_with_ents = []
    for doc in rrf_results:
        graph_context = get_chunk_context_from_graph(driver,doc['chunk_id'])
        
        chunk_with_ents.append({
            "chunk_id": doc["chunk_id"],
            "content": doc["content"],
            "rrf_score": doc["rrf_score"],

            "graph": {
                "article_title": graph_context["article_title"] if graph_context else None,
                "entities": graph_context["entities"] if graph_context else []
            }
        })
    save_json(chunk_with_ents,'src/retrieval/test/chunk_with_ents.json')
    

driver = init_driver()
try:
    test_connection()
    run_retrieval(driver,question,COMPILED)
finally:
    close_driver()

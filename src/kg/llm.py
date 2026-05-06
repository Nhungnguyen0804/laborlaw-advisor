import json
import os
import sys
from src.utils.paths import LABORLAW_CHUNKS_JSON
log_path = os.path.join(os.path.dirname(__file__), "llm.txt")
log_file = open(log_path, "w", encoding="utf-8")
sys.stdout = log_file


def enrich_graph_context(search_results, chunks_json_path):

    import json
    
    # Load chunks
    with open(chunks_json_path, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)
    
    if isinstance(search_results, dict):
        if 'results' in search_results:
            results_list = search_results['results']
        elif 'chunks' in search_results:
            results_list = search_results['chunks']
        else:
            print("search_results dict phải có key 'results' hoặc 'chunks'")
    elif isinstance(search_results, list):
        results_list = search_results
    else:
        print(f"search_results phải là dict hoặc list, nhận được {type(search_results)}")
    
    # Tạo index: chunk_id -> metadata
    chunk_index = {}
    if isinstance(chunks_data, dict) and 'chunks' in chunks_data:
        chunk_index = {
            chunk['chunk_id']: chunk 
            for chunk in chunks_data['chunks']
        }
    elif isinstance(chunks_data, list):
        chunk_index = {
            chunk['chunk_id']: chunk 
            for chunk in chunks_data
        }
    else:
        print("chunks_data format không hợp lệ")
    
    # Thu thập tất cả entities và relations từ search results
    all_entities = {}  # text -> entity info
    all_relations = []
    
    for result in results_list:
        # Lấy chunk_id từ result 
        chunk_id = result.get('chunk_id') or result.get('id')
        
        if not chunk_id:
            continue
            
        # Collect entities from all sentences
        sentences = result.get('sentences', [])
        
        for sentence in sentences:
            # Xử lý entities
            for entity in sentence.get('entities', []):
                entity_text = entity['text']
                entity_type = entity['entity_type']
                
                if entity_text not in all_entities:
                    all_entities[entity_text] = {
                        'text': entity_text,
                        'entity_type': entity_type,
                        'chunk_ids': set()
                    }
                all_entities[entity_text]['chunk_ids'].add(chunk_id)
            
            # Xử lý relations
            for relation in sentence.get('relations', []):
                all_relations.append({
                    'source': relation.get('subject', ''),
                    'source_type': relation.get('subject_type', ''),
                    'relation_type': relation.get('relation_type', ''),
                    'target': relation.get('object', ''),
                    'target_type': relation.get('object_type', ''),
                    'predicate': relation.get('predicate', ''),
                    'confidence': relation.get('confidence', 0.0),
                    'chunk_id': chunk_id
                })
    
    # Tạo enriched graph structure
    enriched_graph = {
        'metadata': {
            'law_info': chunks_data.get('metadata', {}) if isinstance(chunks_data, dict) else {},
            'total_entities': len(all_entities),
            'total_relations': len(all_relations),
            'total_chunks_processed': len(results_list),
            'method': 'search_results_direct',
            'source': 'NER extraction from search results'
        },
        'nodes_with_context': [],
        'relationships_with_context': []
    }
    
    # Enrich nodes với legal contexts
    for entity_text, entity_info in all_entities.items():
        contexts = []
        
        for chunk_id in entity_info['chunk_ids']:
            if chunk_id in chunk_index:
                chunk = chunk_index[chunk_id]
                contexts.append({
                    'chunk_id': chunk_id,
                    'article': chunk.get('metadata', {}).get('article_num'),
                    'article_title': chunk.get('metadata', {}).get('article_title'),
                    'chapter': chunk.get('metadata', {}).get('chapter_num'),
                    'chapter_title': chunk.get('metadata', {}).get('chapter_title'),
                    'content': chunk.get('content_with_context', chunk.get('content', ''))
                })
        
        enriched_graph['nodes_with_context'].append({
            'text': entity_text,
            'entity_type': entity_info['entity_type'],
            'occurrence_count': len(entity_info['chunk_ids']),
            'legal_contexts': contexts
        })
    
    # Enrich relationships với full context
    for rel in all_relations:
        chunk_id = rel['chunk_id']
        context = None
        
        if chunk_id in chunk_index:
            chunk = chunk_index[chunk_id]
            context = {
                'chunk_id': chunk_id,
                'article': chunk.get('metadata', {}).get('article_num'),
                'article_title': chunk.get('metadata', {}).get('article_title'),
                'chapter': chunk.get('metadata', {}).get('chapter_num'),
                'chapter_title': chunk.get('metadata', {}).get('chapter_title'),
                'full_text': chunk.get('content_with_context', chunk.get('content', ''))
            }
        
        enriched_graph['relationships_with_context'].append({
            'source': rel['source'],
            'source_type': rel['source_type'],
            'relation': rel['relation_type'],
            'predicate': rel['predicate'],
            'target': rel['target'],
            'target_type': rel['target_type'],
            'confidence': rel['confidence'],
            'legal_context': context
        })
    
    return enriched_graph


def format_graph_to_jsonl(enriched_graph, output_path):
    """
    Format enriched graph thành JSONL
    Mỗi dòng là 1 relationship với đầy đủ context
    """
    count = 0
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for rel in enriched_graph['relationships_with_context']:
            # Tạo document cho vector search
            doc = {
                'relationship': {
                    'source': rel['source'],
                    'source_type': rel['source_type'],
                    'relation': rel['relation'],
                    'predicate': rel.get('predicate', ''),
                    'target': rel['target'],
                    'target_type': rel['target_type'],
                    'confidence': rel.get('confidence', 0.0)
                },
                'legal_context': rel.get('legal_context'),
                'natural_language': f"{rel['source']} ({rel['source_type']}) {rel.get('predicate', rel['relation'])} {rel['target']} ({rel['target_type']})"
            }
            
            f.write(json.dumps(doc, ensure_ascii=False) + '\n')
            count += 1
    
    return count


# test 
import sys
import os
import json
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

from src.neo4j.connection import get_driver
from src.kg.expand import get_seed_relationships, expand_graph, extract_seeds, deduplicate_seeds


driver = get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

try:
    # Load NER results
    ner_res_path = 'src/retrieval/rrf_ner.json'
    with open(ner_res_path, 'r', encoding='utf-8') as f:
        ner_results = json.load(f)['results']
    
    # Extract seeds
    seeds = extract_seeds(ner_results)
    print(f"Extracted seeds: {len(seeds)}")
    
    seeds = deduplicate_seeds(seeds)
    print(f"sau dedup: {len(seeds)}")
    
    # Get graphs
    print('extract graph')
    
    # bfs_graph = expand_graph(driver, ner_results, method='bfs', max_depth=2, max_nodes=30)
    # dfs_graph = expand_graph(driver, ner_results, method='dfs', max_depth=2, max_nodes=30)
    
    # print(f"\nBFS =>Nodes: {bfs_graph['node_count']}, Rels: {bfs_graph['relationship_count']}")
    # print(f"DFS =>Nodes: {dfs_graph['node_count']}, Rels: {dfs_graph['relationship_count']}")
    
    # enrich , export json
    
    enriched_graph = enrich_graph_context(ner_results, LABORLAW_CHUNKS_JSON)
    jsonl_count = format_graph_to_jsonl(enriched_graph, 'src/kg/enriched_graph.jsonl')
    with open('src/kg/enriched_graph.json', 'w', encoding='utf-8') as f:
        json.dump(enriched_graph, f, ensure_ascii=False, indent=2)

finally:
    sys.stdout.flush()
    log_file.close()
    sys.stdout = sys.__stdout__
    print(f"✅ Log saved to {log_path}")
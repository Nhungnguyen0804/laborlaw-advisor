
def get_node_ids_for_seeds(session, seeds):
    query = """
    UNWIND $seeds AS seed
    MATCH (n)
    WHERE n.text = seed.text 
      AND seed.entity_type IN labels(n)
    WITH seed, n
    ORDER BY coalesce(n.node_frequency, 0) DESC
    WITH seed, collect(n)[0] AS n
    WHERE n IS NOT NULL
    RETURN 
        elementId(n) AS node_id,
        n.text AS text,
        labels(n) AS node_types  
    
    """
    
    result = session.run(query, seeds=seeds)
    
    seed_nodes = []
    for record in result:
        seed_nodes.append({
            'node_id': record['node_id'],
            'text': record['text'],
            'entity_type': record['node_types'][0] if record['node_types'] else 'Unknown'  
        })
    
    return seed_nodes



def build_seed_connections_query():
    return """
    UNWIND $seeds AS seed1
    UNWIND $seeds AS seed2
    WITH seed1, seed2
    WHERE seed1.node_id < seed2.node_id
    
    MATCH (n1), (n2)
    WHERE elementId(n1) = seed1.node_id 
      AND elementId(n2) = seed2.node_id
    
    MATCH (n1)-[r]-(n2)
    RETURN 
        elementId(n1) AS source_id,
        n1.text AS source,
        labels(n1) AS source_node_types,  
        type(r) AS relation_type,
        elementId(n2) AS target_id,
        n2.text AS target,
        labels(n2) AS target_node_types,  
        properties(r) AS rel_props
    """


def get_seed_connections(session, seeds):
    query = build_seed_connections_query()
    result = session.run(query, seeds=seeds)
    
    relationships = []
    for record in result:
        relationships.append({
            'source': record['source'],
            'source_type': record['source_node_types'][0] if record['source_node_types'] else 'Unknown',  
            'relation_type': record['relation_type'],
            'target': record['target'],
            'target_type': record['target_node_types'][0] if record['target_node_types'] else 'Unknown',  
            'properties': dict(record['rel_props']) if record['rel_props'] else {}
        })
    
    return relationships


def extract_seeds(ner_results):
    # trich xuat ent từ ner result từ question làm seed 
    seeds = []
    for doc in ner_results:
        for sentence in doc.get('sentences', []):
            for entity in sentence.get('entities', []):
                seeds.append({
                    'text': entity['text'],
                    'entity_type': entity['entity_type']
                })
    return seeds


def deduplicate_seeds(seeds):
    unique = {}
    for seed in seeds:
        key = (seed['text'], seed['entity_type']) # tuple key
        unique[key] = seed
    return list(unique.values())


# merge result 
def merge_nodes(all_nodes, new_nodes):
    for node in new_nodes:
        key = (node['text'], node['entity_type'])
        if key not in all_nodes:
            all_nodes[key] = node



def deduplicate_rels(relationships):
    unique = {}
    
    for rel in relationships:
        key = (
            rel['source'],
            rel['relation_type'],
            rel['target']
        )
        
        if key not in unique:
            unique[key] = rel
    
    return list(unique.values())

from src.kg.bfs import expand_bfs
from src.kg.dfs import expand_dfs 


def expand_graph(driver, ner_results, method='bfs', max_depth=2, max_nodes=50):
    seeds = extract_seeds(ner_results)
    seeds = deduplicate_seeds(seeds)
    
    all_nodes = {}
    all_rels = {}  
    
    with driver.session(database="test") as session:
        
        seed_nodes = get_node_ids_for_seeds(session, seeds)
        
        print(f"Found {len(seed_nodes)}/{len(seeds)} seeds in Neo4j")
        
        for seed in seed_nodes:  
            node_id = seed['node_id'] 
            
            if method == 'bfs':
                result = expand_bfs(session, node_id, 
                                   max_depth, max_nodes)
            elif method == 'dfs':
                result = expand_dfs(session, node_id, 
                                   max_depth, max_nodes)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            # Merge nodes
            for node in result['nodes']:
                key = (node['text'], node['entity_type'])
                if key not in all_nodes:
                    all_nodes[key] = node
            
            # Merge rels
            for rel in result['relationships']:
                key = (rel['source'], rel['relation_type'], rel['target'])
                if key not in all_rels:
                    all_rels[key] = rel
    
    return {
        'seed_count': len(seed_nodes),
        'node_count': len(all_nodes),
        'relationship_count': len(all_rels),
        'method': method,
        'nodes': list(all_nodes.values()),
        'relationships': list(all_rels.values())
    }


def get_seed_relationships(driver, ner_results):
    seeds = extract_seeds(ner_results)
    seeds = deduplicate_seeds(seeds)
    
    with driver.session(database="test") as session:
        # Map seeds -> node_id
        seed_nodes = get_node_ids_for_seeds(session, seeds)
        print(f"Step 3 - Found in Neo4j: {len(seed_nodes)}/{len(seeds)}")
        
        # Lấy relationships giữa các seeds
        rels = get_seed_connections(session, seed_nodes)  
    
    return {
        'seed_count': len(seed_nodes),
        'seeds': seed_nodes,
        'relationships': rels
    }


# test
# import sys
# import os

# log_path = os.path.join(os.path.dirname(__file__), "expand.txt")
# sys.stdout = open(log_path, "w", encoding="utf-8")
# import os
# from dotenv import load_dotenv
# load_dotenv()
# NEO4J_URI = os.getenv("NEO4J_URI")
# NEO4J_USER = os.getenv("NEO4J_USER")
# NEO4J_PASS = os.getenv("NEO4J_PASS")



# from src.neo4j.connection import get_driver
# driver = get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

# import json
# ner_res_path = 'src/retrieval/rrf_ner.json'
# # Load NER results
# with open(ner_res_path, 'r', encoding='utf-8') as f:
#     ner_results = json.load(f)['results']


# graph = get_seed_relationships(driver, ner_results)
# bfs_graph = expand_graph(driver, ner_results, method='bfs', max_depth=2, max_nodes=30)
# dfs_graph = expand_graph(driver, ner_results, method='dfs', max_depth=2, max_nodes=30)

# # print(ner_results) ok
# seeds = extract_seeds(ner_results)
# print(seeds)
# print(f"Step 1 - Extracted seeds: {len(seeds)}")

# seeds = deduplicate_seeds(seeds)
# print(seeds)
# print(f"Step 2 - After deduplication: {len(seeds)}")

# print("extract seed:")
# for seed in seeds[:5]:  # In 5 seed đầu
#     print(f"Text: '{seed['text']}', Type: '{seed['entity_type']}'")

# # check label trong neo4j
# with driver.session(database="test") as session:
#     check_query = """
#     MATCH (n)
#     RETURN DISTINCT labels(n) AS labels, n.text AS text
#     LIMIT 10
#     """
#     result = session.run(check_query)
#     print("\nlabel trong neo4j:")
#     for record in result:
#         print(f"Labels: {record['labels']}, Text: '{record['text']}'")

# with driver.session(database="test") as session:
#     # Test xem có node nào không
#     test_query = """
#     MATCH (n)
#     RETURN count(n) AS total_nodes
#     """
#     result = session.run(test_query)
#     print(f"\nTotal nodes in Neo4j: {result.single()['total_nodes']}")
# print(graph)
# print(bfs_graph)
# print(dfs_graph)
# print("seed relationship")
# print(f"Seeds found: {graph['seed_count']}")
# print(f"Relationships: {len(graph['relationships'])}")
# print("\nSeeds:")
# for seed in graph['seeds']:
#     print(f"  - {seed['text']} ({seed['entity_type']})")
# print("\nRelationships:")
# for rel in graph['relationships']:
#     print(f"  {rel['source']} --[{rel['relation_type']}]--> {rel['target']}")

# print("\nbfs expand:")
# print(f"Seeds: {bfs_graph['seed_count']}")
# print(f"Nodes: {bfs_graph['node_count']}")
# print(f"Relationships: {bfs_graph['relationship_count']}")
# print(f"Method: {bfs_graph['method']}")

# print("\ndfs expand:")
# print(f"Seeds: {dfs_graph['seed_count']}")
# print(f"Nodes: {dfs_graph['node_count']}")
# print(f"Relationships: {dfs_graph['relationship_count']}")
# print(f"Method: {dfs_graph['method']}")


# driver.close()
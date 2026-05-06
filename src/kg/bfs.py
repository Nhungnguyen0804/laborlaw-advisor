# bfs rong 
# lay all lv 1

def build_bfs_query():
    return """
    MATCH (seed)
    WHERE elementId(seed) = $node_id
    CALL apoc.path.subgraphAll(seed, {
        maxLevel: $max_depth,
        limit: $max_nodes
    })
    YIELD nodes, relationships
    RETURN nodes, relationships
    """
    # return """
    # MATCH (seed {node_id: $node_id})
    # CALL apoc.path.subgraphAll(seed, {
    #     maxLevel: $max_depth,
    #     limit: $max_nodes
    # })
    # YIELD nodes, relationships
    # RETURN nodes, relationships
    # """


def parse_bfs_result(record):
    if not record:
        return {"nodes": [], "relationships": []}
    
    nodes = [
        {
            "text": n["text"],
            "entity_type": n["entity_type"],
            "id": n.element_id
        }
        for n in record["nodes"]
    ]
    
    relationships = [
        {
            "source": r.start_node["text"],
            "target": r.end_node["text"],
            "relation_type": r.type,
            "properties": dict(r)
        }
        for r in record["relationships"]
    ]
    
    return {"nodes": nodes, "relationships": relationships}


def expand_bfs(session, node_id, max_depth=2, max_nodes=50):
    # build query 
    query = build_bfs_query()

    params = {
        "node_id": node_id,
        "max_depth": max_depth,
        "max_nodes": max_nodes
    }
    # run query  
    result = session.run(query, **params)

    records = list(result)

    record = records[0]

    return parse_bfs_result(record)

#test
# import os
# from dotenv import load_dotenv
# from src.neo4j.connection import get_driver

# load_dotenv()

# NEO4J_URI = os.getenv("NEO4J_URI")
# NEO4J_USER = os.getenv("NEO4J_USER")
# NEO4J_PASS = os.getenv("NEO4J_PASS")

# driver = get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

# with driver.session(database="test") as session:
#     apoc_check = session.run("RETURN apoc.version() AS version")
#     try:
#         version = apoc_check.single()
#         print(f"APOC version: {version['version']}")
#     except:
#         print("APOC chưa được cài đặt!")
#         exit(1)
    
#     # Lấy node có relationships
#     result = session.run("""
#     MATCH (n)-[r]-()
#     RETURN elementId(n) AS node_id, n.text AS text, count(r) AS rel_count
#     ORDER BY rel_count DESC
#     LIMIT 1
#     """)
    
#     result = list(result)

#     first_node = result[0]

    
#     if first_node:
#         print(f"BFS from node: {first_node['text']}")
#         print(f"---> Node ID: {first_node['node_id']}")
#         print(f"---> Relationships: {first_node['rel_count']}")
        
#         # expand_bfs
#         subgraph = expand_bfs(session, first_node['node_id'], max_depth=2, max_nodes=20)
        
#         print(f"\nNodes found: {len(subgraph['nodes'])}")
#         print(f"Relationships found: {len(subgraph['relationships'])}")
        
#         # In ra nodes
#         for node in subgraph['nodes'][:5]:
#             print(f"  ---> {node['text']} ({node['entity_type']})")
        
#         # In ra relationships
#         if subgraph['relationships']:
#             print("\nRelationships:")
#             for rel in subgraph['relationships'][:5]:
#                 print(f"  {rel['source']} --[{rel['relation_type']}]--> {rel['target']}")
#     else:
#         print("ko tìm thấy node nào có relationships")

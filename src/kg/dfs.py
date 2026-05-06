def build_neighbors_query():
    # lấy neighbor của 1 node 

    return """
    MATCH (seed)
    WHERE elementId(seed) = $node_id

    MATCH (seed)-[r]->(neighbor)

    RETURN
        elementId(neighbor) AS node_id,
        neighbor.text AS text,
        labels(neighbor) AS labels,
        type(r) AS rel_type,
        properties(r) AS rel_props

    LIMIT $limit
    """

def get_neighbors(session, node_id, limit=50):
    # get list neighbor của 1 node 
    query = build_neighbors_query()

    result = session.run(
        query,
        node_id=node_id,
        limit=limit
    )

    neighbors = []

    for record in result:
        neighbors.append({
            'node_id': record['node_id'],
            'text': record['text'],
            'labels': record['labels'],
            'rel_type': record['rel_type'],
            'rel_props': dict(record['rel_props']) if record['rel_props'] else {}
        })

    return neighbors

def dfs(session, 
        max_depth,
        max_nodes, 
        current_node_id,
        node_text,
        node_type,
        depth,
        visited_nodes,nodes_list,relationships ):

    # dk end
    if depth > max_depth:
        return
    if len(visited_nodes) >= max_nodes:
        return
        
    if current_node_id in visited_nodes:
        return 
        
    # Đánh dấu đã thăm
    visited_nodes.add(current_node_id)
    nodes_list.append({
        'node_id': current_node_id,
        'text': node_text,
        'entity_type': node_type,
        'depth': depth
    })
        
    # Lấy các node kề (neighbors)
    neighbors = get_neighbors(session, current_node_id, max_nodes - len(visited_nodes))
        
    # Duyệt từng neighbor
    for neighbor in neighbors:
        # Lưu relationship
        relationships.append({
            'source': node_text,
            'source_id': current_node_id,
            'target': neighbor['text'],
            'target_id': neighbor['node_id'],
            'relation_type': neighbor['rel_type'],
            'properties': neighbor['rel_props']
        })
            
        # đệ quy vs dfs vs neighbor
        neighbor_type = neighbor['labels'][0] if neighbor['labels'] else 'Unknown'
        dfs(session, 
            max_depth,
            max_nodes, 
            neighbor['node_id'],
            neighbor['text'],
            neighbor_type,
            depth + 1,
            visited_nodes,nodes_list,relationships
        )
      

def expand_dfs(session, node_id, max_depth=2, max_nodes=50):
    visited_nodes = set()
    nodes_list = []
    relationships = []
    # Lấy thông tin node gốc
    query = """
    MATCH (n)
    WHERE elementId(n) = $node_id
    RETURN n.text AS text, labels(n) AS labels
    """
    result = session.run(query, node_id=node_id)
    result = list(result)
    record = result[0]
    if not record:
        print(f"ko tìm thấy node với ID: {node_id}")
        return {'nodes': [], 'relationships': []}
    
    start_text = record['text']
    start_labels = record['labels']
    start_type = start_labels[0] if start_labels else 'Unknown'
    dfs(session,
        max_depth,
        max_nodes,
        node_id, 
        start_text,
        start_type,
        0, #depth
        visited_nodes,nodes_list,relationships
        )

    return {
        'nodes': nodes_list,
        'relationships': relationships
    }

#TEST
# import os
# from dotenv import load_dotenv
# from src.neo4j.connection import get_driver

# load_dotenv()

# NEO4J_URI = os.getenv("NEO4J_URI")
# NEO4J_USER = os.getenv("NEO4J_USER")
# NEO4J_PASS = os.getenv("NEO4J_PASS")

# driver = get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

# with driver.session(database="test") as session:
#     # Check APOC
#     apoc_check = session.run("RETURN apoc.version() AS version")
#     try:
#         version = apoc_check.single()
#         print(f"APOC version: {version['version']}")
#     except:
#         print("APOC chưa cài đặt!")
#         exit(1)
    
#     # Lấy node có nhiều relationships nhất
#     result = session.run("""
#     MATCH (n)-[r]-()
#     RETURN elementId(n) AS node_id, 
#            n.text AS text, 
#            count(r) AS rel_count
#     ORDER BY rel_count DESC
#     LIMIT 1
#     """)
    
#     result = list(result)
#     first_node = result[0]
    
#     if first_node:

#         print(f"DFS from node: {first_node['text']}")
#         print(f"=> Node ID: {first_node['node_id']}")
#         print(f"=> Relationships: {first_node['rel_count']}")
        
#         # Chạy expand_dfs
#         subgraph = expand_dfs(
#             session, 
#             first_node['node_id'],  
#             max_depth=2, 
#             max_nodes=20
#         )

#         print(f"=> Nodes found: {len(subgraph['nodes'])}")
#         print(f"=> Relationships found: {len(subgraph['relationships'])}")
        
#         # In ra nodes theo depth
#         print(f"\nNodes (top 10):")
#         for node in subgraph['nodes'][:10]:
#             indent = "  " * node['depth']
#             print(f"{indent}--->{node['text']} ({node['entity_type']}) [depth={node['depth']}]")
        
#         # In ra relationships
#         if subgraph['relationships']:
#             print(f"\nRelationships (top 10):")
#             for rel in subgraph['relationships'][:10]:
#                 print(f"   {rel['source']} --[{rel['relation_type']}]--> {rel['target']}")
#     else:
#         print("ko tìm thấy node có relationships")

# driver.close()
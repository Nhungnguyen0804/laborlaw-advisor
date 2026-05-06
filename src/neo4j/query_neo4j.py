




def build_neighbors_query():
    #cypher query để lấy neighbors của 1 node
    return """
        MATCH (e:Entity {text: $text, entity_type: $type})-[r]-(neighbor:Entity)
        RETURN neighbor.text AS text, 
               neighbor.entity_type AS type,
               type(r) AS rel_type,
               e.text AS source_text,
               properties(r) AS rel_props
        LIMIT $limit
    """

def build_relationships_query():
    # cypher lay relationship 
    return """
        UNWIND $seeds AS seed
        MATCH (e1:Entity {text: seed.text, entity_type: seed.entity_type})
        MATCH (e2:Entity)
        WHERE e2.text IN [s.text | s IN $seeds WHERE s.entity_type = e2.entity_type]
            AND id(e1) < id(e2)
        MATCH (e1)-[r]-(e2)
        RETURN 
            e1.text AS source,
            e1.entity_type AS source_type,
            type(r) AS relation_type,
            e2.text AS target,
            e2.entity_type AS target_type,
            properties(r) AS rel_props
    """

# def run_bfs_query(session, params):
#     query = build_bfs_query()
#     return session.run(query, **params)

def run_neighbors_query(session, text,entity_type,limit):
    query = build_neighbors_query()
    return session.run(query, text=text, type=entity_type, limit=limit)

def run_relationships_query(session, seeds):
    query = build_relationships_query()
    return session.run(query, seeds=seeds)

# xu ly node 
def parse_nodes(nodes):
    return [
        {
            "text": n["text"],
            "entity_type": n["entity_type"],
            "id": n.id
        }
        for n in nodes
    ]


# Xử lý relationships
def parse_relationships(relationships):
    return [
        {
            "source": r.start_node["text"],
            "target": r.end_node["text"],
            "relation_type": r.type,
            "properties": dict(r)
        }
        for r in relationships
    ]



# def query_entity_neighbors_bfs(session, entity_text, entity_type, max_depth, max_nodes):
#     query = build_bfs_query()

#     params = {
#         "entity_text": entity_text,
#         "entity_type": entity_type,
#         "max_depth": max_depth,
#         "max_nodes": max_nodes
#     }

#     result = run_bfs_query(session, query, params)
#     record = result.single()

#     if not record:
#         return {"nodes": [], "relationships": []}

#     nodes = parse_nodes(record["nodes"])
#     relationships = parse_relationships(record["relationships"])

#     return {
#         "nodes": nodes,
#         "relationships": relationships
#     }


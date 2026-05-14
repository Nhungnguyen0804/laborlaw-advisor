def query_find_rel_in_ents(driver,entity_ids):
    # tìm quan hệ giữa các entities có id trong list
    query = """
    WITH $ids AS ids
    MATCH (e1)-[r]-(e2)
    WHERE e1.node_id IN ids AND e2.node_id IN ids
    RETURN 
        e1.label AS source,
        type(r) AS rel,
        e2.label AS target
    """
    with driver.session() as session:
        result = session.run(query, ids=entity_ids)
        
        # Tạo list triple
        triples = []
        for record in result:
            triples.append((
                record['source'],
                record['rel'],
                record['target']
            ))
        
        return triples
def get_chunk_context_from_graph(driver, chunk_id):
    query = """
    MATCH (c:CHUNK {chunk_id: $chunk_id})
    OPTIONAL MATCH (cl:CLAUSE {node_id: c.clause_id})-[:mentions]->(e1)
    OPTIONAL MATCH (a:ARTICLE {node_id: c.article_id})-[:mentions]->(e2)
    WITH c,
         collect(DISTINCT e1) + collect(DISTINCT e2) AS all_entities
    RETURN
        c.chunk_id AS chunk_id,
        c.chunk_type AS chunk_type,
        c.article_id AS article_id,
        c.article_title AS article_title,
        c.clause_id AS clause_id,
        c.content_with_context AS content_with_context,
        //coalesce(c.content_with_context, c.content) AS display_content,
        c.content AS raw_content,
        [e IN all_entities WHERE e IS NOT NULL | {
            label: e.label,
            type:  e.node_type,
            id:e.node_id,
            attributes: coalesce(e.attributes, {})
        }] AS entities
    """
    with driver.session() as session:
        result = session.run(query, chunk_id=chunk_id)
        rec = result.single()
        if rec is None:
            return None
        return dict(rec) 
    
    
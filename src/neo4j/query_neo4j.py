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
    
def query_structural_children(driver, parent_id, relation_type):
    """
    Query các node con của parent theo relation
    
    parent_id: 'ch1_d13'
    relation_type: 'HAS_CLAUSE'
    
    Returns: list of child nodes
    """

    query = f"""
MATCH (parent {{node_id: $parent_id}})-[r:{relation_type}]->(child)
RETURN
    child.node_id AS id,
    child.node_type AS type,
    child.label AS text,
    COALESCE(
        CASE child.node_type
            WHEN 'CHAPTER' THEN child.chapter_title
            WHEN 'ARTICLE' THEN child.article_title
            WHEN 'CLAUSE'  THEN child.clause_content
            WHEN 'POINT'   THEN child.point_content
        END,
        child.label
    ) AS content
ORDER BY
    CASE
        WHEN child.chapter_num IS NOT NULL THEN toInteger(child.chapter_num)
        WHEN child.article_num IS NOT NULL THEN toInteger(child.article_num)
        WHEN child.clause_num  IS NOT NULL THEN toInteger(child.clause_num)
        ELSE 0
    END,
    child.point_label
"""

    with driver.session() as session:
        result = session.run(
            query, 
            parent_id=parent_id,
            rel_type=relation_type
        )
        
        children = []
        for record in result:
            children.append({
                'id': record['id'],
                'type': record['type'],
                'text': record['text'],
                "content": record["content"]
            })
        
        return children
    

def query_point_node_direct(driver, node_id):
    query = """
    MATCH (n {node_id: $node_id})
    RETURN n.node_id as id, n.label as text, n.point_content as content, n.node_type as type
    """
    with driver.session() as session:
        result = session.run(query, node_id=node_id)
        record = result.single()
        if record:
            return [{
                'id': record['id'],
                'text': record['text'],
                'content': record['content'] if record['content'] else record['text'],
                'type': record['type']
            }]
        return None



def query_node_direct(driver, node_id, node_type=None):

    query = """
    MATCH (n {node_id: $node_id})
    RETURN
        n.node_id AS id,
        n.node_type AS type,
        n.label AS text,
        COALESCE(
            CASE n.node_type
                WHEN 'CHAPTER' THEN n.chapter_title
                WHEN 'ARTICLE' THEN n.article_title
                WHEN 'CLAUSE' THEN n.clause_content
                WHEN 'POINT' THEN n.point_content
            END,
            n.label
        ) AS content
    """

    with driver.session() as session:
        result = session.run(query, node_id=node_id)
        record = result.single()

        if record:
            resolved_type = node_type if node_type else record['type']
            return [{
                'id': record['id'],
                'type':resolved_type,
                'text': record['text'],
                'content': record['content'] if record['content'] else record['text'],
            }]

        return None

from tqdm import tqdm
import json

def create_vector_index(driver):
    with driver.session() as session:
        session.run("""
            CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
            FOR (c:CHUNK) REQUIRE c.chunk_id IS UNIQUE
        """)
        print("Constraint cho :CHUNK")
        
        try:
            session.run("""
                CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
                FOR (c:CHUNK)
                ON c.embedding
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 1536,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            print("Vector index cho embeddings")
        except Exception as e:
            print(f"lỗi: {e}")
        
def import_chunks_with_embeddings(driver, json_path, batch_size=100):
    # Import chunks với embeddings vào Neo4j
    with open(json_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    total = len(chunks)
    print(f"Importing {total} chunks với embeddings")
    
    query = """
    UNWIND $batch AS row
    MERGE (c:CHUNK {chunk_id: row.chunk_id})
    SET c.content  = row.content,
        c.content_with_context = row.content_with_context,
        c.label  = row.content_with_context,
        c.chunk_type = row.chunk_type,
        c.embedding    = row.embedding,
        c.token_estimate   = row.token_estimate,
        c.law_code    = row.metadata.law_code,
        c.law_name   = row.metadata.law_name,
        c.chapter_num  = row.metadata.chapter_num,
        c.chapter_title = row.metadata.chapter_title,
        c.section_id  = row.metadata.section_id,
        c.section_num  = row.metadata.section_num,
        c.section_title = row.metadata.section_title,
        c.article_id   = row.metadata.article_id,     
        c.article_num   = row.metadata.article_num,
        c.article_title  = row.metadata.article_title,
        c.clause_id   = row.metadata.clause_id,      
        c.clause_num   = row.metadata.clause_num
    RETURN count(c)
    """
    
    with driver.session() as session:
        for i in tqdm(range(0, total, batch_size), desc="Chunks"):
            batch = chunks[i:i+batch_size]
            session.run(query, batch=batch)
    
    print(f"Imported {total} chunks")

def link_chunks_to_graph(driver):
    with driver.session() as session:
        # CHUNK -> ARTICLE (qua article_num + law_code)
        query = """
            MATCH (c:CHUNK)
            WHERE c.article_id IS NOT NULL
            MATCH (a:ARTICLE)
            WHERE a.node_id = c.article_id
            MERGE (a)-[:has_chunk]->(c)
            RETURN count(*) AS links
        """
        result = session.run(query)
        print(f"ARTICLE --> CHUNK: {result.single()['links']}")

        # CHUNK -> CLAUSE (nếu chunk_type là clause)
        query = """
            MATCH (c:CHUNK)
            WHERE c.chunk_type = 'clause' AND c.clause_id IS NOT NULL
            MATCH (cl:CLAUSE)
            WHERE cl.node_id = c.clause_id
            MERGE (cl)-[:has_chunk]->(c)
            RETURN count(*) AS links
        """
        result = session.run(query)
        print(f"CLAUSE --> CHUNK: {result.single()['links']}")
       

def verify_embeddings(driver):
    # Kiểm tra dữ liệu sau khi import
    with driver.session() as session:
        # Count chunks
        chunk_count = session.run("MATCH (c:CHUNK) RETURN count(c) AS count").single()["count"]
        print(f"CHUNK nodes = {chunk_count}")
        
        # Count chunks có embedding
        emb_count = session.run("MATCH (c:CHUNK) WHERE c.embedding IS NOT NULL RETURN count(c) AS count").single()["count"]
        print(f"Chunks có embedding = {emb_count}")
        
        # Count relationships
        article_links = session.run("MATCH (:ARTICLE)-[r:has_chunk]->() RETURN count(r) AS count").single()["count"]
        print(f"ARTICLE --> CHUNK = {article_links}")

        clause_links = session.run("MATCH (:CLAUSE)-[r:has_chunk]->() RETURN count(r) AS count").single()["count"]
        print(f"CLAUSE --> CHUNK = {clause_links}")
        
def import_embeddings(driver,EMBEDDING_JSON):
    
    import_chunks_with_embeddings(driver, EMBEDDING_JSON)
    create_vector_index(driver)
    link_chunks_to_graph(driver)
    verify_embeddings(driver)
    print("=> DONE IMPORT EMBEDDINGS TO NEO4J!")

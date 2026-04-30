from neo4j import GraphDatabase
import json
from tqdm import tqdm
import os
from dotenv import load_dotenv
from src.utils.paths import EMB_JSON
load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

EMBEDDING_JSON = EMB_JSON

def get_neo4j_driver(uri, user, password):
    return GraphDatabase.driver(uri, auth=(user, password))

def create_vector_index(driver):
    # Tạo vector index cho Chunk nodes
    with driver.session(database="test") as session:
        # Constraint cho chunk_id
        session.run("""
            CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
            FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE
        """)
        print("Constraint cho :Chunk")
        
        # Vector index 
        try:
            session.run("""
                CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
                FOR (c:Chunk)
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
    print(f"Importing {total} chunks với embeddings...")
    
    query = """
    UNWIND $batch AS row
    MERGE (c:Chunk {chunk_id: row.chunk_id})
    SET c.content = row.content,
        c.content_with_context = row.content_with_context,
        c.chunk_type = row.chunk_type,
        c.embedding = row.embedding,
        c.token_estimate = row.token_estimate,
        c.law_code = row.metadata.law_code,
        c.law_name = row.metadata.law_name,
        c.chapter_num = row.metadata.chapter_num,
        c.chapter_title = row.metadata.chapter_title,
        c.article_num = row.metadata.article_num,
        c.article_title = row.metadata.article_title
    RETURN count(c)
    """
    
    with driver.session(database="test") as session:
        for i in tqdm(range(0, total, batch_size), desc="Chunks"):
            batch = chunks[i:i+batch_size]
            session.run(query, batch=batch)
    
    print(f"Imported {total} chunks")

def link_chunks_to_entities(driver):
    # Liên kết Chunk nodes với Entity nodes qua first_chunk

    with driver.session(database="test") as session:
        result = session.run("""
            MATCH (c:Chunk)
            MATCH (n)
            WHERE n.first_chunk = c.chunk_id
            MERGE (c)-[r:CONTAINS_ENTITY]->(n)
            RETURN count(r) AS links_created
        """)
        
        links = result.single()["links_created"]
        print(f"Created {links} CONTAINS_ENTITY relationships")

def verify_embeddings(driver):
    # Kiểm tra dữ liệu sau khi import
    with driver.session(database="test") as session:
        # Count chunks
        chunk_count = session.run(
            "MATCH (c:Chunk) RETURN count(c) AS count"
        ).single()["count"]
        print(f"  :Chunk nodes = {chunk_count}")
        
        # Count chunks có embedding
        emb_count = session.run(
            "MATCH (c:Chunk) WHERE c.embedding IS NOT NULL RETURN count(c) AS count"
        ).single()["count"]
        print(f"  Chunks với embedding = {emb_count}")
        
        # Count relationships
        rel_count = session.run(
            "MATCH (c:Chunk)-[r:CONTAINS_ENTITY]->() RETURN count(r) AS count"
        ).single()["count"]
        print(f"  :CONTAINS_ENTITY relationships = {rel_count}")
        


def import_embeddings():

    driver = get_neo4j_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    
    try:
  
        create_vector_index(driver)
        import_chunks_with_embeddings(driver, EMBEDDING_JSON)
        link_chunks_to_entities(driver)
        verify_embeddings(driver)

        
    finally:
        driver.close()


import_embeddings()
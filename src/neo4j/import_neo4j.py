from neo4j import GraphDatabase
import pandas as pd
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

def get_neo4j_driver(uri, user, password):
    # tu thu vien neo4j
    # lấy object kết nối Neo4j
    return GraphDatabase.driver(uri, auth=(user, password))


def clear_database(driver):
    with driver.session(database="test") as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("clear database!")

# tạo các ràng buộc cho csdl 
# node id unique
# index ent type
def create_constraints(driver):
    with driver.session(database="test") as session:
        try:
            session.run("""
                CREATE CONSTRAINT entity_id IF NOT EXISTS
                FOR (n:Entity) REQUIRE n.node_id IS UNIQUE
            """)
        except Exception:
            print("constraint skip")

        try:
            session.run("""
                CREATE INDEX entity_type_idx IF NOT EXISTS
                FOR (n:Entity) ON (n.entity_type)
            """)
        except Exception:
            print("index skip")


def import_nodes(driver, csv_path, batch_size=1000):
    df = pd.read_csv(csv_path)
    total = len(df)
    print(f"nodes: {total}")

    query = """
    UNWIND $batch AS row
    MERGE (n:Entity {node_id: row.node_id})
    SET n.text = row.text,
        n.entity_type = row.entity_type,
        n.first_chunk = row.first_chunk,
        n.first_sentence = row.first_sentence,
        n.occurrence_count = toInteger(row.occurrence_count)
    """

    with driver.session(database="test") as session:
        for i in tqdm(range(0, total, batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict('records')
            session.run(query, batch=batch)


def import_edges(driver, csv_path, batch_size=1000):
    df = pd.read_csv(csv_path)
    total = len(df)
    print(f"edges: {total}")

    query = """
    UNWIND $batch AS row
    MATCH (s:Entity {node_id: row.source_id})
    MATCH (t:Entity {node_id: row.target_id})
    MERGE (s)-[r:RELATES_TO {edge_id: row.edge_id}]->(t)
    SET r.relation_type = row.relation_type,
        r.confidence = toFloat(row.confidence),
        r.chunk_id = row.chunk_id,
        r.sentence_id = row.sentence_id
    """

    with driver.session(database="test") as session:
        for i in tqdm(range(0, total, batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict('records')
            session.run(query, batch=batch)

# check data trong graph database sau khi import
def verify(driver):
    with driver.session(database="test") as session:
        node_count = session.run(
            "MATCH (n:Entity) RETURN count(n) AS c"
        ).single()["c"]

        edge_count = session.run(
            "MATCH ()-[r:RELATES_TO]->() RETURN count(r) AS c"
        ).single()["c"]

        orphan_count = session.run("""
            MATCH (n:Entity)
            WHERE NOT (n)--()
            RETURN count(n) AS c
        """).single()["c"]

    print(f"nodes={node_count}, edges={edge_count}, orphan={orphan_count}")


def import_neo4j():
    driver = get_neo4j_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    node_path = 'src/neo4j/data_dir/nodes.csv'
    edge_path = 'src/neo4j/data_dir/edges.csv'
    try:
        create_constraints(driver)
        import_nodes(driver, node_path)
        import_edges(driver, edge_path)
        verify(driver)
    finally:
        driver.close()



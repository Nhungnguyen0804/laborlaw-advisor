from neo4j import GraphDatabase
import pandas as pd
from tqdm import tqdm
from src.neo4j.connection import get_driver

import os
from dotenv import load_dotenv

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")
NODE_CSV = 'src/neo4j/data_dir/nodes.csv'
EDGE_CSV = 'src/neo4j/data_dir/edges.csv'




def clear_database(driver):
    with driver.session(database="test") as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("clear database!")

# tạo các ràng buộc cho csdl 
# node id unique
# index ent type
# tạo constraint cho từng loại entity
def create_constraints(driver):
    with driver.session(database="test") as session:
        # Lấy danh sách tất cả entity_type từ CSV
        df = pd.read_csv(NODE_CSV)
        entity_types = df['entity_type'].unique()

        for etype in entity_types:
            try:
                # Tạo constraint cho từng label
                session.run(f"""
                    CREATE CONSTRAINT {etype.lower()}_id IF NOT EXISTS
                    FOR (n:{etype}) REQUIRE n.node_id IS UNIQUE
                """)
                print(f"Constraint cho :{etype}")
            except Exception as e:
                print(f"Skip {etype}: {e}")


def import_nodes(driver, csv_path, batch_size=1000):
    df = pd.read_csv(csv_path)
    total = len(df)
    print(f"nodes: {total}")
    # dùng apoc.create.node để tạo dynamic label
    query = """
    UNWIND $batch AS row
    CALL apoc.merge.node(
        [row.entity_type],  // label động từ entity_type
        {node_id: row.node_id},  // merge key
        {
            text: row.text,
            entity_type: row.entity_type,
            first_chunk: row.first_chunk,
            first_sentence: row.first_sentence,
            node_frequency: toInteger(row.node_frequency)
        },
        {}  // onMatch properties (để trống)
    ) YIELD node
    RETURN count(node)
    """

    with driver.session(database="test") as session:
        for i in tqdm(range(0, total, batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict('records')
            session.run(query, batch=batch)

def import_edges(driver, csv_path, batch_size=1000):
    df = pd.read_csv(csv_path)
    total = len(df)
    print(f"edges: {total}")
    
    # Dynamic relationship type
    query = """
    UNWIND $batch AS row
    MATCH (s {node_id: row.source_id})
    MATCH (t {node_id: row.target_id})
    CALL apoc.merge.relationship(
        s,
        row.relation_type,  // relationship type động
        {edge_id: row.edge_id},
        {
            confidence: toFloat(row.confidence),
            chunk_id: row.chunk_id,
            sentence_id: row.sentence_id
        },
        t,
        {}
    ) YIELD rel
    RETURN count(rel)
    """
    
    with driver.session(database="test") as session:
        for i in tqdm(range(0, total, batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict('records')
            session.run(query, batch=batch)

# check data trong graph database sau khi import
def verify(driver):
    with driver.session(database="test") as session:
        # Đếm nodes theo từng label
        labels = session.run("CALL db.labels()").data()
        
        for label in labels:
            count = session.run(
                f"MATCH (n:`{label['label']}`) RETURN count(n) AS c"
            ).single()["c"]
            print(f"  :{label['label']} = {count}")
        
        # Đếm relationships theo type
        rel_types = session.run("CALL db.relationshipTypes()").data()
        
        for rel_type in rel_types:
            count = session.run(
                f"MATCH ()-[r:`{rel_type['relationshipType']}`]->() RETURN count(r) AS c"
            ).single()["c"]
            print(f"  :{rel_type['relationshipType']} = {count}")

def import_neo4j():
    driver = get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    node_path = NODE_CSV
    edge_path = EDGE_CSV
    try:
        clear_database(driver)
        create_constraints(driver)
        import_nodes(driver, node_path)
        import_edges(driver, edge_path)
        verify(driver)
    finally:
        driver.close()


import_neo4j()
import os
from dotenv import load_dotenv
from src.neo4j.test_connect import test_connection
from src.neo4j.connection import get_driver, close_driver
from src.neo4j.json_to_csv import convert_json_to_csv,OUTPUT_DIR
from src.neo4j.import_emb_neo4j import import_embeddings  
from src.neo4j.import_graph_neo4j import import_neo4j 
from src.utils.paths import EMB_JSON
NODES_CSV = f'{OUTPUT_DIR}/nodes.csv'
EDGES_CSV = f'{OUTPUT_DIR}/edges.csv'
load_dotenv()

def run():
    test_connection()
    convert_json_to_csv()
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASS = os.getenv("NEO4J_PASS")
    driver = get_driver(NEO4J_URI, NEO4J_USER, NEO4J_PASS)

    try:
        import_neo4j(driver,NODES_CSV,EDGES_CSV)
        import_embeddings(driver,EMB_JSON)
    finally:
        close_driver()
run()
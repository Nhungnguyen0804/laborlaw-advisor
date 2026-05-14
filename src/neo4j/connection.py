from neo4j import GraphDatabase
neo4j_driver = None
import os
def init_driver():
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASS = os.getenv("NEO4J_PASS")

    return get_driver(
        NEO4J_URI,
        NEO4J_USER,
        NEO4J_PASS
    )


def create_neo4j_driver(uri, user, password):
    # tu thu vien neo4j
    # lấy object kết nối Neo4j
    return GraphDatabase.driver(uri, auth=(user, password))

def get_driver(uri, user, password):
    global neo4j_driver
    if neo4j_driver is None: 
        neo4j_driver = create_neo4j_driver(uri, user, password)
    return neo4j_driver


def close_driver():
    global neo4j_driver
    if neo4j_driver is not None:
        neo4j_driver.close()
        neo4j_driver = None
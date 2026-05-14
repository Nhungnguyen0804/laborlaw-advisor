from neo4j import GraphDatabase
import sys
import os
from dotenv import load_dotenv

load_dotenv()
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")
def test_connection():
    # test kết nối đến Neo4j
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        driver.verify_connectivity()
        print("Kết nối thành công!")
        

        with driver.session() as session:
            # Kiểm tra version
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] AS version")
            for record in result:
                print(f"{record['name']}: {record['version']}")
            
            # Kiểm tra số lượng nodes
            result = session.run("MATCH (n) RETURN count(n) AS cnt")
            count = result.single()["cnt"]
            print(f"Số lượng nodes hiện tại: {count}")
            
            if count > 0:
                print(f"\nDatabase đã có {count} nodes")
            
            else:
                print(f"\nDatabase trống!")
        
        driver.close()
        
     
        
    except Exception as e:
        print(f"\nKẾT NỐI THẤT BẠI!")
        print(e)
       



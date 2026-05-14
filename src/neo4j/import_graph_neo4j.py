import pandas as pd
from tqdm import tqdm

def clear_database(driver):
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("Đã xóa toàn bộ nodes và edges")
            
        #Xóa toàn bộ index (trừ index mặc định của Neo4j)
    with driver.session() as session:
        index_list = session.run("SHOW INDEXES").data()
    with driver.session() as session:
        for idx in index_list:
            name = idx.get("name")
            idx_type = idx.get("type", "")
            # Bỏ qua lookup index mặc định của Neo4j
            if name and idx_type != "LOOKUP":
                try:
                    session.run(f"DROP INDEX `{name}` IF EXISTS")
                    print(f"Dropped index: {name}")
                except Exception as e:
                    print(f"Skip index {name}: {e}")
    
    print("===> Clear database xong")


# tạo các ràng buộc cho csdl 
# node id unique => tạo ràng buộc node_id phải unique
def create_unique_node_id(driver,NODE_CSV_PATH):
    nodes_df = pd.read_csv(NODE_CSV_PATH)
    node_types = nodes_df["node_type"].unique()
    with driver.session() as session:
        for node_type in node_types:
            try:
                # Tạo unique constraint cho node_id
                query =f"""
                    CREATE INDEX {node_type.lower()}_node_id_idx IF NOT EXISTS
                    FOR (node:{node_type})
                    ON (node.node_id)
                """
                session.run(query)
                print(f"Đã tạo ràng buộc unique cho :{node_type}")
            except Exception as e:
                print(f"Skip {node_type} vì lỗi: {e}")


def import_nodes(driver, NODES_CSV_PATH, batch_size=1000):
    nodes_df = pd.read_csv(NODES_CSV_PATH)
    total_rows = len(nodes_df)
    print(f"Tổng số node: {total_rows}")
    # dùng apoc.create.node để tạo dynamic label
    query = """
    UNWIND $batch AS row
    WITH apoc.map.clean(row, [], ["", "null",null,"NaN","nan"]) AS clean  //(map, keys_to_remove, values_to_remove)
    CALL apoc.merge.node(
        [clean.node_type],  // label động từ entity_type
        {node_id: clean.node_id},  // merge key
        clean, //tự import toan bo cot csv
        {}  // onMatch properties (để trống)
    ) YIELD node
    RETURN count(node)
    """

    with driver.session() as session:
        for start_index in tqdm(range(0, total_rows, batch_size)):
            end_index = start_index + batch_size
            batch_dataframe = nodes_df.iloc[start_index:end_index]
            batch_data = batch_dataframe.to_dict("records")
            session.run(query, batch=batch_data)

def import_edges(driver, EDGES_CSV_PATH, batch_size=1000):
    edges_df = pd.read_csv(EDGES_CSV_PATH)
    total_rows = len(edges_df)
    print(f"Tổng số cạnh: {total_rows}")
    
    # dùng apoc.create.node để tạo dynamic
    # ["", "null"]
    query = """
    UNWIND $batch AS row
    WITH apoc.map.clean(row, [], ["", "null",null,"NaN","nan"]) AS clean
    MATCH (source_node {node_id: clean.source_id})
    MATCH (target_node {node_id: clean.target_id})
    CALL apoc.merge.relationship(
        source_node,
        clean.relation_type,
        {edge_id: clean.edge_id},
        clean,
        target_node,
        {}
    ) YIELD rel
    RETURN count(rel)
    """
    
    with driver.session() as session:
        for start_index in tqdm(range(0, total_rows, batch_size)):
            end_index = start_index + batch_size
            batch_dataframe = edges_df.iloc[start_index:end_index]
            batch_data = batch_dataframe.to_dict("records")
            session.run(query, batch=batch_data)

# check data trong graph database sau khi import
def check_after_imported(driver):
    with driver.session() as session:
        # Đếm nodes theo từng label
        labels_result = session.run("CALL db.labels()")
        for row in labels_result:
            label_name = row["label"]
            query = f"""
                MATCH (node:`{label_name}`)
                RETURN count(node) AS total
            """
            result = session.run(query)
            total = result.single()["total"]
            print(f"{label_name}: {total}")
    
        # Đếm relationships theo type
        relationship_result = session.run( "CALL db.relationshipTypes()")
        for row in relationship_result:
            relationship_type = row["relationshipType"]
            query = f"""
                MATCH ()-[relationship:`{relationship_type}`]->()
                RETURN count(relationship) AS total
            """
            result = session.run(query)
            total = result.single()["total"]
            print(f"{relationship_type}: {total}")
    
def import_neo4j(driver,NODES_CSV_PATH, EDGES_CSV_PATH):   
    clear_database(driver)
    create_unique_node_id(driver,NODES_CSV_PATH)
    import_nodes(driver, NODES_CSV_PATH)
    # tạo ràng buộc unique cho các node id 
    
    import_edges(driver, EDGES_CSV_PATH)
    check_after_imported(driver)
    print('=>DONE IMPORT GRAPH TO NEO4J!')




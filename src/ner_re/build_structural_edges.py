def build_structural_edges(structural_nodes):
    edges = []

    edge_counter = 1

    current_law = None
    current_chapter = None
    current_section = None
    current_article = None
    current_clause = None

    nodes = structural_nodes["nodes"]

    for node in nodes:
    
        type = node["type"]
        node_id = node["id"]

        if type == "LAW":
            current_law = node_id

        elif type == "CHAPTER":
            if current_law:
                edges.append({
                    "id": f"e_{edge_counter}",
                    "source": current_law,
                    "target": node_id,
                    "type": "HAS_CHAPTER"
                })

                edge_counter += 1

            current_chapter = node_id
            current_section = None

        elif type == "SECTION":
            if current_chapter:
                edges.append({
                    "id": f"e_{edge_counter}",
                    "source": current_chapter,
                    "target": node_id,
                    "relation": "HAS_SECTION"
                })

                edge_counter += 1

            current_section = node_id

        elif type == "ARTICLE":
            if current_section:
                edges.append({
                    "id": f"e_{edge_counter}",
                    "source": current_section,
                    "target": node_id,
                    "relation": "HAS_ARTICLE"
                })

                edge_counter += 1

            elif current_chapter:
                edges.append({
                    "id": f"e_{edge_counter}",
                    "source": current_chapter,
                    "target": node_id,
                    "relation": "HAS_ARTICLE"
                })

                edge_counter += 1

            current_article = node_id

        elif type == "CLAUSE":
            if current_article:
                edges.append({
                    "id": f"e_{edge_counter}",
                    "source": current_article,
                    "target": node_id,
                    "relation": "HAS_CLAUSE"
                })

                edge_counter += 1

            current_clause = node_id

        elif type == "POINT":
            if current_clause:
                edges.append({
                    "id": f"e_{edge_counter}",
                    "source": current_clause,
                    "target": node_id,
                    "relation": "HAS_POINT"
                })

                edge_counter += 1

    return {"edges": edges}





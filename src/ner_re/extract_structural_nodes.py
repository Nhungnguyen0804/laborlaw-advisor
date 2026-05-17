from src.ner_re.common import node_id_to_text
def extract_structural_nodes(law):
    nodes = []

    law_id = law.get("law_code", "law_unknown").replace("/", "_") # a/b/c =a_b_c

    nodes.append({
        "id": f'laborlaw_{law_id}',
        "type": "LAW",
        "text": 'Luật lao động',
        "properties": {
            "law_code": law.get("law_code"),
            "law_name": law.get("law_name"),
            "issued": law.get("issued")
        }
    })

    # CHAP
    chapters = law.get("structure", {}).get("chapters", [])

    for chapter in chapters:
        chap_id = chapter.get("chapter_id")

        nodes.append({
            "id": chap_id,
            "type": "CHAPTER",
            "text": node_id_to_text(chap_id),
            "properties": {
                "chapter_id": chap_id,
                "chapter_num": chapter.get("chapter_num"),
                "chapter_roman": chapter.get("chapter_roman"),
                "chapter_title": chapter.get("chapter_title")
            }
        })
        
        #SECTION
        if chapter.get("sections"):
            for section in chapter["sections"]:
                sec_id = section.get("section_id")

                nodes.append({
                    "id": sec_id,
                    "type": "SECTION",
                    'text':node_id_to_text(sec_id),
                    "properties": {
                        "section_id": sec_id,
                        "section_num": section.get("section_num"),
                        "section_title": section.get("section_title")
                    }
                })

                extract_articles(nodes, section.get("articles", []))

        elif chapter.get("articles"):
            extract_articles(nodes, chapter["articles"])

    return {"nodes": nodes}



def extract_articles(nodes, articles):
    for article in articles:
        art_id = article.get("article_id")

        nodes.append({
            "id": art_id,
            "type": "ARTICLE",
            'text':node_id_to_text(art_id),
            "properties": {
                "article_id": art_id,
                "article_num": article.get("article_num"),
                "article_title": article.get("article_title")
            }
        })

        extract_clauses(nodes, article.get("clauses") or [])



def extract_clauses(nodes, clauses):
    for clause in clauses:
        cls_id = clause.get("clause_id")

        nodes.append({
            "id": cls_id,
            "type": "CLAUSE",
            'text':node_id_to_text(cls_id),
            "properties": {
                "clause_id": cls_id,
                "clause_num": clause.get("clause_num"),
                "clause_content": clause.get("clause_content")
            }
        })

        extract_points(nodes, clause.get("points")or [])


def extract_points(nodes, points):
    for point in points:
        pt_id = point.get("point_id")

        nodes.append({
            "id": pt_id,
            "type": "POINT",
            'text':node_id_to_text(pt_id),
            "properties": {
                "point_id": pt_id,
                "point_label": point.get("point_label"),
                "point_content": point.get("point_content")
            }
        })




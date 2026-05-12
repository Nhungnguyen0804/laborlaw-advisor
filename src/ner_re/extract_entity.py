from src.ner_re.classification import classify_article,classify_clause
import re


TYPE_MAP = {
    # ARTICLE
    "PROHIBITION_ARTICLE": ("PROHIBITION", "by_article_title"),
    "RIGHTS_ARTICLE": ("RIGHTS", "by_article_title"),
    "OBLIGATION_ARTICLE": ("OBLIGATION", "by_article_title"),
    "PROCEDURE_ARTICLE": ("PROCEDURE", "by_article_title"),
    "PENALTY_ARTICLE": ("PENALTY", "by_article_title"),
    "DEFINITION_ARTICLE": ("LEGAL_CONCEPT", "by_article_title"),

    # CLAUSE
    "PROHIBITION_CLAUSE": ("PROHIBITION", "by_clause_title"),
    "RIGHTS_CLAUSE": ("RIGHTS", "by_clause_title"),
    "OBLIGATION_CLAUSE": ("OBLIGATION", "by_clause_title"),
    "CONDITION_CLAUSE": ("CONDITION", "by_clause_title"),
    "PROCEDURE_CLAUSE": ("PROCEDURE", "by_clause_title"),
    "PENALTY_CLAUSE": ("PENALTY", "by_clause_title"),
    "DEFINITION_CLAUSE": ("LEGAL_CONCEPT", "by_clause_title"),

    # POINT
    "PROHIBITION_POINT": ("PROHIBITION", "by_point_title"),
    "RIGHTS_POINT": ("RIGHTS", "by_point_title"),
    "OBLIGATION_POINT": ("OBLIGATION", "by_point_title"),
    "CONDITION_POINT": ("CONDITION", "by_point_title"),
    "PROCEDURE_POINT": ("PROCEDURE", "by_point_title"),
    "PENALTY_POINT": ("PENALTY", "by_point_title"),
    "DEFINITION_POINT": ("LEGAL_CONCEPT", "by_point_title"),
}


def extract_entities(text, patterns, effective_type):
    if not text:
        return []

    entities = []
    seen = set()
    # Trích xuất entities từ patterns
    for entity_type, regex_list in patterns.items():

        for regex in regex_list:
            matches = regex.finditer(text)

            for match in matches:
                start = match.start()
                end = match.end()

                if (start, end) in seen:
                    continue

                seen.add((start, end))

                entities.append({
                    "type": entity_type,
                    "text": match.group(),
                    "span": [start, end],
                    "source": "pattern"
                })
    # Thêm default entity <=>chua co
    if effective_type in TYPE_MAP:
        expected_type, source = TYPE_MAP[effective_type]
                # Kiểm tra xem đã có entity của type này chưa
        if not any(entity["type"] == expected_type for entity in entities):
            entities.append({
                "type": expected_type,
                "text": text,
                "span": [0, len(text)],
                "source": source
            })
    
    return entities

def extract_clause(clause, article_type, patterns):
    content = clause["clause_content"]
    clause_type, is_header_list = classify_clause(content)
    # clause tự classify được thì dùng, không thì dùng article_type
    if clause_type:
        effective_type = clause_type
    else:
        effective_type = article_type

    points = clause.get("points") or []
    if is_header_list and points:
        header = re.split(r'\s*[a-zđ]\)', content)[0].strip()
        entities = extract_entities(header, patterns, effective_type)
    else:
        entities = extract_entities(content, patterns, effective_type)
    # entities = extract_entities(
    #     text=content,
    #     patterns=patterns,
    #     article_type=effective_type 
    # )

    return {
        "node_id": clause["clause_id"],
        "node_type": "clause",
        "clause_type": clause_type,
        "is_header_list": is_header_list,
        "entities": entities
    }


def extract_point(point, article_type,clause_type, patterns):
    content = point["point_content"]

    entities = extract_entities(
        text=content,
        patterns=patterns,
        effective_type=article_type
    )

    return {
        "node_id": point["point_id"],
        "node_type": "point",
        "entities": entities
    }




def process_article(article,patterns):

    article_type = classify_article(article["article_title"])
    results = []

    clauses = article.get("clauses") or []
    for clause in clauses:

        clause_result  = extract_clause(clause,article_type,patterns)

        results.append(clause_result)

        points = clause.get("points") or []
        clause_type = clause_result["clause_type"]
        for point in points:
            point_result = extract_point(point,article_type,clause_type,patterns)

            results.append(point_result)

    return results

import re
def get_article_id(node_id: str) -> str:
    """
    ch1_d2_k1 -> ch1_d2
    ch1_m1_d2_k1 -> ch1_m1_d2
    """
    m = re.match(r"(.+_d\d+)", node_id)
    return m.group(1) if m else node_id


def get_chapter_id(node_id):
    return node_id.split("_")[0]


def calculate_confidence(action_text):
    """Score relation dựa trên action string"""
    HIGH_CONFIDENCE_WORDS = [
        "phải", "được", "cấm", "không được", "có quyền",
        "quy định", "theo", "áp dụng", "bao gồm",
        "thuộc", "là", "bị", "chịu", "thực hiện"
    ]
    
    if not action_text:
        return 0.3
    
    action_lower = action_text.lower()
    for word in HIGH_CONFIDENCE_WORDS:
        if word in action_lower:
            return 0.9
    
    # Action ngắn = relation rõ ràng
    if len(action_text) < 20:
        return 0.7
    
    return 0.5




def print_rel_result(relationships):
    from collections import Counter

    relation_counts = Counter(
        r["relation"] for r in relationships
    )

    type_pair_counts = Counter(
        (r["source"]["type"], r["target"]["type"])
        for r in relationships
    )

    print(f"\nrelationships: {len(relationships)}")

    print("\nrelation count")
    for rel_type, count in relation_counts.most_common():
        print(f"{rel_type}: {count}")

    print("\ntype pairs")
    for (src_type, tgt_type), count in type_pair_counts.most_common(10):
        print(f"{src_type} -> {tgt_type}: {count}")

    print("\nsample")
    for rel in relationships[:10]:
        src_type = rel["source"].get("type", "unknown")
        tgt_type = rel["target"].get("type", "unknown")

        src_value = (
            rel["source"].get("text")
            or rel["source"].get("value")
            or rel["source"].get("id")
            or "?"
        )

        tgt_value = (
            rel["target"].get("text")
            or rel["target"].get("value")
            or rel["target"].get("id")
            or "?"
        )

        print(
            f"{src_type}({src_value}) "
            f"[{rel['relation']}] "
            f"{tgt_type}({tgt_value})"
        )

    rel_result = {
        "total": len(relationships),
        "by_relation": dict(relation_counts),
        "by_type_pair": dict(type_pair_counts),
    }

    return rel_result


def build_mention_edges(property_entities):
    edges = []

    for item in property_entities:
        node_id = item["node_id"]

        for ent in item["entities"]:
            edges.append({
                "source": ent["id"],
                "target": node_id,
                "type": "MENTIONS"
            })

    return edges



def split_structural_text_into_sentences(text):
    # split dieu khoan diem thanh cau 
    # Replace delimiters
    text = text.replace('\n', ' <SPLIT> ')
    text = text.replace(';', ' <SPLIT> ')
    text = text.replace('.', ' <SPLIT> ')

    # Split và clean
    sentences = [s.strip() for s in text.split('<SPLIT>') if s.strip()]
    
    return sentences

def add_sentences_to_nodes(structural_nodes):
    """
    Thêm field 'sentences' cho mỗi node
    """

    nodes = structural_nodes.get("nodes", [])

    for node in nodes:

        props = node.get("properties", {})

        # lấy text từ nhiều field có thể có
        text = (
            props.get("clause_content", "")
            or props.get("article_title", "")
            or props.get("chapter_title", "")
            or props.get("law_name", "")
        )

        if text.strip():
            node["sentences"] = split_structural_text_into_sentences(text)
        else:
            node["sentences"] = []

    return structural_nodes

def run_re(property_entities, structural_nodes):
    all_relationships = []

    groups = {}
    # group theo article
    for node in property_entities:

        node_id = node["node_id"]
        if node_id not in groups:
            groups[node_id] = []
        
        node_texts = {}  # Lưu text của mỗi node

        article_id = get_article_id(node_id)

        # nếu chưa có key thì tạo list rỗng
        if article_id not in groups:
            groups[article_id] = []

        # add entities
        for ent in node["entities"]:

            groups[article_id].append({
                "type": ent["type"],
                "value": ent["text"],
                "node_id": node_id
            })
    edges = build_mention_edges(property_entities)
    return edges
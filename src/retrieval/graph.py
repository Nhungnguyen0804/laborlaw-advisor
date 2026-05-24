import re
from sentence_transformers import SentenceTransformer
from src.utils.file_utils import load_json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
model = SentenceTransformer('keepitreal/vietnamese-sbert')
from src.ner_re.common import get_article_id,roman_to_int
from src.neo4j.query_neo4j import query_structural_children, query_point_node_direct,query_node_direct


QUES_TEMPLATES = {
    "has_clause": [
        "các khoản của điều X",
        "điều X có mấy khoản",
        "liệt kê khoản của điều X",
        "khoản nào trong điều X",
        "điều X gồm khoản nào"
    ],
    "has_point": [
        "các điểm của khoản X",
        "khoản X có điểm nào",
        "liệt kê điểm trong khoản X",
        "điểm nào thuộc khoản X"
    ],
    "has_section": [
        "các mục của điều X",
        "điều X có mục nào",
        "mục nào trong điều X"
    ],
    "has_article": [
        "các điều của chương X",
        "chương X gồm điều nào",
        "liệt kê điều trong chương X"
    ],
    'has_chapter': [
        'bộ luật lao động gồm chương nào',
        'bộ luật lao dộng gồm những chương nào',
        'các chương của bộ luật lao động',
        'liệt kê các chương trong bộ luật lao động',
        'các chương trong bộ luật lao động',
    ]
}

# Embed tất cả canonical questions
canonical_embeddings = {}

for relation, questions in QUES_TEMPLATES.items():
    embeddings = model.encode(questions)
    # Lấy trung bình để có 1 vector đại diện
    canonical_embeddings[relation] = np.mean(embeddings, axis=0)

# Save để reuse
np.save('canonical_embeddings.npy', canonical_embeddings)

import re

def extract_refs(text):
    """
    "Điểm a khoản 2 điều 13 chương III"
    chương -> điều -> khoản -> điểm
    [
        "chương iii",
        "điều 13",
        "khoản 2",
        "điểm a"
    ]
    """

    text = text.lower()

    # regex cho legal refs
    patterns = {
        "blld":    r"(bllđ|bộ\s+luật\s+lao\s+động)",
        "chương": r"chương\s+([IVXLC]+|\d+)",
        "điều":   r"điều\s+(\d+)",
        "khoản":  r"khoản\s+(\d+)",
        "điểm":   r"điểm\s+([a-z])\b",

    }
    refs = []
    blld_matches = re.findall(patterns["blld"], text)
    if blld_matches:
        refs.append("laborlaw")

    chuong_matches = re.findall(patterns["chương"], text)
    for value in chuong_matches:
        if value.isdigit():
            num = int(value)
        else:
            try:
                num = roman_to_int(value.upper())
            except:
                num = value
        refs.append(f"ch{num}")
    dieu_matches = re.findall(patterns["điều"], text)
    for value in dieu_matches:
        refs.append(f"d{value}")
    khoan_matches = re.findall(patterns["khoản"], text)
    for value in khoan_matches:
        refs.append(f"k{value}")
    diem_matches = re.findall(patterns["điểm"], text)
    for value in diem_matches:
        refs.append(f"{value}")

    return refs

def build_node_id_from_refs(refs):
    chuong_refs = []
    dieu_refs = []
    khoan_refs = []
    diem_refs = []

    for ref in refs:
        if ref.startswith("ch"):
            chuong_refs.append(ref)
        elif ref.startswith("d") and len(ref) > 1 and ref[1:].isdigit():
            # d13, d5 -> điều
            dieu_refs.append(ref)
        elif ref.startswith("k") and len(ref) > 1 and ref[1:].isdigit():
            # k2, k10 -> khoản
            khoan_refs.append(ref)
        else:
            # a, b, c, d, e, f, k 1 minh -> điểm
            diem_refs.append(ref)    
    sorted_refs = chuong_refs + dieu_refs + khoan_refs + diem_refs
    return "_".join(sorted_refs)

def find_entity_from_query(user_query, nodes):
    # Điều 13 gồm những gì 
    # {'id': 'ch1_d13', 'type': 'ARTICLE', 'text': 'Chương 1 Điều 13'}
    query_lower = user_query.lower()
    refs = extract_refs(query_lower)
    # print(refs)
    if not refs:
        print('ko co refs')
        return None
    node_id_target = build_node_id_from_refs(refs)
    for node in nodes:
        node_id = node['id']
        if node_id_target in node_id:
            return node
        
    print('ko tim thay ',node_id_target)
    return None 
    

def get_valid_relations(entity_type):
        """Map entity type -> valid relations"""
        mapping = {
            'LAW': ['has_chapter'],
            'CHAPTER': ['has_article','has_section'],
            'ARTICLE': ['has_clause','has_point'],
            'CLAUSE': ['has_point', ],
            'SECTION': ['has_article','has_clause', 'has_point'],
        }
        return mapping.get(entity_type, [])

def find_relation_from_query( user_query, entity_type):
    """
    user_query:
        "Các khoản của Điều 13 gồm gì?"

    Sau khi normalize:
        "các khoản của điều X gồm gì?"
    Encode câu hỏi thành vector embedding
    So sánh với embedding của các câu canonical
    Chọn relation có similarity cao nhất
    Nếu similarity đủ lớn thì trả về relation
    """

    normalized_query = user_query.lower()

    # "điều 13" -> "điều X"
    # "khoản 2" -> "khoản X"

    normalized_query = re.sub(
        r"(điều|chương|khoản|mục|điểm)\s+\d+",
        r"\1 X",
        normalized_query
    )

    
    # Convert query thành embedding vector
    query_embedding = model.encode([normalized_query])[0]
   

    # Lấy danh sách relation hợp lệ
    # entity_type = "article"
    # -> có thể valid:
    #    HAS_CLAUSE
    
    valid_relations = get_valid_relations(entity_type)

    # Tìm relation có similarity cao nhất
    best_relation_type = None
    highest_similarity_score = -1

    for relation_type in valid_relations:

        # Bỏ qua nếu relation chưa có embedding
        if relation_type not in canonical_embeddings:
            continue

        # Embedding của canonical question
        canonical_embedding = canonical_embeddings[relation_type]

        # Tính cosine similarity
        similarity_score = cosine_similarity(query_embedding.reshape(1, -1),canonical_embedding.reshape(1, -1))[0][0]

        # Update nếu tốt hơn
        if similarity_score > highest_similarity_score:
            highest_similarity_score = similarity_score
            best_relation_type = relation_type

    # Kiểm tra threshold
    # Nếu similarity quá thấp
    # -> coi như không match relation nào
    similarity_threshold = 0.65
    # print('highest_similarity_score',highest_similarity_score)
    # print('best_relation_type',best_relation_type)
    if highest_similarity_score > similarity_threshold:
        return best_relation_type

    return None

def format_graph_result(children):
    if not children:
        return "Không tìm thấy thông tin."

    lines = []  
    for child in children:
        title = child["text"]
        content = child["content"] if child["content"] else child["text"]
        lines.append(f"{title}: {content}")
    return "\n\n".join(lines)

def run_retrieval_graph(driver,user_query):
    data = load_json('data/graph/structural_nodes.json')
    nodes = data['nodes']
    entity = find_entity_from_query(user_query, nodes)
    print('entity: ',entity)
    # entity = {'id': 'ch1_d13', 'type': 'ARTICLE'}
    result = None
    if not entity:
        print('lỗi run_retrieval_graph: entity none, ko tim thay')
        return None
    else:
        if entity['type'] == 'POINT':
            result = query_point_node_direct(driver, entity['id'])
        else:
            relation = find_relation_from_query(user_query, entity['type'])
            # relation = 'has_clause'
            if not relation:
                print('lỗi run_retrieval_graph: rel None , k tim thay rel')
            else:       
                children = query_structural_children(driver,entity['id'],relation)
                if not children :
                    print('k có child, query direct')
                    children = query_node_direct(driver, entity['id'])
                    print('node direct: ',children)
                result = children

    if not result:
        return None 
    else :
        return format_graph_result(result)

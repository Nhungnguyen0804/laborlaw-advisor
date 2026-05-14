import re
def get_article_id(node_id) :
    """
    ch1_d2_k1 -> ch1_d2
    ch1_m1_d2_k1 -> ch1_m1_d2
    """
    m = re.match(r"(.+_d\d+)", node_id)
    return m.group(1) if m else node_id


def get_chapter_id(node_id):
    return node_id.split("_")[0]


def build_mention_edges(property_entities):
    edges = []

    for item in property_entities:
        node_id = item["node_id"]

        for ent in item["entities"]:
            edges.append({
                "source": node_id, # dieu khoan diem 
                "target": ent["id"], # de cap den ent
                "type": "mentions"
            })

    return edges


def calculate_sentence_spans(full_text, sentences):
    spans = []
    current_pos = 0

    for sentence in sentences:
        # Tìm vị trí sentence trong full_text
        sentence_lower = sentence.lower()
        idx = full_text.find(sentence_lower, current_pos)

        # Fallback nếu không tìm thấy
        if idx == -1:
            idx = current_pos

        spans.append({
            "begin": idx,
            "end": idx + len(sentence_lower)
        })

        current_pos = idx + len(sentence_lower)

    return spans



def get_entity_length(entity):

    start = entity["span"][0]
    end = entity["span"][1]

    return end - start


def is_overlap(entity1, entity2):

    start1 = entity1["span"][0]
    end1 = entity1["span"][1]

    start2 = entity2["span"][0]
    end2 = entity2["span"][1]

    # Có overlap nếu:
    # entity1 bắt đầu trước khi entity2 kết thúc
    # và entity1 kết thúc sau khi entity2 bắt đầu
    return start1 < end2 and end1 > start2


def remove_overlap_entities(entities):

    # Không có entity
    if len(entities) == 0:
        return []

    # Sort entity dài nhất lên trước theo độ dài span 
    sorted_entities = sorted(
        entities,
        key=get_entity_length,
        reverse=True
    )

    selected_entities = []

    # Duyệt từng entity
    for current_entity in sorted_entities:

        has_overlap = False

        # So sánh với entity đã chọn trước đó
        for selected_entity in selected_entities:

            if is_overlap(current_entity, selected_entity):
                has_overlap = True
                break

        # Nếu không overlap thì giữ lại
        if not has_overlap:
            selected_entities.append(current_entity)

    return selected_entities

def get_entity_begin_position(entity):
    """
    Lấy vị trí bắt đầu của entity trong câu.
    """
    return entity["span_in_sentence"]["begin"]


def extract_action_text(sentence_text, entities):
    #Lấy phần text nằm giữa các entity liên tiếp trong câu

    # Cần ít nhất 2 entity mới có thể tạo relation
    if len(entities) < 2:
        return []

    # Danh sách kết quả
    extracted_actions = []

    # Sắp xếp entity theo vị trí xuất hiện trong câu
    entities_sorted_by_position = sorted(
        entities,
        key=get_entity_begin_position
    )
    
    remove_action_texts = [ 
        # ', hai bên',
        'và nguồn tài chính','khác trong cùng đơn vị','trước và sau',
        'và một số','và hoạt động','mới thì ngoài','trong số danh sách',
        # ? 

        'vẫn tiếp tục', 'như sau: a) ít nhất', 'thì xử lý như sau: a)', 'như sau: a)',
        'a)', 'trực tiếp','bên phía','với nhiều','mới',
        'thì quyền,','thì ngoài việc','thì người đó','thì thời điểm',
        ': a)','những','hiện tại và','kế tiếp','đã', 'trong','với một',', sau đó',
        'mới thì','do các','và các','kế tiếp và', 'khác mà vẫn',', một số','tại đó',
        'khác', ", tập",'tập','do','quá','còn','đến','đi',
        'nhưng', 'có', '(',
        "thì", "mà", "của", "tại", "theo", "về", "cho", "với",
        ':',';',
    ]
    # Duyệt từng cặp entity liên tiếp
    for index in range(len(entities_sorted_by_position) - 1):

        # Entity hiện tại
        current_entity = entities_sorted_by_position[index]

        # Entity kế tiếp
        next_entity = entities_sorted_by_position[index + 1]

        # Vị trí kết thúc của entity hiện tại
        current_entity_end = current_entity["span_in_sentence"]["end"]

        # Vị trí bắt đầu của entity kế tiếp
        next_entity_begin = next_entity["span_in_sentence"]["begin"]

        # Lấy phần text nằm giữa 2 entity
        # fix ' abc ' thành 'abc'
        raw_text = sentence_text[current_entity_end:next_entity_begin]
        text_between_entities = raw_text.strip()
        # số whitespace bên trái
        # Không có text -> bỏ
        if not text_between_entities:
            continue
  
        if text_between_entities.lower() in remove_action_texts:
            continue
        left_strip_count = len(raw_text) - len(raw_text.lstrip())
        # phải 
        right_strip_count = len(raw_text) - len(raw_text.rstrip())
        # span mới sau strip
        clean_begin = current_entity_end + left_strip_count
        clean_end = next_entity_begin - right_strip_count

        # Bỏ qua nếu không có text
        if text_between_entities:

            # Tạo object kết quả
            action_data = {
                "source_entity": current_entity["id"],
                "target_entity": next_entity["id"],
                "action_text": text_between_entities,
                "raw_sentence": sentence_text,
                "span": {
                    "begin": clean_begin,
                    "end": clean_end
                }
            }

            # Thêm vào danh sách kết quả
            extracted_actions.append(action_data)

    return extracted_actions


def map_entities_to_sentences(structural_nodes, property_entities):
    sentence_data = []
    # Group entities theo node_id
    entities_by_node = {}
    for item in property_entities:
        node_id = item["node_id"]
        # entities_by_node[node_id] = item["entities"]
        entities_by_node[node_id] = remove_overlap_entities(item["entities"])
    
    # Lấy list nodes
    nodes = structural_nodes.get("nodes", [])
   
    # Process từng node
    for node_data in nodes:
        node_id = node_data["id"]
        sentences = node_data.get("sentences", [])
    
        if not sentences:
            continue
        
        # Ghép lại full text từ sentences
        # full_text = " ".join(sentences).lower()
        props = node_data.get("properties", {})
        raw_text = (
            props.get("clause_content", "")
            or props.get("article_title", "")
            or props.get("chapter_title", "")
            or props.get("law_name", "")
        )
        full_text = raw_text.lower()
        
        # Tính span của từng sentence
        sentence_spans = calculate_sentence_spans(full_text, sentences)
        
        node_entities = entities_by_node.get(node_id, [])
        
        # Map entity vào sentence
        for idx in range(len(sentences)):
            sentence_text = sentences[idx].lower()
            # sentence_text = sentences[idx]
            sentence_span = sentence_spans[idx]
            sentence_id = f"{node_id}_s{idx}"
            
            entities_in_sentence = []
            for ent in node_entities:
    
                ent_span = ent["span"]
                ent_begin = ent_span[0]  # get phần tử 1
                ent_end = ent_span[1]   # get 2
                
                # Entity thuộc sentence hiện tại
                # Nếu entity bắt đầu trong khoảng của câu → thuộc câu này
                if (sentence_span["begin"]<= ent_begin< sentence_span["end"]):
                    entities_in_sentence.append({
                        "id": ent["id"],
                        "type": ent["type"],
                        "text": ent["text"],
                        # Span theo node
                        "span_in_parent_node": {
                            "begin": ent_begin,
                            "end": ent_end
                        },
                        # Span relative trong sentence
                        "span_in_sentence": {
                            "begin": ent_begin - sentence_span["begin"],
                            "end": ent_end - sentence_span["begin"]
                        },
                        "properties": ent.get("properties", {})
                    })
            # Trích xuất action text
            actions = extract_action_text(sentence_text, entities_in_sentence)
            sentence_data.append({
                "sentence_id": sentence_id,
                "node_id": node_id,
                "sentence_text": sentence_text,
                "sentence_span": sentence_span,
                "entities": entities_in_sentence,
                "action_texts": actions
            })
    
    return sentence_data

# GIÁN TIEPPPPPPPP
# tạo cạnh gián tiếp 
def create_indirect_edges(data):

    for doc in data:
        edges = doc.get('action_texts', [])

        new_edges = []

        for connect_edge in edges:

            # chỉ lấy connect edge
            if not connect_edge.get('is_connect'):
                continue

            ent1 = connect_edge.get('source_entity')
            ent2 = connect_edge.get('target_entity')

            # tìm edge thật từ ent2
            for real_edge in edges:

                if real_edge.get('is_connect'):
                    continue

                if real_edge.get('source_entity') != ent2:
                    continue

                ent3 = real_edge.get('target_entity')

                # tạo edge mới
                new_edges.append({
                    'source_entity': ent1,
                    'target_entity': ent3,
                    'edge_type': real_edge.get('edge_type'),
                    'is_indirect_edge': True,
                    'created_via_entity': ent2
                })

        edges.extend(new_edges)

    return data

def export_indirect_edges(data, output_path):

    lines = []

    for doc in data:

        entities = {
            ent['id']: ent
            for ent in doc.get('entities', [])
        }

        for edge in doc.get('action_texts', []):

            if not edge.get('is_indirect_edge'):
                continue

            ent1_id = edge.get('source_entity')
            ent2_id = edge.get('created_via_entity')
            ent3_id = edge.get('target_entity')

            rel = edge.get('edge_type')
            ent1_obj = entities.get(ent1_id, {})
            ent2_obj = entities.get(ent2_id, {})
            ent3_obj = entities.get(ent3_id, {})
            if ent1_obj.get('type') != ent2_obj.get('type'):
                continue
            
            ent1 = ent1_obj.get('text', ent1_id)
            ent2 = ent2_obj.get('text', ent2_id)
            ent3 = ent3_obj.get('text', ent3_id)

            lines.append(f'{ent1}, connect, {ent2}\n')
            lines.append(f'{ent2}, {rel}, {ent3}\n')
            lines.append(f'{ent1}, {rel}, {ent3}\n')
            lines.append('------------------------------\n')
    from src.utils.file_utils import save_txt
    save_txt(lines, output_path)

# đồng bộ format với mention edge 
def extract_edges(data):
    all_edges = []

    for item in data:

        for edge in item.get('action_texts', []):

            source = edge.get('source_entity')
            target = edge.get('target_entity')
            rel_type = edge.get('edge_type')

            if not source or not target or not rel_type:
                continue

            all_edges.append({
                'source': source,
                'target': target,
                'type': rel_type
            })
    print(f'Extract được {len(all_edges)} cạnh!')
    return all_edges

# phân loại action text to edges
def run_re(property_entities, structural_nodes):

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
    mention_edges = build_mention_edges(property_entities)
    map_ent_to_sentences = map_entities_to_sentences(structural_nodes, property_entities)
    from src.utils.file_utils import save_json
    save_json(map_ent_to_sentences, 'src/ner_re/map_ent_to_sentences.json')

    all_lines = []
    for sentence_item in map_ent_to_sentences:
        action_texts = sentence_item["action_texts"]
        for action in action_texts:
            line = action["action_text"]
            all_lines.append(line + "\n")
            
    from src.utils.file_utils import save_txt 
    save_txt(all_lines, "src/ner_re/test/action_text.txt")


    ''' 
        "action_text": ",",
        "is_connect": true  
        "action_text": "phải trả",
        "is_connect": false 
      '''
    from src.ner_re.classification import is_connect_token,classify_action_to_edge_type
    structural_count = 0
    semantic_count = 0
    
    for sentence in map_ent_to_sentences:
        for action in sentence["action_texts"]:
            text = action["action_text"]

            is_connect = is_connect_token(text)

            action["is_connect"] = is_connect

            if is_connect:
                structural_count += 1
                action["edge_type"] = None
            else:
                semantic_count += 1
                # Map sang edge_type
                edge_type = classify_action_to_edge_type(text)
                action["edge_type"] = edge_type

    save_json(map_ent_to_sentences, 'src/ner_re/map_with_edge_type.json')


    # test unknowns 
    unknowns = []

    for sentence_item in map_ent_to_sentences:
        for action in sentence_item["action_texts"]:
            if not action["is_connect"] and action["edge_type"] is None:
                unknowns.append({
                    "text": action["action_text"],
                    "sentence": sentence_item["sentence_text"]
                })

    print(f"===> Tìm thấy {len(unknowns)} unknown actions")
    save_json(unknowns, 'src/ner_re/unknown_actions.json')


    total_edges = 0
    edges_without_type = 0

    for item in map_ent_to_sentences:
        for action in item.get("action_texts", []):
            total_edges += 1

            if not action.get("edge_type"):
                edges_without_type += 1

    print(f'\n===> {edges_without_type}/{total_edges} chưa có edge_type')
    # ent1 ent2  (ko có text nào ở giữa) => map (ent,ent): rel từ map 

    from src.ner_re.rel_mapping import fill_missing_relationship_types
    map_filled_rel_types = fill_missing_relationship_types(map_ent_to_sentences)
    save_json(map_filled_rel_types, 'src/ner_re/map_filled_rel_types.json')

    map_indirect_edges = create_indirect_edges(map_filled_rel_types)
    save_json(map_indirect_edges, 'src/ner_re/map_indirect_edges.json')
    export_indirect_edges(map_indirect_edges, 'src/ner_re/test/indirect_edges.txt')

    semantic_edges = extract_edges(map_indirect_edges)
    all_semantic_edges = mention_edges + semantic_edges

    # THÊM ID CHO TOÀN BỘ CẠNH
    for idx, edge in enumerate(all_semantic_edges, start=1):
        edge['id'] = f'edge_smt_{idx}'

    print(f'ALL SEMANTIC EDGES có {len(all_semantic_edges)} cạnh!')

    return all_semantic_edges
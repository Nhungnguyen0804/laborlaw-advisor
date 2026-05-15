from src.utils.file_utils import load_json
from src.ner_re.common import get_law_id_from_text
import os 


def extract_legal_refs_text(property_entities,output_path):
    legal_refs = []

    for node in property_entities:
        node_id = node["node_id"]
        for ent in node["entities"]:
            if ent["type"] == "LEGAL_REF":
                legal_refs.append(f"node_id={node_id} ==> {ent.get('text', '')}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(legal_refs))

property_entities = load_json('src/ner_re/property_entities.json')
legalref_text_path = 'test/legalref.txt'

extract_legal_refs_text(property_entities,legalref_text_path)


def expand_cites_edges_from_legal_refs(property_entities, structural_nodes):
    structural_index = {}

    for node in structural_nodes['nodes']:
        node_id = node["id"]
        structural_index[node_id] = node
        # {ch1_d3_k4_a : node}

    LABORLAW_ROOT_ID = "laborlaw_45_2019_QH14"
    LABORLAW_SUFFIX = "của bộ luật lao động"

    edges = []

    for node in property_entities:
        # node_id = node["node_id"]

        for ent in node.get("entities", []):
            if ent["type"] != "LEGAL_REF":
                continue
            ent_id = ent["id"]
            text = ent.get("text", "").strip()

            # "bộ luật này" => root laborlaw
            if text == "bộ luật này":
                edges.append({
                    "source": ent_id,
                    "target": LABORLAW_ROOT_ID,
                    "type": "cites",
                })
                continue

            # có "của bộ luật lao động" => chắc chắn trong kg
            # chỉ "điều X" or "khoản Y điều X" => cũng thử link (confidence thấp hơn)
            if LABORLAW_SUFFIX in text:
                core_text = text.replace(LABORLAW_SUFFIX, "").strip()
            else:
                core_text = text

            law_id_from_text = get_law_id_from_text(core_text)
            if law_id_from_text is None:
                # tham chiếu luật khác, bỏ qua
                continue

            # tìm structural node có node_id kết thúc bằng law_id_from_text
            # ch1_d3_k4_a va k4_a
            target_node_id = None
            for structural_node_id in structural_index:
                # neu structural_node_id kết thúc bằng "_law_id_from_text"
                if structural_node_id.endswith(f"_{law_id_from_text}"):
                    target_node_id = structural_node_id
                    break

                #hoac node id bằng đúng law_id_from_text
                if structural_node_id == law_id_from_text:
                    target_node_id = structural_node_id
                    break
            
            if target_node_id is None:
                continue

            edges.append({
                "source": ent_id,
                "target": target_node_id,
                "type": "cites",
            })

    return edges


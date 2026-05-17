import copy
def dedup_semantic_nodes(nodes):
    seen = {}
    result = []

    for node in nodes:
        key = (
            node.get("type"),
            node.get("text"),
            tuple(node.get("span", []))
        )

        if key not in seen:
            canonical = copy.deepcopy(node)
            # add field moi 
            canonical["merged_entity_ids"] = [node["id"]]
            seen[key] = canonical
            result.append(canonical)

        else:
            canonical_node = seen[key]
            canonical_node["merged_entity_ids"].append(node["id"])

    return result



def build_ent_id_map(nodes):
    entity_id_map = {}

    for node in nodes:
        canonical_id = node["id"]

        for merged_id in node.get("merged_entity_ids", []):
            entity_id_map[merged_id] = canonical_id

    return entity_id_map


def remap_edges(edges, entity_id_map):
    result = []

    for edge in edges:

        original_source = edge["source"]
        original_target = edge["target"]
        new_source  = entity_id_map.get(original_source,original_source)
        new_target = entity_id_map.get(original_target,original_target)

        # neu original != nhau nhung sau remap lại = nhau => bỏ 
        if (original_source != original_target and new_source == new_target):
            continue

        new_edge = copy.deepcopy(edge)

        new_edge["source"] = new_source
        new_edge["target"] = new_target

        result.append(new_edge)

    return result


def dedup_edges(edges):
    seen = set()
    result = []

    for edge in edges:
        # bo tu noi chinh no
        if edge["source"] == edge["target"]:
            continue
        key = (
            edge["source"],
            edge["target"],
            edge["type"]
        )

        if key not in seen:
            seen.add(key)
            result.append(edge)

    return result
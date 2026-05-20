from src.eval.sample.process_gtruth import NODE_IDS
from src.utils.paths import PROPERTY_ENTITES_JSON
from src.utils.file_utils import load_json ,save_json
import unicodedata
import re
def dedup_entities_in_structure(r_ents):
    for node in r_ents:
        seen = set()
        new_entities = []
        for ent in node.get("entities", []):
            key = (
                ent.get("type"),
                ent.get("text", "").lower().strip()
            )
            if key not in seen:
                seen.add(key)
                new_entities.append(ent)
        node["entities"] = new_entities
    return r_ents

def process_regex_ents(regex_ents_data,output_path):
    results = []

    for node in regex_ents_data:
        # Chỉ lấy node_id nằm trong NODE_IDS
        if node["node_id"] not in NODE_IDS:
            continue

        # Lấy entities cần 
        entities = []

        for ent in node.get("entities", []):
            entities.append({
                "text": ent["text"],
                "type": ent["type"]
            })

        # Tạo output
        results.append({
            "node_id": node["node_id"],
            "entities": entities
        })
    
    results = dedup_entities_in_structure(results)
    save_json(results, output_path)
    return results

def normalize_entity(text):
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    # gop nhieu space thanh 1 de strip
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def eval_ent_match(pred_ent, gt_ent):

    pred_text = normalize_entity(pred_ent["text"])
    pred_type = pred_ent["type"]

    gt_text = normalize_entity(gt_ent["text"])
    gt_type = gt_ent["type"]
   
    # EXACT <=> same text va type
    if pred_text == gt_text and pred_type == gt_type:
        return "exact"
        
    # TYPE ERROR (sai cai type <=> same text + khac type nhau)
    elif pred_text == gt_text and pred_type != gt_type:
        return "type_error"

    # PARTIAL (chung type va text cua cai nay nam trong text cua cai kia )
    elif pred_type == gt_type:
        if pred_text in gt_text or gt_text in pred_text:
            return "partial"
    # no match
    return "no_match"
def build_node_dict(data):
    result = {}
    for item in data:
        node_id = item["node_id"]
        result[node_id] = item
    return result

def count_match_result(match_type, match_results):
    if match_type =='exact':
        match_results["exact_count"] += 1
    elif match_type == "partial":
        match_results["partial_count"] += 1
    elif match_type == "type_error":
        match_results["type_error_count"] += 1
 

def eval_one_node(node_id, regex_dict, gt_dict,match_results,pertype_results):
    if node_id not in regex_dict or node_id not in gt_dict:
        print(f"node id {node_id} ko nam trong regex dict or gtruth dict!")
        return

    r_node = regex_dict[node_id]
    gt_node = gt_dict[node_id]
    # print(r_node["node_id"])
    # print(gt_node["node_id"])

    r_ents = r_node["entities"]
    gt_ents = gt_node['entities']
    gt_matched = [False] * len(gt_ents)
    
    for r_ent in r_ents:
        found_match = False
        ent_type = r_ent["type"]
        for i, gt_ent in enumerate(gt_ents):
            if gt_matched[i]: # true la da eval r nen bo qua 
                continue
            match_type = eval_ent_match(r_ent, gt_ent)
            if match_type != "no_match":
                gt_matched[i] = True
                count_match_result(match_type,match_results)
                count_pertype(ent_type, match_type,pertype_results)
                found_match = True
                break

        #no match = FP 
        if not found_match:
            match_results['fp']+=1
            create_type_in_res(ent_type,pertype_results)
            pertype_results[ent_type]['fp'] +=1

    # count fn 
    # gt nào chưa được match
   

    for matched, gt_ent in zip(gt_matched, gt_ents):
        if not matched:
            match_results["fn"] += 1
            gt_type = gt_ent["type"]
            create_type_in_res(gt_type,pertype_results)
            pertype_results[gt_type]["fn"] += 1



def calculate_precision(tp, fp):
    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0
    return precision

def calculate_recall(tp,fn):
    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0
    return recall
def calculate_f1(precision,recall):
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0
    return f1

def eval_overall(match_results):
    #TP
    exact_tp = match_results["exact_count"]
    partial_tp = match_results["partial_count"]
    type_error = match_results["type_error_count"]

    total_tp = exact_tp + partial_tp
    fp = match_results["fp"]
    fn = match_results["fn"]
    precision = calculate_precision(total_tp, fp)
    recall = calculate_recall(total_tp,fn)
    f1 = calculate_f1(precision,recall)

    print('exact match: ',exact_tp)
    print('partial match: ',partial_tp)
    print('type error: ',type_error)
    print('false positive: ',fp)
    print('false negative: ',fn)
    print('- precision: ',precision)
    print('- recall: ',recall)
    print('- f1: ',f1)

def create_type_in_res(ent_type,pertype_results):
    if ent_type not in pertype_results:
        pertype_results[ent_type] = {
            "exact_count": 0,
            "partial_count": 0,
            "type_error_count": 0,
            "fp": 0,
            "fn": 0
        }  

def count_pertype(ent_type,match_type,pertype_results):
    create_type_in_res(ent_type, pertype_results) 
    if match_type == "exact":
        pertype_results[ent_type]["exact_count"] += 1
    elif match_type == "partial":
        pertype_results[ent_type]["partial_count"] += 1
    elif match_type == "type_error":
        pertype_results[ent_type]["type_error_count"] += 1 


def eval_per_type(pertype_results):
    print(
        f"{'TYPE':<20}"
        f"{'P':<10}"
        f"{'R':<10}"
        f"{'F1':<10}"
        f"{'EXACT':<10}"
        f"{'PARTIAL':<10}"
        f"{'FP':<10}"
        f"{'FN':<10}"
    )

    print("-" * 80)

    for ent_type in pertype_results:
        counts = pertype_results[ent_type]
        exact_count = counts["exact_count"]
        partial_count = counts["partial_count"]
        fp = counts["fp"]
        fn = counts["fn"]
        tp = exact_count + partial_count
        precision = calculate_precision(tp,fp)
        recall = calculate_recall(tp,fn)
        f1 = calculate_f1(precision,recall)
        print(
            f"{ent_type:<20}"
            f"{precision:<10.3f}"
            f"{recall:<10.3f}"
            f"{f1:<10.3f}"
            f"{exact_count:<10}"
            f"{partial_count:<10}"
            f"{fp:<10}"
            f"{fn:<10}"
        )
    
 

GTRUTH_JSON_PATH = 'src/eval/sample/gtruth.json'
REGEX_ENTS_PATH = 'src/eval/regex_ents.json'
regex_ents_data = load_json(PROPERTY_ENTITES_JSON)
regex_ents = process_regex_ents(regex_ents_data, REGEX_ENTS_PATH)

gtruth_ents = load_json(GTRUTH_JSON_PATH)
match_results = {
    "exact_count": 0,
    "partial_count": 0,
    "type_error_count": 0,
    "fp":0,
    "fn":0,
}
per_type_results = {}

regex_dict = build_node_dict(regex_ents)
gt_dict = build_node_dict(gtruth_ents)


# cả 2 tập chung node id 
for node_id in NODE_IDS:
    eval_one_node(node_id,regex_dict,gt_dict,match_results,per_type_results)

# eval_overall(match_results)
# eval_per_type(per_type_results)



def debug_only_fp(regex_dict, gt_dict):

    debug_fp = []

    for node_id in NODE_IDS:

        if node_id not in regex_dict or node_id not in gt_dict:
            continue

        r_node = regex_dict[node_id]
        gt_node = gt_dict[node_id]

        r_ents = r_node["entities"]
        gt_ents = gt_node["entities"]

        gt_matched = [False] * len(gt_ents)

        for r_ent in r_ents:

            found_match = False

            for i, gt_ent in enumerate(gt_ents):

                if gt_matched[i]:
                    continue

                match_type = eval_ent_match(r_ent, gt_ent)

                if match_type != "no_match":
                    gt_matched[i] = True
                    found_match = True
                    break

            # predict có nhưng gt không có
            if not found_match:

                debug_fp.append({
                    "node_id": node_id,
                    "pred_text": r_ent["text"],
                    "pred_type": r_ent["type"]
                })

    print('\n')
    print("PREDICT CO NHUNG GTRUTH KHONG CO (FP)")
    print('\n')

    for item in debug_fp:
        print(item)

    print("\nTOTAL FP:", len(debug_fp))
# debug_only_fp(regex_dict, gt_dict)
eval_overall(match_results)
eval_per_type(per_type_results)

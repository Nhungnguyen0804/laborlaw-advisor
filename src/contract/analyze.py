from src.models.gem import analyze_contract_item
from google import genai

WEIGHTS = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


def calc_score(issues):
    score = sum(WEIGHTS[i["severity"]] for i in issues)
    if score == 0:
        return score, "LOW"
    elif score <= 4:
        return score, "MEDIUM"
    else:
        return score, "HIGH"
    
import random
import time
def analyze_contract(client, contract_items):
    all_results = []
    total_score = 0
    
    # client = genai.Client(api_key=key)
    for item in contract_items:
        try:
            issues = analyze_contract_item(client,item)
        except Exception as e:
            err_str = str(e)
            is_503 = "503" in err_str or "UNAVAILABLE" in err_str
            if is_503:
                wait = 2 * 10 + random.uniform(0, 3)
                print(f"  503 retry, chờ {wait} giây")
                time.sleep(wait)
            else:
                raise
            continue
        score, risk = calc_score(issues)
        all_results.append({
            "id": item["id"],
            "issues": issues,
            "score": score,
            "risk": risk
        })
        total_score += score
        
    # Score tổng thể
    if all_results:
        avg_score = total_score / len(all_results)
    else: 
        avg_score = 0
    if avg_score == 0:
        overall_risk = "LOW"
    elif avg_score <= 4:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "HIGH"

    return all_results, total_score, overall_risk
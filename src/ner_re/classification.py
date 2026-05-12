import re
# match với các title article 

TYPES = {
    "PROHIBITION": r"hành vi bị nghiêm cấm|không được|cấm",
    "RIGHTS": r"quyền của|được quyền|có quyền",
    "OBLIGATION": r"nghĩa vụ|phải|có trách nhiệm",
    "CONDITION": r"điều kiện sau|yêu cầu|tiêu chuẩn|tiêu chí",
    "PROCEDURE": r"trình tự|thủ tục|quy trình|bước",
    "PENALTY": r"xử phạt|chế tài|vi phạm",
    "DEFINITION": r"giải thích từ ngữ|giải thích|hiểu là|được hiểu|hiểu như sau",
}

def match_type(text):
    if not text:
        return None

    for key, pattern in TYPES.items():
        if re.search(pattern, text, re.IGNORECASE):
            return key

    return None

def classify_article(article_title):
    key = match_type(article_title)
    return f"{key}_ARTICLE" if key else None

'''
# test 

print('1=>',classify_article('Các hành vi bị nghiêm cấm trong lĩnh vực lao động'))
print('2=>',classify_article('Quyền và nghĩa vụ của người lao động'))

# 1=> PROHIBITION_ARTICLE
2=> OBLIGATION_ARTICLE
'''
def classify_clause(clause_content):
    key = match_type(clause_content)
    clause_type = f"{key}_CLAUSE" if key else None

    if clause_content:
        is_header = bool(re.search(r":\s*$", clause_content.strip()))
    else:
        is_header = False

    return clause_type, is_header


print(classify_clause("Tổ chức, cá nhân không được thực hiện các hành vi sau:"))
# => ('PROHIBITION_CLAUSE', True)




def classify_point(point_content):
    key = match_type(point_content)
    point_type = f"{key}_POINT" if key else None
    

    
    # True nếu point là header cho sub-point (kết thúc bằng ':' hoặc có cụm 'sau đây:')
    if point_content:
        is_header = bool(
            re.search(r"sau đây\s*:", point_content, re.IGNORECASE) or
            re.search(r":\s*$", point_content.strip())
        )
    else:
        is_header = False
    return point_type, is_header

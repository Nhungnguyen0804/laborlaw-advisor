import re
# match với các title article 

TYPES = {
    "PROHIBITION": r"hành vi bị nghiêm cấm|không được|cấm",
    "RIGHT": r"quyền của|được quyền|có quyền",
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

#===============================================================================
# Token dùng để nối/gom entities, không mang semantic meaning
#  ";", ":", "thì", "mà", "của", "tại", "theo", "về", "cho", "với", "đối với"
CONNECT_TOKENS = {",", "và", "hoặc", "cùng với", "đồng thời"}
# Các từ cho confidence cao

def is_connect_token(text):
    # token kiểu nối/gom entity thì bỏ qua, không tạo edge
    if not text:
        return False

    text = text.strip().lower()
    return text in CONNECT_TOKENS



EDGE_PATTERNS = {
    "defines": [  
        "là", "là việc", "là người", "bao gồm", 
        "được hiểu là", "có nghĩa là", "nghĩa là",
        "được thành lập", "thành lập" ,

        'không trên cơ sở',
    ],
    
    "regulates": [ 
        "quy định", "quy định chi tiết", "điều chỉnh", 
        "hướng dẫn", "ban hành",
        "quyết định", "quyết định cụ thể" ,
        'bằng lời nói',
    ],
    
    "applies_to": [

        "áp dụng cho", "áp dụng đối với", "dành cho", 
        "thuộc", "trong phạm vi",
        'trong một số',
        'theo danh mục do',
        'cho',
    ],
    
    "requires": [  
        "phải", "có trách nhiệm", "có nghĩa vụ", 
        "được yêu cầu", "bắt buộc", "cần phải", "cần",
        "bổ nhiệm", "được bổ nhiệm", "ủy quyền", "được ủy quyền",
        "chỉ định", "cử người", "đề cử" ,
        'mới ít nhất',

        'thì gửi','chỉ được','chỉ',
    ],
    
    "prohibits": [
        "không được", "cấm", "nghiêm cấm", 
        "không được phép", "bị cấm"
    ],
    
    "enables": [  
        "có quyền", "được phép", "được hưởng", 
        "được tự do", "được ưu tiên", "được nghỉ", "được tạm ứng",
        'có hưởng', 'có thể',
    ],
    
    "has_condition": [  
        'theo tỷ lệ tương ứng với',
        "nếu", "khi", "trường hợp", "trong trường hợp", 
        "sau khi", "trước khi",
        "có hiệu lực áp dụng", "có hiệu lực từ" ,

        'phù hợp với trình độ, kỹ năng nghề trên cơ sở',
        'trong thời gian',
        'có thời hạn',
        'và có đủ',
        'và có',
        'mà có từ đủ','mà có',
    ],
    
    "has_exception": [ 
        "trừ", "ngoại trừ", "không áp dụng", "loại trừ",
        'ngoài những','chưa kể',
    ],
    
    "cites": [
        "tại điều", "theo điều", "quy định tại", 
        "theo quy định tại", "căn cứ"
    ],
    
    "involves": [  
        "liên quan đến", "bao gồm các bên",
        "tham gia", "tham gia vào", "trực tiếp tham gia"  ,
        'việc tập huấn, nâng cao năng lực chuyên môn của',
        'có liên quan trực tiếp đến',
        'của địa phương và đưa vào',
        'trong việc đại diện',
        'chịu trách nhiệm trước',
        'đang tiến hành',
        'ghi trong',
        'sử dụng',
        'giữa','hưởng',
        'của','bằng',

        'thống nhất',
    ],

    'modifies':['việc tiếp tục thực hiện, sửa đổi, bổ sung'],
    "results_in": [  
        "dẫn đến", "làm phát sinh", "trở thành", "phát sinh",
        "gây ra", "có hiệu lực", "hết hiệu lực", 
        "chấm dứt", "vô hiệu", "bị", "chấm dứt sự tồn tại"
    ],
    
    "has_purpose": [  
        "nhằm mục đích", "nhằm", 
        "để tìm kiếm", "để xử lý", "để hướng dẫn", 
        "để thực hiện", "để bảo vệ", "để phát triển", 
        "để nâng cao", "để giải quyết", "để đào tạo",
        "để bồi dưỡng", "để công nhận", "để tham gia",
        "để đưa", "để tính", 'để',
    ],
    # vi phạm 
    'violates':['có hành vi',
                'thì tùy theo tính chất, mức độ vi phạm',
                'thì tùy theo mức độ vi phạm',
                'chưa phù hợp với',
                ],
    'supports':['trên cơ sở khuyến nghị của hội đồng'],
    'not': ['không'],
    'lack':['chưa có'],
    # fallback
    'related_to':[
        "thông qua", "qua", "bằng cách",

        "về", "về các vấn đề",

        "được xác lập", "được xác lập qua",

        "với sự hỗ trợ của", "kết hợp với",

        "hoặc thông qua", "được",
    ]
}

remove_edge_types =["a)"]
def classify_action_to_edge_type(action_text):


    if action_text is None:
        return None

    if action_text == "":
        return None

    if is_connect_token(action_text):
        return None

    cleaned_text = action_text.strip().lower()

    for edge_type in EDGE_PATTERNS:

        pattern_list = EDGE_PATTERNS[edge_type]

        for pattern in pattern_list:

            if pattern in cleaned_text:
                if edge_type in remove_edge_types:
                    return None
                return edge_type

    return None
from copy import deepcopy

def normalize_entities(raw_entities):

    normalized_entities = deepcopy(raw_entities)

    for node in normalized_entities:

        new_entities = []

        for ent in node["entities"]:

            normalized_ent = normalize_entity(ent)
            if normalized_ent is not None:
                new_entities.append(normalized_ent)

        node["entities"] = new_entities

    return normalized_entities

def normalize_entity(ent):

    ent_type = ent["type"]

    if ent_type == "LEGAL_ROLE":
        return normalize_role(ent)
    elif ent_type == "TIME_PERIOD":
        return normalize_time(ent)
    elif ent_type == 'LEGAL_CONCEPT':
        return normalize_concept(ent)
    elif ent_type == 'PROCEDURE':
        return normalize_procedure(ent)
    elif ent_type == 'LEGAL_REF':
        return normalize_ref(ent)
    elif ent_type == 'CONDITION':
        return normalize_condition(ent)
    elif ent_type == 'PROHIBITION':
        return normalize_prohibition(ent)
    elif ent_type == 'RIGHT':
        return normalize_right(ent)
    elif ent_type == 'OBLIGATION':
        return normalize_obligation(ent)
    elif ent_type == 'PENALTY':
        return normalize_penalty(ent)
    elif ent_type == 'ACTION':
        return normalize_action(ent)
    return ent



def update_span(ent, new_text):

    old_text = ent["text"].lower()
    new_text =new_text.lower()

    # Tìm vị trí của new_text trong old_text
    newtext_startpos = old_text.find(new_text)
    if newtext_startpos == -1:
        return ent
    
    start = ent["span"][0] + newtext_startpos
    end = start + len(new_text)

    ent["text"] = new_text
    ent["span"] = [start, end]

    return ent


def normalize_role(ent):
    text = ent["text"]
    text = text.lower()

    # abcd thì xyz => abc
    text = text.split('thì')[0].strip();
    text = text.split('chỉ được')[0].strip();
    text = text.split('không được')[0].strip();

    remove_last_word = [';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    return update_span(ent, text)


def normalize_time(ent):
    text = ent["text"]
    text_lower = text.lower()
    CUT_WORDS = [
        'phát hiện ra',
        'xảy ra',
        'ban hành',
        'nhận được',
        'bắt đầu',
        'được thành lập',
        'có hiệu lực',
        'hết',
        'ban trọng tài',
        'hợp đồng',
        'báo cho',
        'hòa giải',
        'chấm dứt',
        'được thông qua',
        'lập biên bản',
        'bị xử lý'
    ]

    time_keywords = ['kể từ ngày', 'kể từ thời điểm']
    # Tìm marker trước
    found_keyword = None
    start_time_pos = -1
    # Tìm keyword xuất hiện trong text
    for keyword in time_keywords:
        index = text_lower.find(keyword)
        if index != -1:
            found_keyword = keyword
            start_time_pos = index + len(keyword)  # vị trí sau keyword
            break
    
    if found_keyword is None:
        return update_span(ent, text) # update span trên text chưa lower
    
    # Chỉ xét phần sau marker
    after_keyword = text_lower[start_time_pos:]
    cut_pos = len(after_keyword)
    for w in CUT_WORDS:
        index = after_keyword.find(w)
        if index != -1 and index < cut_pos:
            cut_pos = index # vi tri cut_word start
    result = text[:start_time_pos + cut_pos].strip()

    remove_last_word = [';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    return update_span(ent, result)



def normalize_concept(ent):
    text = ent["text"]
    text = text.lower()

    # abcd thì xyz => abc
    text = text.split(';')[0].strip();
    text = text.split('nếu')[0].strip();
    text = text.split('nhưng')[0].strip();

    remove_last_word = [';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    return update_span(ent, text)


def normalize_procedure(ent):
    text = ent["text"]
    text = text.lower()


    text = text.split('theo quy định')[0].strip();
    text = text.split('quy định tại')[0].strip();
    text = text.split('của bộ luật này')[0].strip();
    text = text.split('mà')[0].strip();
    text = text.split('trừ')[0].strip();
    text = text.split('được thực hiện theo')[0].strip();
    text = text.split('có quyền')[0].strip();
    text = text.split('sau khi')[0].strip();
    text = text.split('trước khi')[0].strip();
    text = text.split('trong trường hợp')[0].strip();
    text = text.split('nếu')[0].strip();

    remove_last_word = [';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    return update_span(ent, text)


# text = text.split('nếu')[0].strip();

def normalize_ref(ent):
    text = ent["text"]
    text = text.lower()


    remove_text = [
        'căn cứ điều kiện',
        "các chương trình",'các khoản tiền', 'các khoản chi', 'các khoản bảo hiểm','các điều kiện',
        'chương trình',
        'điều kiện','điều chỉnh', 'điều phối','điều trị','điều động','điều ước quốc tế', 'điều của',
        'mục do','mục nghề','mục nơi', 'mục quy định','mục tại','mục đích', 'mục công việc',
        'điều dưỡng', 'điều khiển', 'điều hành',
        'khoản tiền','khoản cá nhân',
        'điểm bắt đầu', 'điểm chấm dứt','điểm của nguyên liệu','điểm hoạt động', 'điểm kinh doanh',
        'điểm làm việc','điểm nghỉ hưu','điểm trả lương','điểm và các điều kiện','điểm và cách thức','điểm về cơ thể','điểm đăng ký','điểm có',
        
    ]

    for prefix in remove_text:
        if text.startswith(prefix):
            return None
    # cắt text sau các keyword này
    #  ,  phai co nhu sau nghỉ việc 
    cut_text_after = [
        # phẩy 
        ', trừ trường hợp', ', người sử dụng lao động', ', người lao động', ', ban trọng tài',', các bên',
        ', lao động',', nếu',', cơ quan',', khi',', hòa giải viên', ', hai bên', ', hội đồng',', tử hình',
        ', cứ mỗi năm',
    
        'làm ảnh hưởng đến', 'căn cứ vào','hết hiệu lực','và có đủ','hoặc tổ chức','hoặc yêu cầu',
        'nghỉ việc có đủ',
        'và các quyền lợi khác','và trợ cấp', 'và cách thức',
        'hoặc trường hợp',
        'có quyền sau', 'có trách nhiệm','có hiệu lực',
        'phải có', 'như sau', 'hết hạn','trở thành','thống nhất','người sử dụng',
        'chỉ được','còn được','được quốc hội',
        'đối với','bình đẳng về',

        'nếu','khi','thì','để','mà','đã','nhưng','từ', 

    ]

    for keyword in cut_text_after:
        text = text.split(keyword)[0].strip()

    remove_last_word = [';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()

    return update_span(ent, text)


def normalize_condition(ent):
    text = ent["text"]
    text = text.lower()

    cut_text_after = ['; trường hợp','; trong thời gian', 'quy định tại','theo quy định', ]
    for keyword in cut_text_after:
        text = text.split(keyword)[0].strip()
    remove_first_word = [',','trừ trường hợp']
    remove_last_word = ['thì',';']
    text = text.lstrip()
    for keyword in remove_first_word:
        if text.startswith(keyword):
            text = text[len(keyword):].lstrip() 
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    return update_span(ent, text)


def normalize_prohibition(ent):
    text = ent["text"]
    text = text.lower()


    remove_text = ['bộ trưởng']

    for prefix in remove_text:
        if text.startswith(prefix):
            return None
    cut_text_after = ['theo quy định',', trừ trường hợp', 'quy định tại','theo danh mục', 'nếu',]
    for keyword in cut_text_after:
        text = text.split(keyword)[0].strip()
    
    remove_last_word = [';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    
    return update_span(ent, text)

def normalize_right(ent):
    text = ent["text"]
    text = text.lower()


    cut_text_after = [', trừ trường hợp','trong trường hợp', 'theo danh mục',
                      'theo trình tự','theo quy định','quy định tại', 'nếu']
    for keyword in cut_text_after:
        text = text.split(keyword)[0].strip()
    
    remove_last_word = [';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()

    return update_span(ent, text)

def normalize_obligation(ent):
    text = ent["text"]
    text = text.lower()

    cut_text_after = [', trừ trường hợp','trong trường hợp', 'theo danh mục',
                      'theo trình tự','theo quy định','quy định tại', 'nếu', 'khi','thì']
    for keyword in cut_text_after:
        text = text.split(keyword)[0].strip()

    remove_last_word = ['thì','hoặc',';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    return update_span(ent, text)

def normalize_penalty(ent):
    text = ent["text"]
    text = text.lower()

    cut_text_after = [', trừ trường hợp','trong trường hợp', 'theo danh mục', 'theo bản án',
                      'theo trình tự','theo quy định','quy định tại', 'nếu','thì']
    for keyword in cut_text_after:
        text = text.split(keyword)[0].strip()

    remove_last_word = ['hoặc',';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    return update_span(ent, text)

def normalize_action(ent):
    text = ent["text"]
    text = text.lower()

    cut_text_after = [', trừ trường hợp','trong trường hợp', 'theo danh mục', 'theo bản án',
                      'theo trình tự','theo quy định','quy định tại', 'nếu','thì']
    for keyword in cut_text_after:
        text = text.split(keyword)[0].strip()

    remove_last_word = [';']
    text = text.lstrip()
    for keyword in remove_last_word:
        if text.endswith(keyword):
            text = text[:-len(keyword)].rstrip()
    return update_span(ent, text)





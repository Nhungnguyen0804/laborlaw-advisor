import re 
from src.utils.file_utils import load_json, save_json
from src.utils.paths import LABORLAW_CHUNKS_JSON,LABORLAW_ENTITIES_JSON
PATTERNS = { 
    
    # partern dài -> ngắn
    "SUBJECT": [
        # tổ chức đại diện người lao động
        # to chuc dai dien ngươi su dung lao dong
        r"tổ chức\s+đại diện\s+người\s+(?:sử dụng\s+)?lao\s+động",
        # nguoi lao dong nuoc ngoai
        r"người\s+lao\s+động\s+nước\s+ngoài",
        # nguoi su dung lao dong
        r"người\s+(?:sử dụng\s+)?lao\s+động",
        # nguoi hoc nghe 
        # nguoi tap nghe
        r"người\s+(?:học|tập)\s+nghề",
        
        r"(?:doanh nghiệp|công ty|tổ chức|cơ quan)",

        # ho gia dinh 
        # ca nhan
        r"(?:hộ\s+gia\s+đình|cá\s+nhân)",
        # ben thue lao dong
        # ben cho thue lao dong 
        r"bên\s+(?:thuê|cho\s+thuê)\s+lao\s+động",

        # chu lao dong
        # chu su dung lao dong
        r"(?:chủ|chủ sử dụng)\s+lao\s+động",  
    ],
     # Có quyền, được phép
    "RIGHT": [  
        r"có\s+quyền",
        r"được\s+(?:phép|quyền|hưởng|nghỉ|từ\s+chối)",
        r"được\s+\w+",  # được tham gia, được yêu cầu
    ],

    # Phải, có nghĩa vụ
    "OBLIGATION": [
        r"có\s+(?:trách\s+nhiệm|nghĩa\s+vụ)",
        r"phải\s+(?:\w+\s+){0,3}\w+",  # phải đóng BHXH, phải trả lương
        r"bắt\s+buộc\s+phải",
    ],
    
    "PROHIBITION": [
        r"không\s+được\s+(?:\w+\s+){0,3}\w+",
        r"cấm\s+(?:không\s+)?(?:\w+\s+){0,3}\w+",
        r"nghiêm\s+cấm",
    ],
    
    "TIME_PERIOD": [
        r"\d+\s*(?:ngày\s+làm\s+việc|ngày|tháng|năm|giờ)",
        r"(?:hàng|hằng)\s+(?:ngày|tuần|tháng|năm)",
        r"(?:trong\s+vòng|tối\s+đa|tối\s+thiểu|ít\s+nhất)\s+\d+\s*(?:ngày|tháng|năm)",
        r"trước\s+(?:ngày|khi)\s+\d+",  # trước ngày 15, trước khi 30 ngày
    ],
    
    "CONDITION": [
        r"trong\s+trường\s+hợp\s+(?:\w+\s+){0,5}\w+",
        r"trừ\s+(?:trường\s+hợp|khi)",
        r"(?:nếu|khi)\s+(?:\w+\s+){1,5}",
        r"với\s+điều\s+kiện\s+(?:\w+\s+){0,3}",
    ],
    
    "ACTION": [  
        r"ký\s+kết\s+(?:hợp\s+đồng)?",
        r"chấm\s+dứt\s+(?:hợp\s+đồng)?",
        r"đơn\s+phương\s+chấm\s+dứt",
        r"bồi\s+thường\s+(?:thiệt\s+hại)?",
        r"thanh\s+toán\s+(?:\w+)?",
        r"chi\s+trả\s+(?:lương|trợ\s+cấp)?",
    ],
    #đối tượng pháp lý
    "OBJECT": [  
        r"hợp\s+đồng\s+lao\s+động",
        r"hợp\s+đồng\s+(?:xác\s+định|không\s+xác\s+định)\s+thời\s+hạn",
        r"(?:tiền\s+)?lương\s+(?:tối\s+thiểu)?",
        r"bảo\s+hiểm\s+(?:xã\s+hội|y\s+tế|thất\s+nghiệp)",
        r"thời\s+giờ\s+làm\s+việc",
        r"nghỉ\s+(?:phép\s+năm|thai\s+sản|ốm\s+đau)",
    ],
    
    "PENALTY": [
        r"bị\s+(?:xử\s+phạt|sa\s+thải|kỷ\s+luật)",
        r"xử\s+phạt\s+vi\s+phạm\s+hành\s+chính",
        r"bồi\s+thường\s+thiệt\s+hại",
        r"truy\s+cứu\s+trách\s+nhiệm\s+hình\s+sự",
    ],
}


# compile tat ca cac pattern 
COMPILED = {}

for entity_type, pattern_list in PATTERNS.items():
    compiled_list = []

    for pattern in pattern_list:
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
        compiled_list.append(compiled_pattern)

    COMPILED[entity_type] = compiled_list

# print(COMPILED)

def sort_key(item):
    start = item["start"]
    end = item["end"]
    length = end - start  # độ dài entity
    priority_length = -length # dài hơn thì độ ưu tiên cao hơn 
    return (start, priority_length)

def extract_entities(text: str) -> list[dict]:
    matches = []

    #Tìm tất cả match từ các pattern
    for entity_type, compiled_patterns in COMPILED.items():
        for pattern in compiled_patterns:
            for match in pattern.finditer(text):
                entity_info = {
                    "entity_type": entity_type,
                    "text": match.group().strip(),
                    "start": match.start(),
                    "end": match.end(),
                }
                matches.append(entity_info)


    # với mỗi item trong matches gọi sort_key(item) => lấy kết quả trả về để đem đi so sánh
    # sort theo start tăng dần, nếu trùng thì entity dài hơn trước
    matches.sort(key=sort_key)

    # loại bỏ các entity bị overlap 
    filtered_entities = []
    last_end = 0

    for item in matches:
        # lay vi tri start, end cua tung item 
        start_pos = item["start"]
        end_pos = item["end"]

        # nếu entity này bắt đầu sau vị trí entity cũ end -> k bị chồng nhau 
        if start_pos >= last_end :
            filtered_entities.append(item)
            last_end = end_pos # update vị trí end mới 

    return filtered_entities


# chạy extract
# gom entity theo loại
def get_entity_summary(chunk):
    content = chunk.get("content", "")
    entities = extract_entities(content)

    entity_summary = {}

    for e in entities:
        e_type = e["entity_type"]
        e_text = e["text"]

        if e_type not in entity_summary:
            entity_summary[e_type] = []
        
        entity_summary[e_type].append(e_text)
        

    return {
        "chunk_id": chunk["chunk_id"],
        "chunk_type": chunk["chunk_type"],
        "content": content,
        "entities": entities,
        "entity_summary": entity_summary,
        "entity_count": len(entities),
    }


def run_ner():

    data = load_json(LABORLAW_CHUNKS_JSON)
    output_path = LABORLAW_ENTITIES_JSON
    chunks = data["chunks"] 

    results = []
    for chunk in chunks:
        result = get_entity_summary(chunk)
        results.append(result)


    # tổng số entity của toàn bộ văn bản 
    total_entities = 0
    for r in results:
        total_entities += r["entity_count"]
    print(f"Xử lý {len(results)} chunk, tìm được {total_entities} entities")

    # Lưu output
    output = {
        "metadata": data.get("metadata", {}),
        "total_chunks_processed": len(results),
        "total_entities_found": total_entities,
        "results": results,
    }
    save_json(output, output_path)
    return results

run_ner()


from google import genai
import json

def build_prompt(content, context):
    prompt = f'''
        Bạn là một hệ thống hỗ trợ rà soát hợp đồng lao động.

        [ĐIỀU KHOẢN HỢP ĐỒNG]

        {content}

        [QUY ĐỊNH PHÁP LUẬT LIÊN QUAN]

        {context}

        NHIỆM VỤ

        Đối chiếu điều khoản hợp đồng với các quy định pháp luật được cung cấp.

        Chỉ xác định các nội dung có căn cứ rõ ràng cho thấy:

        - Trái với quy định pháp luật.
        - Hạn chế hoặc làm giảm quyền lợi của người lao động so với quy định.
        - Thiếu nghĩa vụ hoặc trách nhiệm mà pháp luật yêu cầu.
        - Đặt ra điều kiện không phù hợp với quy định pháp luật.

        YÊU CẦU

        - Chỉ sử dụng thông tin xuất hiện trong phần [QUY ĐỊNH PHÁP LUẬT LIÊN QUAN].
        - Không sử dụng kiến thức bên ngoài.
        - Không suy đoán.
        - Không đưa ra nhận định nếu không tìm thấy căn cứ rõ ràng trong các quy định được cung cấp.
        - Mỗi vấn đề chỉ tạo một issue.
        - reason phải ngắn gọn, tối đa một câu.
        - law_reference phải ghi đúng điều/khoản xuất hiện trong dữ liệu pháp luật được cung cấp.
        - severity chỉ được phép là HIGH, MEDIUM hoặc LOW.

        Định nghĩa mức độ nghiêm trọng (biến severity):

        HIGH:
        - Có dấu hiệu vi phạm trực tiếp quy định pháp luật.
        - Làm mất hoặc hạn chế đáng kể quyền lợi của người lao động.

        MEDIUM:
        - Có khả năng không phù hợp với quy định pháp luật.
        - Quy định không rõ ràng hoặc có nguy cơ dẫn đến áp dụng trái luật.

        LOW:
        - Có điểm chưa nhất quán, chưa đầy đủ hoặc cần làm rõ thêm.
        - Chưa đủ căn cứ để kết luận vi phạm trực tiếp.

        CHỈ TRẢ VỀ JSON HỢP LỆ.

        KHÔNG markdown.
        KHÔNG giải thích.
        KHÔNG thêm văn bản ngoài JSON.
        KHÔNG thêm thuộc tính ngoài schema.

        {{
        "issues": [
            {{
            "severity": "HIGH",
            "reason": "Mô tả ngắn gọn",
            "law_reference": "Điều X Khoản Y"
            }}
        ]
        }}

        Nếu không phát hiện vấn đề:

        {{
        "issues": []
        }}
    '''
    return prompt


import time
MODEL_1 ='gemini-3.5-flash'
# MODEL_2 = 'gemini-2.5-flash'
def analyze_contract_item(client, item):
    prompt = build_prompt(item["content"], item["related_law"])
    time.sleep(5) 
    response = client.models.generate_content(
        model= MODEL_1,
        contents=prompt,
        config={"response_mime_type": "application/json", "automatic_function_calling": { "maximum_remote_calls": 64}}
    )
    data = json.loads(response.text)
    issues = data.get("issues", [])
    return issues

def make_client(api_key):
    return genai.Client(api_key=api_key)



from src.utils.file_utils import load_json

contract_items = load_json('src/contract/contract_v1.json')


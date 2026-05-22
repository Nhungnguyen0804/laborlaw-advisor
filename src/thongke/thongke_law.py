import json
# đọc file json
input_path = 'data/processed/laborlaw_structure.json'
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)
chapters = data["structure"]["chapters"]

# thống kê
tong_chuong = len(chapters)
tong_dieu = 0
tong_khoan = 0
tong_diem = 0
tong_muc = 0
for chapter in chapters:
    # có thể có sections
    sections = chapter.get("sections", [])
    tong_muc += len(sections)
    if "sections" in chapter:
        sections = chapter["sections"]
        for section in sections:
            articles = section.get("articles", [])
            tong_dieu += len(articles)
            for article in articles:
                clauses = article.get("clauses")
                if clauses:
                    tong_khoan += len(clauses)
                    for clause in clauses:
                        points = clause.get("points")
                        if points:
                            tong_diem += len(points)
                    
    if "articles" in chapter:
        articles = chapter["articles"]
        tong_dieu += len(articles)
        for article in articles:
            clauses = article.get("clauses")
            if clauses:
                tong_khoan += len(clauses)
                for clause in clauses:
                    points = clause.get("points")
                    if points:
                        tong_diem += len(points)



# print kết quả
print("Tên luật:", data["law_name"])
print("Mã luật:", data["law_code"])

print("Tổng số chương:", tong_chuong)
print("Tổng số mục:", tong_muc)
print("Tổng số điều:", tong_dieu)
print("Tổng số khoản:", tong_khoan)
print("Tổng số điểm:", tong_diem)


'''

Tên luật: BỘ LUẬT LAO ĐỘNG
Mã luật: 45/2019/QH14
Tổng số chương: 17
Tổng số điều: 220
Tổng số khoản: 638
Tổng số điểm: 267

'''
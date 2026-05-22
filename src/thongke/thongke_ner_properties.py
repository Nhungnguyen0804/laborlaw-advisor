import json

input_path = 'src/ner_re/raw_entities.json'
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Tổng số document/node
tong_node = len(data)
print("Tong so node:", tong_node)


tong_entity = 0
# Đếm theo loại entity
dem_loai = {}
# Entity dài nhất
entity_dai_nhat = ""
# Entity xuất hiện nhiều nhất
tan_suat_entity = {}

for node in data:
    entities = node.get("entities", [])
    tong_entity += len(entities)
    for entity in entities:
        text = entity.get("text", "")
        loai = entity.get("type", "Khong ro")
        # Đếm theo loại
        if loai not in dem_loai:
            dem_loai[loai] = 0
        dem_loai[loai] += 1
        # Entity dài nhất
        if len(text) > len(entity_dai_nhat):
            entity_dai_nhat = text
        # Đếm tần suất entity
        if text not in tan_suat_entity:
            tan_suat_entity[text] = 0
        tan_suat_entity[text] += 1


print("\nTong so entity:", tong_entity)

# Trung bình entity mỗi node
if tong_node > 0:
    tb = tong_entity / tong_node
    print("Trung binh entity moi node:", round(tb, 2))


print('thong ke theo type')
for key in dem_loai:
    print(key, ":", dem_loai[key])


print('ent dai nhat')
print(entity_dai_nhat)
print("So ky tu:", len(entity_dai_nhat))


print('top ent xuat hien nhieu')
# Sắp xếp giảm dần
sap_xep = sorted(
    tan_suat_entity.items(),
    key=lambda x: x[1],
    reverse=True
)

top = 10
for i in range(top):
    if i < len(sap_xep):
        ten = sap_xep[i][0]
        so_lan = sap_xep[i][1]
        print(i + 1, ".", ten, "-", so_lan, "lan")


max_entity = 0
node_max = None

for node in data:
    entities = node.get("entities", [])
    if len(entities) > max_entity:
        max_entity = len(entities)
        node_max = node

print('node dieu luat max ent')
print("So entity:", max_entity)

# In thử nội dung
if node_max is not None:

    if "text" in node_max:
        print("\nNoi dung:")
        print(node_max["text"][:500])



entity_trung = 0

for value in tan_suat_entity.values():

    if value > 1:
        entity_trung += 1

print("So entity trung lap:", entity_trung)

print('5 ent first')
count = 0
for node in data:
    entities = node.get("entities", [])
    for entity in entities:
        print(entity)
        count += 1
        if count == 5:
            break
    if count == 5:
        break
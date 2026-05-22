import json
input_path = 'src/ner_re/raw_entities.json'
# Đọc file JSON
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Tổng số node
print("Tong so node:", len(data))
# Đếm tổng entity
tong_entity = 0
# Đếm theo type
dem_type = {}
for node in data:
    entities = node.get("entities", [])
    tong_entity += len(entities)
    for entity in entities:
        entity_type = entity.get("type")
        if entity_type not in dem_type:
            dem_type[entity_type] = 0
        dem_type[entity_type] += 1

print("Tong so entity:", tong_entity)
print("\nThong ke theo type:")
for key, value in dem_type.items():
    print(key, ":", value)

# In thử 5 entity đầu tiên
print("\n5 entity dau tien:")
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

'''
Tong so node: 905
Tong so entity: 9658

Thong ke theo type:
LEGAL_ROLE : 2893
LEGAL_CONCEPT : 1913
RIGHT : 264
CONDITION : 879
ACTION : 1342
LEGAL_REF : 1079
OBLIGATION : 535
PROHIBITION : 172
TIME_PERIOD : 425
PENALTY : 72
PROCEDURE : 84

5 entity dau tien:
{'type': 'LEGAL_ROLE', 'text': 'người làm việc không có quan hệ lao động', 'span': [50, 90], 'source': 'pattern'}
{'type': 'LEGAL_ROLE', 'text': 'người làm việc', 'span': [50, 64], 'source': 'pattern'}
{'type': 'LEGAL_ROLE', 'text': 'người học nghề', 'span': [16, 30], 'source': 'pattern'}
{'type': 'LEGAL_ROLE', 'text': 'người tập nghề', 'span': [32, 46], 'source': 'pattern'}
{'type': 'LEGAL_ROLE', 'text': 'Người lao động', 'span': [0, 14], 'source': 'pattern'}

'''
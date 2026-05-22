import json
input_path = 'src/ner_re/normalized_entities.json'
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

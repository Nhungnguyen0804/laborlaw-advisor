import json
import random
import csv
from src.utils.file_utils import load_json
from src.utils.paths import LABORLAW_ENTITIES_JSON,EMPTY_NER_GROUND_TRUTH_CSV 

output_file = EMPTY_NER_GROUND_TRUTH_CSV
data = load_json(LABORLAW_ENTITIES_JSON)
chunks = data["results"] # get list chunk có entity từ ner

chunks_no_entity_list = []
chunks_with_entity_list = []

for chunk in chunks:
    entity_count = chunk['entity_count']
    if entity_count == 0:
        chunks_no_entity_list.append(chunk)
    else:
        chunks_with_entity_list.append(chunk)


print(f"Chunk có entity: {len(chunks_with_entity_list)}")
print(f"Chunk ko có entity: {len(chunks_no_entity_list)}")

ent_num = len(chunks_with_entity_list)/ len(chunks)
no_ent_num = len(chunks_no_entity_list)/ len(chunks)
print(f"tỷ lệ có entity: {ent_num}") 
print(f"tỷ lệ ko có entity: {no_ent_num}")  

chunks_ent_num = round(ent_num * 100)
chunks_no_ent_num = round(no_ent_num * 100)

print('Tỷ lệ: ',chunks_ent_num,' và ',chunks_no_ent_num)
random_chunks_ent = random.sample(chunks_with_entity_list, chunks_ent_num)
random_chunks_no_ent = random.sample(chunks_no_entity_list, chunks_no_ent_num)

random_chunks = random_chunks_ent + random_chunks_no_ent 

# shuffle để trộn 
random.shuffle(random_chunks)

# utf-8-sig => utf-8-sig
with open(output_file, "w", newline="", encoding="utf-8-sig") as csvfile:
    writer = csv.writer(csvfile)

    # ghi header 
    writer.writerow(["chunk_id", "chunk_text", "entity_type", "entity_text"])

    for chunk in random_chunks:
        chunk_id = chunk["chunk_id"]
        chunk_text = chunk["content"]

        writer.writerow([chunk_id, chunk_text, "", ""])
    
    print("Đã tạo file csv tại:", output_file)


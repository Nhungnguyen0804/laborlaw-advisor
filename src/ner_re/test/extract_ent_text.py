import json
from pathlib import Path


def export_entity_texts(
    input_file,
    entity_type,
    output_dir="src/ner_re/test"
):
 

    # Đọc file JSON
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Dùng set để dedup
    entity_texts = set()

    # Duyệt toàn bộ records
    for item in data:
        entities = item.get("entities", [])

        for ent in entities:
            if ent.get("type") == entity_type:
                text = ent.get("text", "").strip()

                if text:
                    entity_texts.add(text)

    # Sort cho dễ nhìn
    entity_texts = sorted(entity_texts)

    # Tạo thư mục nếu chưa có
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # File output
    output_file = Path(output_dir) / f"entity_{entity_type}.txt"

    # Ghi file
    with open(output_file, "w", encoding="utf-8") as f:
        for text in entity_texts:
            f.write(text + "\n")

    print(f"Saved {len(entity_texts)} entities to: {output_file}")

input = 'src/ner_re/normalized_entities.json'
export_entity_texts(input_file=input,entity_type="LEGAL_ROLE")
export_entity_texts(input_file=input,entity_type="TIME_PERIOD")
export_entity_texts(input_file=input,entity_type="LEGAL_CONCEPT")
export_entity_texts(input_file=input,entity_type="PROCEDURE")
export_entity_texts(input_file=input,entity_type="LEGAL_REF")
export_entity_texts(input_file=input,entity_type="PROHIBITION")
export_entity_texts(input_file=input,entity_type="RIGHT")
export_entity_texts(input_file=input,entity_type="OBLIGATION")
export_entity_texts(input_file=input,entity_type="PENALTY")
export_entity_texts(input_file=input,entity_type="ACTION")


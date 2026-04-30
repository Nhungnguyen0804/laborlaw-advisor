import re
from src.utils.file_utils import load_json, save_json
from src.utils.paths import LABORLAW_CHUNKS_JSON
import unicodedata
from src.ner.patterns import PATTERNS

COMPILED = {}
for entity_type, pattern_list in PATTERNS.items():
    COMPILED[entity_type] = [re.compile(p, re.IGNORECASE) for p in pattern_list]


def remove_leading_thi(text):
    text = text.lstrip()
    if text.startswith("thì"):
        return text[3:].lstrip()
    return text


def clean_condition(text):
    text = text.strip()
    if text.endswith("thì"):
        return text[:-3].rstrip()
    return text


def clean_right(text):
    text = text.strip()
    text = remove_leading_thi(text)
    if text.startswith('quy định'):
        return None

    stop_patterns = [
        r'\s+trước\s+và\s+sau\s+khi\b',
        r'\s+trừ\s+trường\s+hợp\b',
        r'\s+trường\s+hợp\b',
        r'\s+nhưng\b',
        r'\s+(trước\s+khi|sau\s+khi)\b',
        r'\s+khi\b',
    ]

    earliest_pos = len(text)
    for pattern in stop_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()

    cleaned = text[:earliest_pos].strip()
    cleaned = cleaned.rstrip('.,')
    return cleaned if cleaned else None


def clean_obligation(text):
    text = text.strip()
    text = remove_leading_thi(text)
    if text.startswith('quy định'):
        return None

    stop_patterns = [
        r'\s+trước\s+và\s+sau\s+khi\b',
        r'\s+trừ\s+trường\s+hợp\b',
        r'\s+(?:hoặc\s+về\s+)?trường\s+hợp\b',
        r'\s+nhưng\b',
        r'\s+(trước\s+khi|sau\s+khi)\b',
        r'\s+khi\b',
    ]

    earliest_pos = len(text)
    for pattern in stop_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()

    cleaned = text[:earliest_pos].strip()
    cleaned = cleaned.rstrip('.,')
    return cleaned if cleaned else None


def clean_prohibition(text):
    text = text.strip()
    text = remove_leading_thi(text)
    if text.startswith('quy định'):
        return None

    stop_patterns = [
        r'\s+trước\s+và\s+sau\s+khi\b',
        r'\s+trừ\s+trường\s+hợp\b',
        r'\s+(?:hoặc\s+về\s+)?trường\s+hợp\b',
        r'\s+nhưng\b',
        r'\s+(trước\s+khi|sau\s+khi)\b',
        r'\s+khi\b',
    ]

    earliest_pos = len(text)
    for pattern in stop_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()

    cleaned = text[:earliest_pos].strip()
    cleaned = cleaned.rstrip('.,')
    return cleaned if cleaned else None


CLEANERS = {
    "LEGAL_ROLE": lambda x: x,
    "RIGHT": clean_right,
    "OBLIGATION": clean_obligation,
    "PROHIBITION": clean_prohibition,
    "TIME_PERIOD": lambda x: x,
    "CONDITION": clean_condition,
    "ACTION": lambda x: x,
    "LEGAL_CONCEPT": lambda x: x,
    "EVENT": lambda x: x,
    "PENALTY": lambda x: x.strip().rstrip(','),
    "PURPOSE": lambda x: x,
    "PROCEDURE": lambda x: x,
    "LEGAL_REF": lambda x: x,
}


def extract_entity(text: str, entity_type: str, pattern) -> list[dict]:
    matches = []
    cleaner = CLEANERS.get(entity_type, lambda x: x.strip())

    for match in pattern.finditer(text):
        matched_text = match.group().strip()
        cleaned_text = cleaner(matched_text)

        if cleaned_text and match.start() != match.end():
            matches.append({
                "entity_type": entity_type,
                "text": cleaned_text,
                "start": match.start(),
                "end": match.end(),
            })

    return matches


def extract_entities(text: str) -> list[dict]:
    text = text.lower()
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'[\u00A0\u200B\u200C\u200D\uFEFF]', ' ', text)
    text = re.sub(r' +', ' ', text)

    all_matches = []

    for entity_type, compiled_patterns in COMPILED.items():
        for pattern in compiled_patterns:
            matches = extract_entity(text, entity_type, pattern)
            all_matches.extend(matches)

    return all_matches


def split_into_sentences(text: str) -> list[dict]:
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)

    parts = re.split(r'(?<!\d)\.(?!\d)|;', text)

    sentences = []
    sent_id = 0

    for part in parts:
        part = part.strip()
        part = re.sub(r'^\d+\.\s*', '', part)

        if not part or len(part) < 10:
            continue

        sentences.append({
            "sentence_id": f"s{sent_id}",
            "text": part,
            "start": text.find(part),
        })
        sent_id += 1

    return sentences


def extract_sentence_relations(sentence_text: str, sentence_entities: list[dict]) -> list[dict]:
    relations = []
    sorted_entities = sorted(sentence_entities, key=lambda x: x["start"])

    for i, e1 in enumerate(sorted_entities):
        for e2 in sorted_entities[i+1:]:
            if e2["start"] - e1["end"] > 80:
                break

            between_text = sentence_text[e1["end"]:e2["start"]].strip()

            relation_type = infer_relation_type(
                e1["entity_type"],
                e2["entity_type"],
                between_text
            )

            if relation_type:
                confidence = calculate_confidence(e1, e2, between_text)

                relations.append({
                    "subject": e1["text"],
                    "subject_type": e1["entity_type"],
                    "predicate": extract_predicate(between_text),
                    "object": e2["text"],
                    "object_type": e2["entity_type"],
                    "relation_type": relation_type,
                    "confidence": confidence
                })

    return relations


def infer_relation_type(type1: str, type2: str, between_text: str) -> str:
    between_lower = between_text.lower()

    if type1 == "LEGAL_ROLE" and type2 == "RIGHT":
        if any(word in between_lower for word in ["được", "có quyền", "được quyền"]):
            return "has_right"

    if type1 == "LEGAL_ROLE" and type2 == "OBLIGATION":
        if any(word in between_lower for word in ["phải", "có nghĩa vụ", "có trách nhiệm"]):
            return "has_obligation"

    if type1 == "LEGAL_ROLE" and type2 == "PROHIBITION":
        if any(word in between_lower for word in ["không được", "cấm"]):
            return "has_prohibition"

    if type1 == "CONDITION":
        if type2 in ["RIGHT", "OBLIGATION", "PROHIBITION"]:
            if "thì" in between_lower:
                return "triggers"

    if type1 == "TIME_PERIOD" and type2 == "ACTION":
        return "time_of_action"

    if type1 == "LEGAL_ROLE" and type2 == "PENALTY":
        if any(word in between_lower for word in ["bị", "chịu"]):
            return "receives_penalty"

    return None


def extract_predicate(between_text: str) -> str:
    between_lower = between_text.lower().strip()

    predicates = [
        "có quyền", "được quyền", "được",
        "phải", "có nghĩa vụ", "có trách nhiệm",
        "không được", "cấm",
        "bồi thường", "thanh toán", "chi trả",
        "thực hiện", "tuân thủ",
    ]

    for pred in predicates:
        if pred in between_lower:
            return pred

    return between_lower[:20]


def calculate_confidence(e1, e2, between_text):
    score = 0.5

    distance = e2["start"] - e1["end"]
    if distance < 20:
        score += 0.3
    elif distance < 50:
        score += 0.2

    keywords = ["được", "phải", "có", "bị", "thì"]
    if any(kw in between_text.lower() for kw in keywords):
        score += 0.2

    return min(score, 1.0)


def process_chunk(chunk):
    content = chunk.get("content", "")
    sentences = split_into_sentences(content)

    processed_sentences = []
    all_entities = []
    all_relations = []

    for sentence in sentences:
        sentence_text = sentence["text"]

        sentence_entities = extract_entities(sentence_text)
        sentence_relations = extract_sentence_relations(sentence_text, sentence_entities)

        processed_sentences.append({
            "sentence_id": sentence["sentence_id"],
            "text": sentence_text,
            "entities": sentence_entities,
            "entity_count": len(sentence_entities),
            "relations": sentence_relations,
            "relation_count": len(sentence_relations)
        })

        all_entities.extend(sentence_entities)
        all_relations.extend(sentence_relations)

    entity_summary = {}
    for e in all_entities:
        e_type = e["entity_type"]
        if e_type not in entity_summary:
            entity_summary[e_type] = []
        entity_summary[e_type].append(e["text"])

    return {
        "chunk_id": chunk["chunk_id"],
        "chunk_type": chunk["chunk_type"],
        "content": content,
        "sentences": processed_sentences,
        "entity_summary": entity_summary,
        "total_entities": len(all_entities),
        "total_relations": len(all_relations),
    }


def run_ner_re():
    data = load_json(LABORLAW_CHUNKS_JSON)
    chunks = data["chunks"]

    results = []
    for chunk in chunks:
        result = process_chunk(chunk)
        results.append(result)

    total_entities = sum(r["total_entities"] for r in results)
    total_relations = sum(r["total_relations"] for r in results)

    print(f"Processed {len(results)} chunks")
    print(f"Entities: {total_entities}")
    print(f"Relations: {total_relations}")

    output = {
        "metadata": data.get("metadata", {}),
        "total_chunks_processed": len(results),
        "total_entities_found": total_entities,
        "total_relations_found": total_relations,
        "results": results,
    }

    out_path = 'src/ner/ner_re.json'
    save_json(output, out_path)
    return results


if __name__ == "__main__":
    run_ner_re()
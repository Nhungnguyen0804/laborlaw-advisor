from pathlib import Path

ROOT_DIR =  Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
LABORLAW_PDF = RAW_DIR / "laborlaw.pdf"

# =====================================================================

PROCESSED_DIR = DATA_DIR / "processed"
LABORLAW_STRUCTURE_JSON = PROCESSED_DIR / 'laborlaw_structure.json'
LABORLAW_CHUNKS_JSON = PROCESSED_DIR / 'laborlaw_chunks.json'
LABORLAW_ENTITIES_JSON = PROCESSED_DIR / 'laborlaw_entities.json'
LABORLAW_ENTITIES_V1_JSON = PROCESSED_DIR / 'laborlaw_entities_v1.json'
EMB_JSON = PROCESSED_DIR / 'laborlaw_embeddings.json'

EMPTY_NER_GROUND_TRUTH_CSV = PROCESSED_DIR /'empty_ner_ground_truth.csv'
NER_GROUND_TRUTH_CSV = PROCESSED_DIR /'ner_ground_truth.csv'
# =====================================================================
SRC_DIR = ROOT_DIR / "src"
LABOR_LAW_DIR = RAW_DIR / "labor_law"

TEST_DIR = ROOT_DIR / "test"
TEST_DIR1 = ROOT_DIR / "test1"


NER_RE = SRC_DIR / "ner_re"
PROPERTY_ENTITES_JSON = NER_RE/ 'property_entities.json'
SPLIT_ENTS_JSON = NER_RE/ 'splited_entities.json'
STRUCTURAL_NODES_JSON = 'data/graph/structural_nodes.json'







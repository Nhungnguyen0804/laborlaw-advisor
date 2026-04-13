from pathlib import Path

ROOT_DIR =  Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
LABORLAW_PDF = RAW_DIR / "laborlaw.pdf"


PROCESSED_DIR = DATA_DIR / "processed"
LABORLAW_STRUCTURE_JSON = PROCESSED_DIR / 'laborlaw_structure.json'
LABORLAW_CHUNKS_JSON = PROCESSED_DIR / 'laborlaw_chunks.json'
SRC_DIR = ROOT_DIR / "src"
LABOR_LAW_DIR = RAW_DIR / "labor_law"

TEST_DIR = ROOT_DIR / "test"
TEST_DIR1 = ROOT_DIR / "test1"
# print('ROOT_DIR: ',ROOT_DIR)
# print('DATA_DIR: ',DATA_DIR)
# print('--RAW_DIR: ',RAW_DIR)
# print('--PROCESSED_DIR: ',PROCESSED_DIR)
# print('SRC_DIR: ',SRC_DIR)
# print('--LABOR_LAW_DIR: ',LABOR_LAW_DIR)
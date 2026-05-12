from src.utils.file_utils import load_json, save_json
from src.utils.paths import LABORLAW_CHUNKS_JSON, LABORLAW_STRUCTURE_JSON

def load_input():
    # chunk_data = load_json(LABORLAW_CHUNKS_JSON)
    law_data = load_json(LABORLAW_STRUCTURE_JSON)
    # chunks = chunk_data["chunks"]
    structure = law_data['structure']
    chapters = structure['chapters']

    # print(f"Tổng chunk đầu vào là: {len(chunks)} chunk")
    print(f"Tổng chapters đầu vào là: {len(chapters)} chapters")
    titles = extract_titles(chapters)
    save_to_txt(titles)
    return law_data,structure,chapters



def extract_titles(chapters):
    lines = []

    for chapter in chapters:
        # Dòng chương
        chapter_title = f"Chương {chapter.get('chapter_num')} {chapter.get('chapter_title')}"
        lines.append(chapter_title)

        # Case 1: có section
        if chapter.get("sections"):
            for section in chapter["sections"]:
                for article in section.get("articles", []):
                    line = f"Điều {article.get('article_num')} {article.get('article_title')}"
                    lines.append(line)

        # Case 2: không có section
        else:
            for article in chapter.get("articles", []):
                line = f"Điều {article.get('article_num')} {article.get('article_title')}"
                lines.append(line)

        # Ngăn cách chương
        lines.append("============")

    
    return lines

def save_to_txt(lines, path="src/ner_re/all_title.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


import json
import os
import datetime
from src.utils.paths import LABORLAW_STRUCTURE_JSON,TEST_DIR,LABORLAW_CHUNKS_JSON
from src.utils.file_utils import load_json

# chunk vb theo cau truc phan cap 

def build_context_metadata(law_code, law_name, chapter, section , article):
    # gom metadata của các cấp cha vào 1 dict 
    # cha gồm chuong, muc, dieu 
    return {
        'law_code': law_code,
        'law_name': law_name,
        'chapter_id': chapter['chapter_id'],
        'chapter_num': chapter['chapter_num'],
        'chapter_title': chapter['chapter_title'],
        # 'chapter_id': chapter['chapter_id'],
        # section có thể None 
        'section_id': section['section_id'] if section else None,
        'section_num': section['section_num'] if section else None,
        'section_title': section['section_title'] if section else None,
        'article_id': article['article_id'],
        'article_num': article['article_num'],
        'article_title': article['article_title'],
    }

def key_to_context_header(key):
    parts = []

    items = key.split("_")
    for item in items:
        if item.startswith("ch"):
            parts.append(f"Chương {item[2:]}")
        elif item.startswith("muc"):
            parts.append(f"Mục {item[3:]}")
        elif item.startswith("d"):
            parts.append(f"Điều {item[1:]}")
        elif item.startswith("k"):
            parts.append(f"Khoản {item[1:]}")
        elif len(item) == 1:  # điểm a, b, c
            parts.append(f"Điểm {item}")

    return ", ".join(parts) + ":"

def estimate_tokens(text):
    return len(text.split())  # dem so word 
def make_chunk(chunk_id, chunk_type, content, metadata):
    # str, str, str, dict
    # return dict 
    return {
        "chunk_id": chunk_id,
        "chunk_type": chunk_type,
        "content": content,
        "content_with_context": key_to_context_header(metadata['article_id']) + "\n" + content,
        "metadata": metadata,
        "token_estimate": estimate_tokens(content),
    }

def chunk_clause(clause, context_metadata, start_id):
    # dict dict int 
    # 1 khoản  có thể có 1 or N chunk
    # nếu points rỗng => 1 chunk từ clause content 
    #có points, clause content, vượt giới hạn token => tách từng điểm
    # nếu có point, clauses content , ko vượt ngưỡng => 1 chunk ko tách
    MAX_CLAUSE_TOKENS = 400 # khoản vượt ngưỡng này + có points => tách xuống điểm 

    if 'clause_content' in clause:
        content = clause['clause_content'].strip()
    else:
        content = ''

    if 'points' in clause:
        points = clause['points'] 
    else:
        points = []

    # bổ sung thêm metadata của khoản vào meta cha (copy từ meta cha)
    clause_metadata = context_metadata.copy()
    clause_metadata["clause_id"] = clause["clause_id"]
    clause_metadata["clause_num"] = clause["clause_num"]

    #  points rỗng || khoản có độ dài ngắn-> 1 chunk
    if not points or estimate_tokens(content) <= MAX_CLAUSE_TOKENS:
        return [
            make_chunk(
                chunk_id=f"chunk_{start_id:05d}",
                chunk_type="clause", # kiểu chunk là Khoản
                content=content,
                metadata=clause_metadata,
            )
        ]
    
    # khoản dài, có points => tách từng point 

    chunks =[]
    for index, point in enumerate(points):
        if 'point_content' in point:
            point_content = point['point_content']
        else: point_content = ''

        if not point_content: continue

        point_metadata = clause_metadata.copy()
        point_metadata["point_id"] = point["point_id"]
        point_metadata["point_label"] = point["point_label"]

        chunk_dict = make_chunk(
            chunk_id=f"chunk_{start_id + index:05d}",
            chunk_type="point", # kiểu chunk là điểm
            content=point_content,
            metadata=point_metadata,
        )
        chunks.append(chunk_dict)
            
    # tat ca points rỗng content nên mảng chunks rỗng => giữ nguyen clause 
    if not chunks:
       return [
            make_chunk(
                chunk_id=f"chunk_{start_id:05d}",
                chunk_type="clause", 
                content=content,
                metadata=clause_metadata,
            )
        ]

    return chunks

def chunk_article(article, context_metadata, start_id):
    # article la Dict {id, num, ... , clauses: []}
    # context metadata la dict , 
    # id bắt đầu để đánh số chunk 

    # 1 điều có thể có 1 or N chunk
    # nếu clauses null => Điều ko có khoản, article_title chứa cả content -> 1 chunk
    # nếu clauses ko null => chunk từng khoản 

    if 'clauses' in article:
        clauses = article['clauses']
    else:
        clauses = []

    if not clauses:
        return [
            make_chunk(
                chunk_id=f"chunk_{start_id:05d}", # 00123
                chunk_type="full_article",
                content=article["article_title"],
                metadata=context_metadata,
            )
        ]
    
    # neu có khoản -> chunk từng khoản 
    chunks = []
    temp_index = start_id
    for clause in clauses:
        clause_chunks = chunk_clause(clause, context_metadata, temp_index)
        chunks.extend(clause_chunks)
        temp_index += len(clause_chunks)

    return chunks



def build_chunks(json_path):
    data = load_json(json_path)
    if data is None:
        print('Load json fail!')
    
    law_code = data['law_code']
    law_name = data['law_name']
    chapters = data['structure']['chapters']


    all_chunks = []
    next_chunk_id = 1 #  id tiếp theo sẽ dùng  

    for chapter in chapters:
        # check chương có mục ko 
        if 'sections' in chapter:
            sections = chapter['sections']
        else:
            sections = []

        if sections: # chương có mục nên ko rỗng
            for section in sections:
                # check section có các điều ko 
                if 'articles' in section:
                    articles = section['articles']
                else:
                    articles = [] # rỗng 
                    print('articles trong section rỗng !')

                for article in articles:
                    # print(article)
                    context_metadata = build_context_metadata(law_code, law_name, chapter, section, article)
                    article_chunks = chunk_article(article, context_metadata,next_chunk_id)
                    all_chunks.extend(article_chunks)

                    # update chunk id làm start 
                    next_chunk_id += len(article_chunks)

                    # context_header = key_to_context_header(context_metadata['article_id'])
                    # with open(TEST_DIR /"context_meta.txt", "a", encoding="utf-8") as f:
                    #     article_id = article['article_id']
                    #     f.write(f'{article_id} --> {context_metadata}\n')
                    
                    # with open(TEST_DIR /"context_header.txt", "a", encoding="utf-8") as f:
                    #     article_id = article['article_id']
                    #     f.write(f'{article_id} --> {context_header}\n')

        else: # chương ko có mục: chương -> điều

            # check chương có điều ko ? 
            if 'articles' in chapter:
                articles = chapter['articles']
            else:
                articles = []
                print('articles trong chapter rỗng !')

            for article in articles: 
                context_metadata = build_context_metadata(law_code, law_name, chapter, None, article)
                article_chunks = chunk_article(article, context_metadata, next_chunk_id)
                all_chunks.extend(article_chunks)
                next_chunk_id+=len(article_chunks)
                # context_header = key_to_context_header(context_metadata['article_id'])
                # with open(TEST_DIR /"context_meta.txt", "a", encoding="utf-8") as f:
                #     article_id = article['article_id']
                #     f.write(f'{article_id} --> {context_metadata}\n')

                # with open(TEST_DIR /"context_header.txt", "a", encoding="utf-8") as f:
                #         article_id = article['article_id']
                #         f.write(f'{article_id} --> {context_header}\n')

    law_metadata = {"law_code": law_code, "law_name": law_name}
    return all_chunks,law_metadata

def save_chunks(chunks,law_metadata, output_path):
    output_data = {
    'metadata': {
        **law_metadata, # bỏ {} cua dict
        'total_chunks': len(chunks)
    },
    'chunks': chunks,    
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print('Done chunking!')
    
def run_chunk():
    law_structure_json_path = LABORLAW_STRUCTURE_JSON
    chunks_path = LABORLAW_CHUNKS_JSON
    if not os.path.exists(law_structure_json_path):
        print(f'Khong tim thay file: {law_structure_json_path}')
        return
    
    chunks,law_metadata = build_chunks(law_structure_json_path)
    save_chunks(chunks, law_metadata, chunks_path)

run_chunk()
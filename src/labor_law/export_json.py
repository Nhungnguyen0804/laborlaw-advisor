import time
from tqdm import tqdm
import json

from src.labor_law.parser import read_pdf_pdfplumber,remove_pdf_headers,format_newlines_after_dot,parse_legal_document, parse_general_metadata

def count_law_elements(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"{data['law_name']}")
    print(f"Cơ quan ban hành: {data['issuing_authority']}")

    total_chapters = len(data['structure']['chapters'])
    total_sections = 0  # Mục
    total_articles = 0
    total_clauses = 0
    total_points = 0

    chapter_ids = []
    section_ids = []
    article_ids = []
    clause_ids = []
    point_ids = []

    # theo chuong 
    chapter_stats = []
    for chapter in data['structure']['chapters']:
        chapter_number = chapter.get('chapter_number', 'N/A')
        chapter_id = chapter.get('chapter_id', 'N/A')
        chapter_ids.append(chapter_id)

        chapter_articles = 0
        chapter_sections = 0 
        chapter_clauses = 0
        chapter_points = 0
        if 'sections' in chapter:
            
            chapter_sections = len(chapter['sections'])
            total_sections += chapter_sections
            
            for section in chapter['sections']:
                section_id = section.get('section_id', 'N/A')
                section_ids.append(section_id)
                if 'articles' in section:
                    for article in section['articles']:
                        article_id = article.get('article_id', 'N/A')
                        article_ids.append(article_id)
                        chapter_articles += 1
                        
                        if 'clauses' in article:
                            chapter_clauses += len(article['clauses'])
                            for clause in article['clauses']:
                                clause_id = clause.get('clause_id', 'N/A')
                                clause_ids.append(clause_id)
                                if 'points' in clause:
                                    chapter_points += len(clause['points'])
                                    for point in clause['points']:
                                        point_id = point.get('point_id', 'N/A')
                                        point_ids.append(point_id)
        
        elif 'articles' in chapter:
            # Trường hợp KHÔNG có Mục - trực tiếp có Điều
            for article in chapter['articles']:
                article_id = article.get('article_id', 'N/A')
                article_ids.append(article_id)
                chapter_articles += 1
                
                if 'clauses' in article:
                    chapter_clauses += len(article['clauses'])
                    for clause in article['clauses']:
                        clause_id = clause.get('clause_id', 'N/A')
                        clause_ids.append(clause_id)
                        if 'points' in clause:
                            chapter_points += len(clause['points'])
                            for point in clause['points']:
                                point_id = point.get('point_id', 'N/A')
                                point_ids.append(point_id)
        
            
        total_articles += chapter_articles
        total_clauses += chapter_clauses
        total_points += chapter_points
        
        chapter_stats.append({
            'chapter_id': chapter['chapter_id'],
            'chapter_number': chapter['chapter_number'],
            'sections': chapter_sections,
            'articles': chapter_articles,
            'clauses': chapter_clauses,
            'points': chapter_points
        })

    print(f"Tổng số chương: {total_chapters}")
    print(f"Tổng số Mục: {total_sections}")
    print(f"Tổng số điều: {total_articles}")
    print(f"Tổng số khoản: {total_clauses}")
    print(f"Tổng số điểm: {total_points}")

     # In danh sách ID
    print("DANH SÁCH CÁC ID:\n")
    
    # print(f"Chapter IDs ({len(chapter_ids)}):")
    # for idx, cid in enumerate(chapter_ids, 1):
    #     print(f"  {idx}. {cid}")
    
    # if section_ids:
    #     print(f"\nSection IDs ({len(section_ids)}):")
    #     for idx, sid in enumerate(section_ids, 1):
    #         print(f"  {idx}. {sid}")
    
    print(f"\nArticle IDs ({len(article_ids)}):")
    for idx, aid in enumerate(article_ids, 1):
        print(f"  {idx}. {aid}")
    
    # if clause_ids:
    #     print(f"\nClause IDs ({len(clause_ids)}):")
    #     for idx, clid in enumerate(clause_ids, 1):
    #         print(f"  {idx}. {clid}")
    
    # if point_ids:
    #     print(f"\nPoint IDs ({len(point_ids)}):")
    #     for idx, pid in enumerate(point_ids, 1):
    #         print(f"  {idx}. {pid}")
            
def run_parse():
    INPUT_FILE_PATH = 'src/data/raw/laborlaw.pdf'
    OUTPUT_FILE_PATH = 'src/data/processed/all_laborlaw.json'
    pdf_path = INPUT_FILE_PATH
    
    try:
        start_time = time.time()
        # Đọc PDF
        pages = read_pdf_pdfplumber(pdf_path)
        print(f"Đọc được {len(pages)} trang ({time.time() - start_time:.2f}s)")
        
        # Xử lý text
        step_time = time.time()
        full_text = '\n'.join(pages)
        full_text = remove_pdf_headers(full_text)
        processed_lines = format_newlines_after_dot(full_text)
        print(f"Xử lý xong {len(processed_lines)} dòng ({time.time() - step_time:.2f}s)")
        
        # Parse cấu trúc
        step_time = time.time()
        metadata = parse_general_metadata(pdf_path)
        structure = parse_legal_document(processed_lines)
        output_res = {
            **metadata,   # unpack metadata
            "structure": structure
        }
        print(f"Parse hoàn tất ({time.time() - step_time:.2f}s)")
        
        # Lưu ra file JSON
        step_time = time.time()
        output_file = OUTPUT_FILE_PATH
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_res, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu kết quả vào: {output_file} ({time.time() - step_time:.2f}s)")

        total_time = time.time() - start_time
        print(f"===> Tổng thời gian: {total_time:.2f}s ({total_time/60:.2f} phút)")
        

        # in ra thành phần
        count_law_elements(OUTPUT_FILE_PATH)
    except FileNotFoundError:
        print("Không tìm thấy file PDF!")
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()

run_parse()

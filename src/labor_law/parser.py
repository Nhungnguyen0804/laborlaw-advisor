
import re
from PyPDF2 import PdfReader
import unicodedata
import pdfplumber
import time
import json
from pathlib import Path
from src.labor_law.extractor import extract_sections
from src.utils.paths import TEST_DIR,LABORLAW_PDF,LABORLAW_STRUCTURE_JSON

# preprocessing 

def remove_pdf_headers(full_text):
    # tách theo enter
    lines = full_text.split('\n')

    # clean header 
    removed_header = "CÔNG BÁO/Số 993 + 994/Ngày 26-12-2019"
    cleaned_lines = []
    for line in lines:
        if removed_header not in line:
            cleaned_lines.append(line)
    
    # ghép lại enter  
    return '\n'.join(cleaned_lines)

def format_newlines_after_dot(full_text):
    #Xử lý xuống dòng, chỉ giữ xuống dòng sau dấu chấm hoặc từ khóa cấu trúc
    lines = full_text.split('\n')
    processed_lines = []
    temp_line = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Kiểm tra từ khóa cấu trúc
        starts_with_structure = (
            line.startswith(('Chương ', 'Mục ')) or
            re.match(r'^\d+\.\s', line) or
            re.match(r'^Điều\s+\d+\.', line)  # phải có dấu chấm sau số như:Điều 54. 
             # lọc đi trường hợp "Điều 169 của..."
        )
        if temp_line:
            if temp_line.endswith('.') or starts_with_structure:
                processed_lines.append(temp_line)
                temp_line = line
            else:
                temp_line += ' ' + line
        else:
            temp_line = line

    if temp_line:
        processed_lines.append(temp_line)

    return processed_lines

# normalize ko dấu + lower
def normalize_to_noformat_text(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.lower()
    text = text.replace('đ', 'd')
    return text



def roman_to_int(roman):
    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev = 0
    for ch in reversed(roman):
        value = roman_map.get(ch, 0)
        if value < prev:
            total -= value
        else:
            total += value
            prev = value
    return total

def read_first_page_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        if pdf.pages:
            return pdf.pages[0].extract_text() or ""
    return ""

def read_pdf_pdfplumber(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text = unicodedata.normalize('NFC', text)
                pages.append(text)
    return pages


def read_multiple_pdfs(pdf_dir):
    #Loop qua folder PDF
    pdf_dir = Path(pdf_dir)
    results = {}
    for pdf_file in pdf_dir.glob("*.pdf"):
        pages = read_pdf_pdfplumber(pdf_file)
        results[pdf_file.name] = '\n'.join(pages)
    return results

# parser
# metadata là thông tin chung của bộ luật 
def parse_general_metadata(first_line):
    # print('first line chứa metadata: ',first_line)
    '''
    first line chứa metadata:  QUỐC HỘI CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc lập - Tự do - Hạnh phúc Bộ luật số: 45/2019/QH14 BỘ LUẬT LAO ĐỘNG Căn cứ Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam; Quốc hội ban hành Bộ luật Lao động.
    '''
    law_code = re.search(r'Bộ luật số:\s*([\w/]+)', first_line)
    # print(law_code) #<re.Match object; span=(72, 96), match='Bộ luật số: 45/2019/QH14'>
    # print(law_code.group(1)) #45/2019/QH14
    if law_code:
        law_code = law_code.group(1)
    else:
        law_code = None
    lower_line = first_line.lower()
    law_name = "BỘ LUẬT LAO ĐỘNG"
    issued = re.search(r'([^;.]+ban hành[^.]+\.)', first_line)
    issued = issued.group(1).strip() if issued else None
    # print(issued)

    metadata = {
        "law_code": law_code,
        "law_name": law_name,
        "issued": issued
    }

    return metadata


def parse_chapters(processed_lines):
 
    structure = {"chapters": []}
    # CHƯƠNG
    chapter_pattern = re.compile(r"Chương\s+([IVXLCDM]+)")
    # Trích xuất chương
    chapter_blocks  = extract_sections(processed_lines, chapter_pattern, "Chương") # list 

    chapter_no_section = []

    for sentences in chapter_blocks:
        # chapter_block -> list 
        
        origin_chapter_title = sentences[0]
        roman_chapter = re.findall(chapter_pattern, origin_chapter_title)
            
        if not roman_chapter:
            continue
        chapter_roman = roman_chapter[0]
        chapter_num = roman_to_int(chapter_roman)
        chapter_id = f'ch{chapter_num}'
        # sub loại bỏ phần chapter_pattern
        chapter_title = chapter_pattern.sub("", origin_chapter_title).strip()

        # print(origin_chapter_title)
        # print(chapter_id)
        # print(chapter_num)
        # print(chapter_roman)
        # print(chapter_title)

        chapter_obj = {
            'chapter_id': chapter_id,
            'chapter_num': chapter_num,
            'chapter_roman': chapter_roman,
            'chapter_title': chapter_title,
            'orgin_chapter': origin_chapter_title,
        }
        
        # parse mục trước, nếu k có mới parse điều 

        # section là mục 
        sections = parse_sections(sentences, chapter_obj['chapter_id'],chapter_no_section)
        

        if sections:
            # có mục , điều nằm trong mục
            chapter_obj['sections'] = sections
        else:
            # k có mục => parse điều
            articles = parse_articles(sentences, chapter_obj['chapter_id'])
            chapter_obj['articles'] = articles
        # print('số chapter ko có mục: ', len(chapter_no_section), '-->' , chapter_no_section)
        structure["chapters"].append(chapter_obj)
    return structure


#Mục 
def parse_sections(chapter_lines,chapter_id,chapter_no_section):
 
    # Thử tìm mục
    section_pattern = re.compile(r"Mục\s+(\d+)")
    section_blocks = extract_sections(chapter_lines,section_pattern, "Mục ")
    
    # with open(TEST_DIR /"test_muc.txt", "a", encoding="utf-8") as f:
    #     for item in section_blocks:
    #         f.write(f"{chapter_id} --> sections = {item}\n")
    if not section_blocks:
        # print(f'{chapter_id} ko có Mục!')
        chapter_no_section.append(chapter_id)
        return []  # Chương này không có mục thì rỗng
    
    sections = []
    
    for sentences in section_blocks:
        # sentences mảng các câu 
        origin_section_title = sentences[0]
        # print(origin_section_title)
        section_number = re.findall(section_pattern, origin_section_title) # ['1']
        if not section_number:
            continue   
        section_num = section_number[0]
        # print(section_num)

     
  
        section_title = section_pattern.sub("", origin_section_title).strip()
        section_id = f'{chapter_id}_muc{section_num}'

        # print(section_id)
        # print(section_title)
        
        section_obj = {
            'section_id': section_id,
            'section_num': section_num,
            'section_title': section_title,
            'origin_section': origin_section_title
        }
    
        # Parse điều từ mục này, 1: để bỏ đi line Mục 1,2,3 ... 
        articles = parse_articles(sentences[1:],section_obj['section_id'])
        section_obj['articles'] = articles
        sections.append(section_obj)
    
    return sections


def parse_articles(lines,parent_id):

    articles = []
    article_pattern = re.compile(r"Điều\s+(\d+)")
    article_blocks  = extract_sections(lines, article_pattern,'Điều ')
    
    for sentences in article_blocks :
        origin_article = sentences[0]
        # print(origin_article)
        # bỏ qua nếu line k bắt đầu là Điều 
        if not origin_article.strip().startswith('Điều '):
            continue
        article_number = re.findall(article_pattern, origin_article)
        if not article_number:
            continue
        article_num = article_number[0]
        article_id = f'{parent_id}_d{article_num}'
        article_title = article_pattern.sub('',origin_article).strip()
        # title đang bị: . textttt  => replace '. ' ở đầu câu thành ''
        article_title = re.sub(r'^\.\s*', '', article_title)
        # print(article_num, article_id, '-->' , article_title)

        article_obj = {
            'article_id': article_id,
            'article_num': article_num,
            'article_title': article_title,
            'origin_article': origin_article,
            'clauses': parse_clauses(sentences,article_id) # parse khoản 
        }

        articles.append(article_obj)
   
    return articles
     

def parse_clauses(lines,article_id):
    len_lines = len(lines)
    if len_lines == 1:
        print(f'điều {article_id} ko có khoản !')
        return None # 1 câu là điều r
    else:
        # bỏ dòng đầu đi vì là title của điều r 
        clauses_lines = lines[1:]
        clauses =[]
        clause_pattern = re.compile(r"^(\d+)\.\s+(.*)")
        point_pattern = re.compile(r"^([a-zđ]\))\s+(.*)") # lọc extra line 
        clause_blocks = extract_sections(clauses_lines,clause_pattern , "")
    
        # with open(TEST_DIR /"test_khoan.txt", "a", encoding="utf-8") as f:
        #     f.write(f"{article_id} ---> {len(clause_blocks)}\n")
        #     for block in clause_blocks:
        #         for item in block:
        #             f.write(f"{item}\n")
           
        for sentences in clause_blocks:
            if not sentences:
                continue
        
            origin_clause = sentences[0]
            match = clause_pattern.match(origin_clause)
            if not match:
                continue

            clause_num = match.group(1)
            clause_content = match.group(2).strip()
            clause_id = f'{article_id}_k{clause_num}'

            extra_lines = sentences[1:]
            # lọc các dòng điểm a), b) khỏi extra line trc khi gộp vào full content 
            non_point_lines = [l for l in extra_lines if not point_pattern.match(l)]
            full_content = clause_content
            if non_point_lines:
                full_content = clause_content + ' ' + ' '.join(non_point_lines)
            full_content = full_content.strip()
          
            clause_obj = {
                'clause_id': clause_id,
                'clause_num': clause_num,
                'clause_content': full_content,
                'origin_clause': origin_clause,
                'points': parse_points(sentences, clause_id)  
            }

            clauses.append(clause_obj)
        return clauses
        

def parse_points(lines, clause_id):
    """Parse các điểm a), b), c)... trong một khoản"""
    point_pattern = re.compile(r"^([a-zđ]\))\s+(.*)")
    if len(lines) <= 1: # content chứa a b c chung 1 dòng
        candidates = re.split(r'(?<!\w)(?=[a-zđ]\)\s)', lines[0]) # lấy dòng first, chia thành list, [a) ... , b) ... , c) ... ]
    else:
        candidates = lines[1:] # khoản nhiều dòng thì bỏ dòng đầu là title 

    # lọc dòng là point 
    sub_lines = []

    for l in candidates:
        l_clean = l.strip()
        if point_pattern.match(l_clean): # check match với a) b) c) 
            sub_lines.append(l_clean)

    if not sub_lines:
        return None

    points = []
    for line  in sub_lines:
        match = point_pattern.match(line)
        if not match:
            continue

        point_label = match.group(1)           # "a)"
        point_content = match.group(2).strip() # nội dung
        point_id = f'{clause_id}_{point_label[0]}'  # "ch1_d5_k1_a"

        points.append({
            'point_id': point_id,
            'point_label': point_label,
            'point_content': point_content,
            'origin_point': line,
        })


    return points if points else None
  


def run_parse():
    pdf_path = LABORLAW_PDF
    output_file = LABORLAW_STRUCTURE_JSON

    print('đọc pdf, tách line theo enter, gộp line theo dấu chấm-------------------------------------------')
    pages = read_pdf_pdfplumber(pdf_path)
    print(f"Đọc được {len(pages)} trang")

    full_text = '\n'.join(pages)
    full_text = remove_pdf_headers(full_text)
    processed_lines = format_newlines_after_dot(full_text)

    print(f"Tổng {len(processed_lines)} dòng")
    # print(f"5 line đầu tiên:")
    # # print(processed_lines[:5])
    # for index,line in enumerate(processed_lines[:5]):
    #     print(index+ 1, ' --> ',line)

    '''
    1  -->  QUỐC HỘI CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM Độc lập - Tự do - Hạnh phúc Bộ luật số: 45/2019/QH14 BỘ LUẬT LAO ĐỘNG Căn cứ Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam; Quốc hội ban hành Bộ luật Lao động.
    2  -->  Chương I NHỮNG QUY ĐỊNH CHUNG
    3  -->  Điều 1. Phạm vi điều chỉnh Bộ luật Lao động quy định tiêu chuẩn lao động; quyền, nghĩa vụ, trách nhiệm của người lao động, người sử dụng lao động, tổ chức đại diện người lao động tại cơ sở, tổ chức đại diện người sử dụng lao động trong quan hệ lao động và các quan hệ khác liên quan trực tiếp đến quan hệ lao động; quản lý nhà nước về lao động.
    4  -->  Điều 2. Đối tượng áp dụng
    5  -->  1. Người lao động, người học nghề, người tập nghề và người làm việc không có quan hệ lao động.
    '''
    print('parse cấu trúc ---------------------------------------')

    metadata = parse_general_metadata(processed_lines[0]) # dòng đầu tiên (line 1) chứa metadata
    # print('metadata: ',metadata, '--> type: ', type(metadata))

    # print('type processed_line',type(processed_lines))
    structure = parse_chapters(processed_lines)
    
    output_res = {
        **metadata,   # đưa thuộc tính thành cùng cấp structure
        "structure": structure
    }

    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_res, f, ensure_ascii=False, indent=2)
    print(f"Đã lưu kết quả vào: {output_file}" )
    

run_parse()

def thongke(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        structure = json.load(f)

    print(f"Luật: {structure.get('law_name')}")
    print(f"Mã: {structure.get('law_code')}")
    print(f"Ban hành: {structure.get('issued')}")

    total_chapters = 0
    total_sections = 0
    total_articles = 0
    total_clauses  = 0
    total_points   = 0
    chapter_stats  = []

    for chapter in structure['structure']['chapters']:
        total_chapters += 1
        ch_sections = 0
        ch_articles = 0
        ch_clauses  = 0
        ch_points   = 0

        # Gom tất cả điều cần xử lý vào một list
        articles = []
        if chapter.get('sections'):
            for section in chapter['sections']:
                ch_sections += 1
                articles.extend(section.get('articles') or [])
        else:
            articles.extend(chapter.get('articles') or [])

        for article in articles:
            ch_articles += 1
            for clause in (article.get('clauses') or []):
                if not isinstance(clause, dict):
                    continue
                ch_clauses += 1
                for point in (clause.get('points') or []):
                    if isinstance(point, dict):
                        ch_points += 1

        total_sections += ch_sections
        total_articles += ch_articles
        total_clauses  += ch_clauses
        total_points   += ch_points

        chapter_stats.append({
            'so': chapter.get('chapter_num'),
            'ten': chapter.get('chapter_title', '')[:40],
            'muc': ch_sections,
            'dieu': ch_articles,
            'khoan': ch_clauses,
            'diem': ch_points,
        })
    print("Chuong:", total_chapters)
    print("Muc:", total_sections)
    print("Dieu:", total_articles)
    print("Khoan:", total_clauses)
    print("Diem:", total_points)
thongke(LABORLAW_STRUCTURE_JSON)

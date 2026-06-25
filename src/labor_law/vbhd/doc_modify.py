import re
RAW_DOC_MODIFY_KEYWORDS = [
    "thay thế",
    "hết hiệu lực",
    "không còn hiệu lực",
    "bãi bỏ",
    "hủy bỏ",
]

VAN_BAN_SO_HIEU_PATTERN = r'\d{1,5}[/-]\d{4}[/-][a-zà-ỹ0-9-]+'

DOC_TYPE_PATTERN = (
    r'(luật|nghị quyết|nghị định|thông tư|quyết định|pháp lệnh|bộ luật)'
)

SO_HIEU_PATTERN = r'\d{1,5}[/-]\d{4}[/-][a-zà-ỹ0-9-]+'

FULL_DOC_REF_PATTERN = (
    rf'{DOC_TYPE_PATTERN}'
    rf'(?:\s+[a-zà-ỹ\s]+?)?'
    rf'\s+số\s+({SO_HIEU_PATTERN})'
)


def extract_doc_references(line):
    results = []

    for match in re.finditer(
        FULL_DOC_REF_PATTERN,
        line,
        re.IGNORECASE
    ):
        doc_type = match.group(1).strip()
        so_hieu = match.group(2).strip()

        full_match = match.group(0).strip()

        doc_name = full_match

        doc_name = re.sub(
            rf'^{doc_type}\s*',
            '',
            doc_name,
            flags=re.IGNORECASE
        )

        doc_name = re.sub(
            rf'\s*số\s+{re.escape(so_hieu)}$',
            '',
            doc_name,
            flags=re.IGNORECASE
        )

        doc_name = doc_name.strip()

        results.append({
            "doc_type": doc_type,
            "doc_name": doc_name if doc_name else None,
            "so_hieu": so_hieu,
            "raw": full_match,
        })

    return results

def extract_raw_doc_modify(lines):
    candidates = []

    for line in lines:
        line = line.lower()

        has_keyword = any(
            keyword in line
            for keyword in RAW_DOC_MODIFY_KEYWORDS
        )

        if not has_keyword:
            continue

        if re.search(VAN_BAN_SO_HIEU_PATTERN, line):
            candidates.append(line)

    return candidates


PARTIAL_MARKERS = [
    "một số điều",
    "một số khoản",
    "một số điểm",
    "một số cụm từ",
    "một số nội dung",
    "một số quy định",
]

FULL_END_MARKERS = [
    "hết hiệu lực",
    "không còn hiệu lực",
    "hết hiệu lực toàn bộ",
]

EXCEPTION_MARKERS = [
    "trừ trường hợp quy định tại",
    "trừ quy định tại",
]

def classify_doc_modify(line):
    is_full = any(
        marker in line
        for marker in FULL_END_MARKERS
    )

    is_partial = any(
        marker in line
        for marker in PARTIAL_MARKERS
    )

    has_exception = any(
        marker in line
        for marker in EXCEPTION_MARKERS
    )

    if is_full and (has_exception or not is_partial):
        return "full"

    if is_partial and not is_full:
        return "partial"

    if is_full:
        return "full"

    return "unknown"


SUA_DOI_PATTERN = (
    r'sửa đổi[^.]*?theo\s+(.*?)(?=hết hiệu lực|$)'
)

def extract_document_relations(line):

    m = re.search(
        SUA_DOI_PATTERN,
        line,
        re.IGNORECASE
    )

    if not m:
        return extract_doc_references(line), []

    amend_part = m.group(1)

    amend_start = line.find(amend_part)

    root_part = line[:amend_start]

    root_refs = extract_doc_references(root_part)

    amending_refs = extract_doc_references(amend_part)

    return root_refs, amending_refs


# lay van ban het hieu luc that su 
def get_replaced_documents(raw_doc_modify):

    replaced_docs = []

    seen = set()

    for line in raw_doc_modify:

        if classify_doc_modify(line) != "full":
            continue

        root_refs, _ = extract_document_relations(line)

        for ref in root_refs:

            so_hieu = ref["so_hieu"]

            if so_hieu not in seen:

                seen.add(so_hieu)

                replaced_docs.append(ref)

    return replaced_docs

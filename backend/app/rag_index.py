"""Page-preserving local BM25 retrieval. No embedding/model call during indexing."""
from collections import Counter
import math
import re
import unicodedata
from sqlalchemy import delete, select, func
from sqlalchemy.orm import defer
from .models import RagDocument, RagChunk
from .security import ApiError

INDEX_VERSION = "bm25-multilingual-v1"
CONCEPTS = {
    "outpatient": ("ngoai tru", "outpatient", "门诊"),
    "inpatient": ("noi tru", "inpatient", "hospitalisation", "hospitalization", "住院"),
    "dental": ("nha khoa", "kham rang", "chua rang", "dental", "dentist", "牙科"),
    "evacuation": ("van chuyen y te", "evacuation", "medical transport", "医疗转运"),
    "maternity": ("thai san", "maternity", "childbirth", "生育", "产科"),
    "vision": ("thi luc", "vision care", "眼科"),
    "exclusion": ("loai tru", "exclusion", "excluded", "exclusions", "除外", "免责"),
    "claim": ("boi thuong", "claim", "claims", "理赔"),
    "documents": ("ho so", "chung tu", "documents", "documentation", "材料"),
    "waiting": ("thoi gian cho", "thoi han cho", "waiting period", "等待期"),
    "territory": ("lanh tho", "territory", "territorial", "地区", "地域"),
    "deductible": ("khau tru", "deductible", "免赔"),
    "premium": ("phi bao hiem", "premium", "保费"),
    "deadline": ("thoi han nop", "deadline", "within", "时限"),
}
STOP = set("toi cua la co khong nhung duoc cho bao hiem va voi ve nhu nao gi nay theo trong de ban can mot cac khi hay xin the and what how this that with are does can you your policy insurance please about is a an to of for my me explain tell it covered cover coverage health toi hoi tai lieu".split())


def normal(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower().replace("đ", "d")) if not unicodedata.combining(c))


def concepts(text):
    value = normal(text)
    return {name for name, phrases in CONCEPTS.items() if any(
        (phrase in value if re.search(r"[\u4e00-\u9fff]", phrase) else re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", value)) for phrase in phrases)}


def tokens(text):
    value = normal(text)
    words = [w for w in re.findall(r"[a-z0-9]+", value) if len(w) > 1 and w not in STOP]
    for run in re.findall(r"[\u4e00-\u9fff]+", value):
        words.extend(run[i:i+2] for i in range(len(run)-1))
    return words + ["__" + name for name in concepts(text)]


def split_pages(pages, size=900, overlap=100):
    result = []
    for page in pages:
        text = page["text"]
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                boundary = max(text.rfind("\n", start + size // 2, end), text.rfind(". ", start + size // 2, end))
                if boundary > start: end = boundary + 1
            content = text[start:end]
            frequencies = dict(Counter(tokens(content)))
            if frequencies:
                result.append({"ordinal": len(result) + 1, "page": page["page"], "start": start, "end": end,
                               "content": content, "terms": frequencies, "token_count": sum(frequencies.values())})
            if end == len(text): break
            start = max(start + 1, end - overlap)
    return result


def reindex(db, doc):
    chunks = split_pages(doc.pages) if not doc.deleted else []
    if len(chunks) > 1500:
        raise ApiError("RAG_CORPUS_LIMIT", "Tài liệu có quá nhiều đoạn; hãy chia nhỏ tài liệu.", 413)
    db.execute(delete(RagChunk).where(RagChunk.document_id == doc.id))
    retained = db.scalar(select(func.count()).select_from(RagChunk))
    if retained + len(chunks) > 20000:
        raise ApiError("RAG_CORPUS_LIMIT", "Kho RAG đã đạt giới hạn 20.000 đoạn.", 409)
    db.add_all([RagChunk(document_id=doc.id, revision=doc.revision, **chunk) for chunk in chunks])
    db.flush()


def retrieve(db, question, document_id=None, category=None, jurisdiction=None, draft=False):
    query = select(RagChunk, RagDocument).options(defer(RagDocument.original_bytes), defer(RagDocument.pages)).join(RagDocument, RagChunk.document_id == RagDocument.id).where(
        RagDocument.deleted == False, RagChunk.revision == RagDocument.revision)
    if not draft: query = query.where(RagDocument.published == True)
    if document_id: query = query.where(RagDocument.id == document_id)
    if category: query = query.where(RagDocument.category == category)
    if jurisdiction: query = query.where(RagDocument.jurisdiction.in_([jurisdiction, "WORLD"]))
    # Explicit size limit enforced on writes; published scope applied before ranking.
    rows = list(db.execute(query.order_by(RagDocument.id, RagChunk.ordinal)))
    terms = set(tokens(question)); wanted = concepts(question)
    specific = wanted & {"outpatient", "inpatient", "dental", "evacuation", "maternity", "vision"}
    if not rows or not terms: return [], wanted
    df = Counter(term for chunk, _ in rows for term in terms if term in chunk.terms)
    average = sum(chunk.token_count for chunk, _ in rows) / len(rows)
    ranked = []
    for chunk, doc in rows:
        supported = {key[2:] for key in chunk.terms if key.startswith("__")}
        if specific and not specific & supported: continue
        score = 0
        hits = []
        for term in terms:
            frequency = chunk.terms.get(term, 0)
            if not frequency: continue
            idf = math.log(1 + (len(rows) - df[term] + .5) / (df[term] + .5))
            score += (2 if term.startswith("__") else 1) * idf * (frequency * 2.5) / (frequency + 1.5 * (.25 + .75 * chunk.token_count / average))
            hits.append(term)
        if score <= 0: continue
        ranked.append({"document_id": str(doc.id), "revision": doc.revision, "chunk_id": str(chunk.id), "page": chunk.page,
            "start": chunk.start, "end": chunk.end, "excerpt": chunk.content, "title": doc.title, "publisher": doc.publisher,
            "filename": doc.filename, "source_url": doc.source_url, "document_kind": doc.source_kind, "sha256": doc.sha256,
            "category": doc.category, "language": doc.language, "jurisdiction": doc.jurisdiction,
            "score": round(score, 5), "matched_terms": sorted(hits), "concepts": sorted(supported)})
    ranked.sort(key=lambda item: (-item["score"], item["document_id"], item["start"]))
    selected = []; seen_concepts = set()
    # Prefer evidence for different requested concepts over near-duplicate overlap chunks.
    while ranked and len(selected) < 3:
        item = max(ranked, key=lambda item: (len((set(item["concepts"]) & wanted) - seen_concepts), item["score"]))
        ranked.remove(item)
        if any(item["document_id"] == prev["document_id"] and item["page"] == prev["page"] and
               max(item["start"], prev["start"]) < min(item["end"], prev["end"]) for prev in selected): continue
        selected.append(item); seen_concepts.update(item["concepts"])
    return selected, wanted - seen_concepts

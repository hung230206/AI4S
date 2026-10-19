"""Private policy documents with extractive, cited search; no generated insurance claims."""
import hashlib
import io
import re
import unicodedata
from pathlib import PurePosixPath
from urllib.parse import quote
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import Field, AnyHttpUrl, TypeAdapter, ValidationError
from pypdf import PdfReader
from sqlalchemy import select
from .db import get_db
from .models import PolicyDocument
from .schemas import Strict
from .security import student, lock_user, ApiError
from .services import iso, audit

router = APIRouter(prefix="/api/v1/documents", tags=["Private policy documents"])
MAX_BYTES = 5 * 1024 * 1024


class Search(Strict):
    question: str = Field(min_length=2, max_length=500)
    document_id: UUID | None = None


def normalize(value):
    value = unicodedata.normalize("NFKD", value.lower().replace("đ", "d"))
    return "".join(c for c in value if not unicodedata.combining(c))


def extract(raw, filename, language="auto"):
    if filename.lower().endswith(".pdf"):
        if not raw.startswith(b"%PDF-"):
            raise ApiError("DOCUMENT_INVALID", "File is not a PDF", 422)
        try:
            reader = PdfReader(io.BytesIO(raw), strict=False)
            if reader.is_encrypted:
                raise ApiError("DOCUMENT_ENCRYPTED", "Upload an unlocked policy PDF", 422)
            if len(reader.pages) > 50:
                raise ApiError("DOCUMENT_TOO_LARGE", "Maximum 50 pages", 422)
            pages = [{"page": i + 1, "text": page.extract_text(extraction_mode="plain") or ""} for i, page in enumerate(reader.pages)]
            if len(pages) <= 5 and any(len(page["text"].strip()) < 20 for page in pages):
                from .ocr import extract_file
                pages, _, _ = extract_file(raw, filename, language)
        except ApiError:
            raise
        except Exception:
            raise ApiError("DOCUMENT_INVALID", "Cannot read this PDF; try a text-based PDF or UTF-8 text", 422)
        mime = "application/pdf"
    elif filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        from .ocr import extract_file
        pages, mime, _ = extract_file(raw, filename, language)
    elif filename.lower().endswith((".txt", ".md")):
        try:
            value = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ApiError("DOCUMENT_INVALID", "Text documents must use UTF-8 encoding", 422)
        pages = [{"page": 1, "text": value}]
        mime = "text/plain; charset=utf-8"
    else:
        raise ApiError("DOCUMENT_TYPE_UNSUPPORTED", "Supported types: PDF, images, TXT and MD", 422)
    chars = sum(len(page["text"]) for page in pages)
    if chars > 500_000:
        raise ApiError("DOCUMENT_TOO_LARGE", "Maximum 500,000 extracted characters", 422)
    if chars < 20:
        raise ApiError("DOCUMENT_NO_TEXT", "No readable text found. Scanned images need OCR before upload", 422)
    return pages, mime


def public_document(doc):
    return {"id": str(doc.id), "title": doc.title, "filename": doc.filename, "byte_size": doc.byte_size, "page_count": len(doc.pages), "source_url": doc.source_url, "created_at": iso(doc.created_at), "source_type": "USER_DOCUMENT", "document_kind": doc.document_kind, "extraction_method": "LOCAL_TESSERACT" if any("confidence" in p for p in doc.pages) else "TEXT_EXTRACT"}


def own(db, document_id, user):
    doc = db.scalar(select(PolicyDocument).where(PolicyDocument.id == document_id, PolicyDocument.user_id == user.id))
    if not doc:
        raise ApiError("DOCUMENT_NOT_FOUND", "Document not found", 404)
    return doc


@router.post("")
def upload(file: UploadFile = File(...), title: str = Form(""), source_url: str = Form(""), language: Literal["auto", "en", "vi", "zh"] = Form("auto"), document_kind: Literal["USER_PROVIDED", "PUBLIC_REFERENCE", "TEST_FIXTURE"] = Form("USER_PROVIDED"), user=Depends(student), db=Depends(get_db, scope="function")):
    raw = file.file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ApiError("DOCUMENT_TOO_LARGE", "Maximum upload size is 5 MB", 413)
    filename = PurePosixPath((file.filename or "document").replace("\\", "/")).name
    filename = "".join(c for c in filename if ord(c) >= 32)[:180]
    title = title.strip() or filename
    if len(title) > 200 or not filename:
        raise ApiError("DOCUMENT_INVALID", "Invalid title or filename", 422)
    if document_kind == "PUBLIC_REFERENCE" and not source_url.strip():
        raise ApiError("DOCUMENT_SOURCE_REQUIRED", "Public reference documents require the original source URL", 422)
    if source_url:
        try:
            source_url = str(TypeAdapter(AnyHttpUrl).validate_python(source_url))
        except ValidationError:
            raise ApiError("DOCUMENT_INVALID", "Source must be an HTTP(S) URL", 422)
    pages, mime = extract(raw, filename, language)
    lock_user(db, user)
    sha = hashlib.sha256(raw).hexdigest()
    previous = db.scalar(select(PolicyDocument).where(PolicyDocument.user_id == user.id, PolicyDocument.sha256 == sha))
    if previous:
        return {**public_document(previous), "already_uploaded": True}
    doc = PolicyDocument(user_id=user.id, title=title, filename=filename, content_type=mime, byte_size=len(raw), sha256=sha, original_bytes=raw, pages=pages, source_url=source_url or None, document_kind=document_kind)
    db.add(doc)
    db.flush()
    audit(db, user, "POLICY_DOCUMENT_UPLOADED", document_id=str(doc.id))
    return public_document(doc)


@router.get("")
def documents(user=Depends(student), db=Depends(get_db, scope="function")):
    return {"items": [public_document(d) for d in db.scalars(select(PolicyDocument).where(PolicyDocument.user_id == user.id).order_by(PolicyDocument.created_at.desc()))]}


@router.get("/{document_id}")
def detail(document_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    doc = own(db, document_id, user)
    return {**public_document(doc), "pages": doc.pages}


@router.get("/{document_id}/download")
def download(document_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    doc = own(db, document_id, user)
    return Response(doc.original_bytes, media_type=doc.content_type, headers={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(doc.filename), "Cache-Control": "no-store"})


@router.post("/{document_id}/delete")
def delete(document_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    from .models import InsurancePolicy, InsuranceClaim
    lock_user(db, user)
    if (db.scalar(select(InsurancePolicy.id).where(InsurancePolicy.document_id == document_id, InsurancePolicy.user_id == user.id)) or
            db.scalar(select(InsuranceClaim.id).where(InsuranceClaim.user_id == user.id, InsuranceClaim.policy_snapshot["document_id"].astext == str(document_id)))):
        raise ApiError("DOCUMENT_IN_USE", "Tài liệu đang làm nguồn cho hợp đồng. Giữ bản gốc để đối chiếu hồ sơ và trích dẫn.", 409)
    doc = own(db, document_id, user)
    db.delete(doc)
    audit(db, user, "POLICY_DOCUMENT_DELETED", document_id=str(document_id))
    return {"deleted": True}


@router.post("/search")
def search(body: Search, user=Depends(student), db=Depends(get_db, scope="function")):
    query = select(PolicyDocument).where(PolicyDocument.user_id == user.id)
    if body.document_id:
        own(db, body.document_id, user)
        query = query.where(PolicyDocument.id == body.document_id)
    docs = list(db.scalars(query))
    if not docs:
        return {"status": "NO_DOCUMENTS", "message": "Upload your policy document first", "matches": [], "method": "EXTRACTIVE_SEARCH"}
    question = normalize(body.question)
    stopwords = {"toi", "cua", "la", "co", "khong", "nhung", "duoc", "cho", "bao", "hiem", "the", "and", "what", "how", "this", "that", "with", "are", "does", "can"}
    terms = {t for t in re.findall(r"[\w]+", question) if len(t) > 2 and t not in stopwords}
    for word in re.findall(r"[\u4e00-\u9fff]{2,}", question):
        terms.add(word)
        terms.update(word[i:i + 2] for i in range(len(word) - 1))
    synonyms = {"boi thuong": ["claim", "claims", "compensation", "理赔"], "loai tru": ["exclusion", "excluded", "exclusions", "除外"], "phi": ["premium", "fee", "保费"], "thoi han": ["period", "expiry", "duration", "期限"], "quyen loi": ["benefit", "coverage", "benefits", "保障"], "ho so": ["documents", "documentation", "材料"]}
    for vi, values in synonyms.items():
        if vi in question or any(value in question for value in values):
            terms.update(values)
            terms.add(vi)
    matches = []
    for doc in docs:
        for page in doc.pages:
            for passage in re.split(r"\n\s*\n|(?<=[.!?。])\s+", page["text"]):
                passage = passage.strip()
                normalized = normalize(passage)
                hits = [term for term in terms if term in normalized]
                if hits:
                    first = min(normalized.find(term) for term in hits)
                    start = max(0, first - 180)
                    excerpt = passage[start:start + 900]
                    matches.append({"document_id": str(doc.id), "title": doc.title, "filename": doc.filename, "page": page["page"], "excerpt": excerpt, "source_url": doc.source_url, "document_kind": doc.document_kind, "matched_terms": hits, "score": len(hits)})
    matches.sort(key=lambda item: item["score"], reverse=True)
    return {"status": "MATCHES_FOUND" if matches else "INSUFFICIENT_INFORMATION", "message": "Original excerpts from your documents; check the full clause and context" if matches else "No matching clause found in the uploaded documents", "matches": matches[:5], "method": "EXTRACTIVE_SEARCH"}

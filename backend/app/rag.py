"""Managed insurance RAG: authenticated publication, local retrieval, optional generation."""
import hashlib
from pathlib import PurePosixPath
from typing import Literal
from urllib.parse import quote
from uuid import UUID
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response
from pydantic import Field, AnyHttpUrl, field_validator, model_validator
from sqlalchemy import select, func, text
from sqlalchemy.orm import defer
from . import gemini
from .accounts import throttle
from .config import settings
from .db import get_db
from .documents import extract, MAX_BYTES
from .file_consent import require_file_consent
from .models import RagDocument, RagChunk, RagRevision, now
from .privacy import require_permission
from .rag_index import reindex, retrieve, INDEX_VERSION
from .schemas import Strict
from .security import ApiError, student, rag_admin
from .services import audit, iso

router = APIRouter(prefix="/api/v1", tags=["Managed insurance RAG"])
PUBLICATION_NOTICE = "rag-publication-2026-10-19-v1"


class Metadata(Strict):
    title: str = Field(min_length=3, max_length=200)
    publisher: str = Field(min_length=2, max_length=200)
    source_url: AnyHttpUrl | None = None
    source_kind: Literal["TEST_FIXTURE", "PUBLIC_REFERENCE"] = "TEST_FIXTURE"
    license_note: str = Field(min_length=10, max_length=1000)
    category: Literal["POLICY", "CLAIMS", "GLOSSARY"] = "POLICY"
    language: Literal["vi", "en", "zh"] = "vi"
    jurisdiction: Literal["CN", "VN", "WORLD"] = "CN"

    @field_validator("title", "publisher", "license_note")
    @classmethod
    def strip_text(cls, value):
        if not value.strip(): raise ValueError("Required text")
        return value.strip()

    @model_validator(mode="after")
    def public_source(self):
        if self.source_kind == "PUBLIC_REFERENCE" and self.source_url is None:
            raise ValueError("A public reference needs its original source URL")
        if self.source_url and (self.source_url.username or self.source_url.password or len(str(self.source_url)) > 2000):
            raise ValueError("Source URLs must not contain credentials and must be at most 2000 characters")
        return self


class CreateText(Metadata):
    content: str = Field(min_length=40, max_length=200000)


class UpdateText(Metadata):
    revision: int = Field(ge=1)
    content: str | None = Field(default=None, min_length=40, max_length=200000)


class RevisionInput(Strict):
    revision: int = Field(ge=1)


class PublishInput(RevisionInput):
    publication_confirmed: bool = False
    notice_version: str


class RagQuestion(Strict):
    question: str = Field(min_length=2, max_length=500)
    document_id: UUID | None = None
    category: Literal["POLICY", "CLAIMS", "GLOSSARY"] | None = None
    jurisdiction: Literal["CN", "VN"] | None = None
    language: Literal["vi", "en", "zh"] = "vi"
    use_gemini: bool = False
    privacy_revision: int | None = None

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, value):
        if len(value.strip()) < 2: raise ValueError("Question required")
        return value.strip()


def out(doc):
    return {"id": str(doc.id), "title": doc.title, "publisher": doc.publisher, "source_url": doc.source_url,
        "source_kind": doc.source_kind, "license_note": doc.license_note, "category": doc.category,
        "language": doc.language, "jurisdiction": doc.jurisdiction, "revision": doc.revision, "published": doc.published,
        "deleted": doc.deleted, "origin": doc.origin, "filename": doc.filename, "sha256": doc.sha256,
        "page_count": len(doc.pages), "updated_at": iso(doc.updated_at), "created_at": iso(doc.created_at)}


def locked(db, document_id, revision=None, deleted=False):
    # Consistent lock order for corpus quotas and atomic reindex/publish/delete.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext('rag-corpus-write'))"))
    doc = db.scalar(select(RagDocument).where(RagDocument.id == document_id).with_for_update())
    if not doc or (doc.deleted and not deleted): raise ApiError("RAG_DOCUMENT_NOT_FOUND", "Không tìm thấy tài liệu RAG.", 404)
    if revision is not None and revision != doc.revision: raise ApiError("STALE_REVISION", "Tài liệu vừa thay đổi. Tải lại trước khi lưu.", 409)
    return doc


def record(db, doc, user, action, initial=False):
    if not initial: doc.revision += 1
    doc.updated_at = now(); doc.updated_by = user.id if user else None
    db.flush(); reindex(db, doc)
    db.add(RagRevision(document_id=doc.id, revision=doc.revision, actor_id=doc.updated_by,
                       action=action, snapshot=out(doc)))
    if user: audit(db, user, "RAG_" + action, document_id=str(doc.id), revision=doc.revision, sha256=doc.sha256)
    db.flush()


def create(db, meta, pages, raw, filename, mime, origin, user, document_id=None, published=False):
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext('rag-corpus-write'))"))
    if db.scalar(select(func.count()).select_from(RagDocument)) >= 100:
        raise ApiError("RAG_CORPUS_LIMIT", "Kho thử nghiệm tối đa 100 tài liệu, kể cả thùng rác.", 409)
    fields = meta.model_dump(mode="json")
    doc = RagDocument(**fields, pages=pages, original_bytes=raw, filename=filename, content_type=mime,
                      origin=origin, sha256=hashlib.sha256(raw).hexdigest(), revision=1, published=published, deleted=False)
    if document_id: doc.id = document_id
    db.add(doc); db.flush(); record(db, doc, user, "CREATED", initial=True)
    return doc


def read_file(file, language):
    raw = file.file.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES: raise ApiError("DOCUMENT_TOO_LARGE", "Tệp cần từ 1 byte đến 5 MB.", 413)
    filename = PurePosixPath((file.filename or "document").replace("\\", "/")).name
    filename = "".join(c for c in filename if ord(c) >= 32)[:180]
    pages, mime = extract(raw, filename, language)
    return raw, filename, pages, mime


@router.get("/admin/rag/documents")
def admin_documents(deleted: bool = False, user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    docs = db.scalars(select(RagDocument).options(defer(RagDocument.original_bytes)).where(RagDocument.deleted == deleted).order_by(RagDocument.updated_at.desc()))
    return {"items": [out(doc) for doc in docs], "publication_notice": PUBLICATION_NOTICE, "index_method": INDEX_VERSION}


@router.post("/admin/rag/documents")
def create_text(body: CreateText, user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    raw = body.content.encode("utf-8")
    meta = Metadata(**body.model_dump(exclude={"content"}))
    return out(create(db, meta, [{"page": 1, "text": body.content}], raw, "authored-document.txt", "text/plain; charset=utf-8", "AUTHORED_TEXT", user))


@router.post("/admin/rag/documents/upload")
def upload_document(metadata: str = Form(...), file: UploadFile = File(...),
                    consent=Depends(require_file_consent("rag-corpus")), user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    try: meta = Metadata.model_validate_json(metadata)
    except ValueError: raise ApiError("VALIDATION_ERROR", "Kiểm tra thông tin nguồn và quyền sử dụng.", 422) from None
    raw, filename, pages, mime = read_file(file, meta.language)
    doc = create(db, meta, pages, raw, filename, mime, "UPLOADED_FILE", user)
    audit(db, user, "RAG_FILE_PROCESSING_ACCEPTED", document_id=str(doc.id), processing_consent=consent)
    return out(doc)


@router.get("/admin/rag/documents/{document_id}")
def admin_detail(document_id: UUID, user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    doc = db.get(RagDocument, document_id)
    if not doc: raise ApiError("RAG_DOCUMENT_NOT_FOUND", "Không tìm thấy tài liệu RAG.", 404)
    revisions = db.scalars(select(RagRevision).where(RagRevision.document_id == doc.id).order_by(RagRevision.revision.desc()))
    return {**out(doc), "pages": doc.pages, "chunk_count": db.scalar(select(func.count()).select_from(RagChunk).where(RagChunk.document_id == doc.id)),
            "history": [{"revision": row.revision, "action": row.action, "at": iso(row.created_at), "snapshot": row.snapshot} for row in revisions]}


@router.post("/admin/rag/documents/{document_id}/update")
def update_document(document_id: UUID, body: UpdateText, user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    doc = locked(db, document_id, body.revision)
    if body.content is not None:
        if doc.origin != "AUTHORED_TEXT": raise ApiError("RAG_REPLACE_FILE_REQUIRED", "Để sửa nội dung tệp gốc, hãy tải tệp thay thế. Không ghi đè văn bản trích xuất.", 422)
        doc.pages = [{"page": 1, "text": body.content}]; doc.original_bytes = body.content.encode("utf-8")
        doc.sha256 = hashlib.sha256(doc.original_bytes).hexdigest()
    for key, value in body.model_dump(mode="json", exclude={"revision", "content"}).items(): setattr(doc, key, value)
    doc.published = False
    record(db, doc, user, "UPDATED")
    return out(doc)


@router.post("/admin/rag/documents/{document_id}/file")
def replace_file(document_id: UUID, revision: int = Form(...), file: UploadFile = File(...),
                 consent=Depends(require_file_consent("rag-corpus")), user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    doc = locked(db, document_id, revision)
    raw, filename, pages, mime = read_file(file, doc.language)
    doc.original_bytes = raw; doc.filename = filename; doc.pages = pages; doc.content_type = mime
    doc.sha256 = hashlib.sha256(raw).hexdigest(); doc.origin = "UPLOADED_FILE"; doc.published = False
    record(db, doc, user, "FILE_REPLACED")
    audit(db, user, "RAG_FILE_PROCESSING_ACCEPTED", document_id=str(doc.id), processing_consent=consent)
    return out(doc)


@router.post("/admin/rag/documents/{document_id}/publish")
def publish(document_id: UUID, body: PublishInput, user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    doc = locked(db, document_id, body.revision)
    if not body.publication_confirmed or body.notice_version != PUBLICATION_NOTICE:
        raise ApiError("RAG_PUBLICATION_CONSENT_REQUIRED", "Cần xác nhận quyền công bố tài liệu trước khi xuất bản.", 403)
    gemini.ensure_non_sensitive({"title": doc.title, "publisher": doc.publisher, "license_note": doc.license_note, "source_url": doc.source_url, "pages": doc.pages})
    if not db.scalar(select(RagChunk.id).where(RagChunk.document_id == doc.id).limit(1)):
        raise ApiError("DOCUMENT_NO_TEXT", "Tài liệu chưa có đoạn có thể truy xuất.", 422)
    doc.published = True; record(db, doc, user, "PUBLISHED")
    return out(doc)


@router.post("/admin/rag/documents/{document_id}/{action}")
def state_change(document_id: UUID, action: Literal["unpublish", "delete", "restore"], body: RevisionInput,
                 user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    doc = locked(db, document_id, body.revision, deleted=action == "restore")
    doc.published = False; doc.deleted = action == "delete"
    record(db, doc, user, {"unpublish": "UNPUBLISHED", "delete": "DELETED", "restore": "RESTORED"}[action])
    return out(doc)


@router.get("/rag/documents")
def public_documents(user=Depends(student), db=Depends(get_db, scope="function")):
    return {"items": [out(doc) for doc in db.scalars(select(RagDocument).options(defer(RagDocument.original_bytes)).where(RagDocument.published == True, RagDocument.deleted == False).order_by(RagDocument.title))],
            "gemini_configured": gemini.configured(), "index_method": INDEX_VERSION}


def published_source(db, document_id, revision=None):
    doc = db.get(RagDocument, document_id)
    if not doc or not doc.published or doc.deleted: raise ApiError("RAG_DOCUMENT_NOT_FOUND", "Nguồn chưa xuất bản hoặc đã được gỡ khỏi kho.", 404)
    if revision is not None and doc.revision != revision:
        raise ApiError("RAG_SOURCE_RETIRED", "Nguồn đã được cập nhật. Hỏi lại để dùng phiên bản mới.", 409)
    return doc


@router.get("/rag/documents/{document_id}")
def public_detail(document_id: UUID, revision: int | None = None, user=Depends(student), db=Depends(get_db, scope="function")):
    doc = published_source(db, document_id, revision)
    return {**out(doc), "pages": doc.pages}


@router.get("/rag/documents/{document_id}/download")
def public_download(document_id: UUID, revision: int, user=Depends(student), db=Depends(get_db, scope="function")):
    doc = published_source(db, document_id, revision)
    return Response(doc.original_bytes, media_type=doc.content_type, headers={"Content-Disposition": "attachment; filename*=UTF-8''" + quote(doc.filename)})


def retrieval(body, db, draft=False):
    if body.document_id and not draft: published_source(db, body.document_id)
    matches, missing = retrieve(db, body.question, body.document_id, body.category, body.jurisdiction, draft=draft)
    for i, match in enumerate(matches):
        match["source_id"] = f"R{i + 1}"
        match["href"] = f"/knowledge/{match['document_id']}?revision={match['revision']}#page-{match['page']}"
    return matches, sorted(missing)


@router.post("/admin/rag/preview")
def admin_preview(body: RagQuestion, user=Depends(rag_admin), db=Depends(get_db, scope="function")):
    if not body.document_id: raise ApiError("RAG_DOCUMENT_REQUIRED", "Chọn một bản nháp để thử truy xuất.", 422)
    doc = db.get(RagDocument, body.document_id)
    if not doc or doc.deleted: raise ApiError("RAG_DOCUMENT_NOT_FOUND", "Không tìm thấy tài liệu.", 404)
    matches, missing = retrieval(body, db, draft=True)
    return {"matches": matches, "missing_concepts": missing, "provider": "LOCAL", "method": INDEX_VERSION}


def cloud_permission(db, request, user, revision):
    permission = require_permission(db, request, user, revision)
    if "documents" not in permission.scopes:
        raise ApiError("AI_CONSENT_REQUIRED", "Quyền hiện tại chưa cho phép gửi đoạn tài liệu tới Gemini.", 403)
    return permission


@router.post("/rag/preview")
def preview(body: RagQuestion, request: Request, user=Depends(student), db=Depends(get_db, scope="function")):
    cloud_permission(db, request, user, body.privacy_revision)
    matches, missing = retrieval(body, db)
    return {"recipient": "Google Gemini", "question": body.question, "excerpts": matches, "missing_concepts": missing, "sent": False}


@router.post("/rag/ask")
def ask(body: RagQuestion, request: Request, user=Depends(student), db=Depends(get_db, scope="function")):
    permission = cloud_permission(db, request, user, body.privacy_revision) if body.use_gemini else None
    matches, missing = retrieval(body, db)
    prefixes = {"vi": "Các đoạn gốc liên quan để bạn đối chiếu:", "en": "Relevant original passages to review:", "zh": "请核对以下相关原文："}
    absent = {"vi": "Chưa có đủ thông tin trong kho tài liệu đã xuất bản để trả lời. Hãy bổ sung hoặc chọn lại nguồn; không suy đoán quyền lợi.",
              "en": "The published knowledge base has insufficient evidence. Add or choose a source; coverage cannot be inferred.",
              "zh": "已发布的知识库证据不足，请补充或重新选择来源，不能推测保障权益。"}
    result = {"status": "PARTIAL_EVIDENCE" if missing and matches else "EVIDENCE_FOUND" if matches else "INSUFFICIENT_INFORMATION",
        "answer": prefixes[body.language] + "\n\n" + "\n\n".join(f"[{m['source_id']}] {m['excerpt']}" for m in matches) if matches else absent[body.language],
        "provider": "EXTRACTIVE", "method": INDEX_VERSION, "citations": matches, "missing_concepts": missing,
        "executed_actions": [], "actions": [{"title": "Kiểm tra quyền lợi hợp đồng", "href": "/insurance"}, {"title": "Chuẩn bị hồ sơ bồi thường", "href": "/insurance"}],
        "notice": "Nguồn mẫu/tham khảo; không xác nhận quyền lợi, xét duyệt hoặc gửi hồ sơ. Điểm truy xuất không phải xác suất trả lời đúng."}
    if not matches or not body.use_gemini: return result
    if not gemini.configured(): return {**result, "fallback_reason": "NOT_CONFIGURED"}
    evidence = [{"id": m["source_id"], "kind": "ORIGINAL_DOCUMENT_EXCERPT", "data": {k: m[k] for k in ("title", "page", "excerpt", "document_kind", "revision")}} for m in matches]
    gemini.ensure_non_sensitive({"question": body.question, "server_evidence": evidence})
    throttle(db, request, str(user.id), "GEMINI_USER", limit=20)
    throttle(db, request, "all", "GEMINI_APP", limit=60)
    audit(db, user, "AI_REQUEST_DISPATCHED", notice_version=permission.notice_version, revision=permission.revision,
          evidence_count=len(evidence), purpose="INSURANCE_RAG", model=settings.gemini_model)
    db.commit()  # Never hold corpus/account locks during the network call.
    try:
        generated = gemini.generate(body.question, [], body.language, evidence)
        if not generated.source_ids: raise gemini.GeminiFailure("UNGROUNDED_RESPONSE")
        allowed = {m["source_id"] for m in matches}
        if not set(generated.source_ids) <= allowed: raise gemini.GeminiFailure("INVALID_RESPONSE")
        response = {**result, "provider": "GEMINI", "method": "BM25_RAG_GEMINI", "model": settings.gemini_model,
                "answer": generated.answer, "citations": [m for m in matches if m["source_id"] in generated.source_ids]}
    except gemini.GeminiFailure as exc:
        response = {**result, "fallback_reason": exc.code}
    # Revalidate on success AND fallback: long-running calls must not serve withdrawn data.
    db.expire_all()
    session = getattr(request.state, "account_session", None)
    if session and (session.revoked or session.expires_at <= now()):
        raise ApiError("UNAUTHORIZED", "Phiên đăng nhập đã hết hiệu lực.", 401)
    cloud_permission(db, request, user, body.privacy_revision)
    for match in matches:
        try: published_source(db, UUID(match["document_id"]), match["revision"])
        except ApiError: return {**result, "answer": absent[body.language], "citations": [], "status": "SOURCES_CHANGED", "fallback_reason": "SOURCES_CHANGED"}
    return response

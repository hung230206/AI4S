"""Local OCR + labelled field extraction. Document content never goes upstream."""
import hashlib
import io
import os
import json
import logging
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unicodedata
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from uuid import UUID, uuid4
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import Response
from PIL import Image, ImageOps, UnidentifiedImageError
from pypdf import PdfReader
import pypdfium2 as pdfium
from sqlalchemy import select, func, text
from .config import ROOT, settings
from .file_consent import require_file_consent
from .db import get_db, SessionLocal
from .models import InvoiceImport, User, now
from .security import student, ApiError, lock_user
from .services import audit

router = APIRouter(prefix="/api/v1/invoice-imports", tags=["Reviewed local invoice OCR"])
slots = threading.BoundedSemaphore(settings.ocr_max_workers)
job_slots = threading.BoundedSemaphore(settings.ocr_max_workers)
MAX_BYTES = 5 * 1024 * 1024


def plain(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower().replace("đ", "d")) if not unicodedata.combining(c))


def amount_value(value):
    value = re.sub(r"[^0-9,.]", "", value)
    if not value:
        return None
    if "," in value and "." in value:
        decimal = "," if value.rfind(",") > value.rfind(".") else "."
        value = value.replace("." if decimal == "," else ",", "").replace(decimal, ".")
    elif "," in value:
        value = value.replace(",", ".") if len(value.rsplit(",", 1)[1]) in (1, 2) else value.replace(",", "")
    elif value.count(".") > 1:
        value = value.replace(".", "")
    try:
        number = Decimal(value)
        if 0 < number < Decimal("1000000000000") and number == number.quantize(Decimal(".01")):
            return format(number, ".2f")
    except InvalidOperation:
        pass
    return None


def suggestions(pages):
    from .document_assist import labelled, unique, number, dates, currency as detect_currency, document_type
    fields = {}
    labels = {
        "invoice_number": r"invoice\s*(?:no\.?|number|#)|ma\s*(?:hoa don|thong bao)|发票号码|发票编号|编号|票据编号|bill reference",
        "institution_name": r"issuer|institution|school|don vi phat hanh|开票单位|学校|收费单位",
        "beneficiary_name": r"beneficiary|payee|recipient|ben nhan|收款单位|收款人",
        "amount_cny": r"amount\s*due|total\s*due|total|tong tien|so tien|应付金额|合计|金额",
        "due_date": r"due\s*date|pay\s*by|han thanh toan|缴费截止日期|截止日期|到期日",
    }
    text = "\n".join(p["text"] for p in pages)
    code = detect_currency(text)
    kind = document_type(pages)
    blocked = kind != "INVOICE_OR_NOTICE"
    for name, label in labels.items():
        convert = (lambda raw: number(raw) if code == "CNY" else None) if name == "amount_cny" else (lambda raw: dates(raw)[0] if len(dates(raw)) == 1 else None) if name == "due_date" else (lambda raw: raw[:100] if name == "invoice_number" else raw[:200])
        found = unique(labelled(pages, label), convert)
        if found and not blocked:
            fields[name] = {"value": found["value"], "page": found["page"], "source_line": found["quote"][:500]}
    fee_type = None
    for _, row in [(p["page"], row) for p in pages for row in p["text"].splitlines()[:12]]:
        normalized = plain(row)
        for category, pattern in (("TUITION", r"tuition(?: fee)?(?: notice)?|学费"), ("ACCOMMODATION", r"accommodation(?: fee)?|住宿费"), ("ANNUAL_HEALTH_INSURANCE_PREMIUM", r"insurance premium|保险费"), ("MEDICAL_SERVICE_FEE", r"medical service fee|医疗服务费")):
            if re.search(pattern, normalized):
                if fee_type and fee_type != category: fee_type = "AMBIGUOUS"
                elif fee_type != "AMBIGUOUS": fee_type = category
    warnings = []
    if blocked:
        warnings.append("Đây là chứng từ hồ sơ yêu cầu chi trả hoặc khoản đã chi, không phải khoản cần đóng. Hãy dùng ở mục Hồ sơ bồi thường.")
    if code != "CNY": warnings.append("Tệp không xác định rõ số tiền CNY. Không dùng số tiền VND hoặc ngoại tệ khác làm số tiền CNY.")
    warnings.append("Đối chiếu tất cả trường với bản gốc trước khi lưu. OCR có thể đọc sai số và tên.")
    return {"fields": fields, "document_type": kind, "currency": code, "fee_type": fee_type if fee_type != "AMBIGUOUS" and not blocked else None, "warnings": warnings}


def local_ocr(images, language="auto"):
    if not all((ROOT / ".local/ocr-models" / f"{lang}.traineddata").is_file() for lang in ("eng", "chi_sim", "vie")):
        raise ApiError("OCR_NOT_READY", "Run python scripts/setup_ocr.py and npm install in frontend", 503)
    native = shutil.which("tesseract")
    node = shutil.which("node")
    if not native and not node:
        raise ApiError("OCR_NOT_READY", "Node.js is required for local OCR", 503)
    if not slots.acquire(blocking=False):
        raise ApiError("OCR_BUSY", "OCR is busy; retry shortly", 429)
    try:
        if native:
            languages = {"auto": "eng+chi_sim+vie", "en": "eng", "vi": "vie+eng", "zh": "chi_sim+eng"}[language]
            deadline = time.monotonic() + settings.ocr_timeout_seconds
            pages = []
            for image in images:
                result = subprocess.run([native, image, "stdout", "--tessdata-dir", str(ROOT / ".local/ocr-models"), "-l", languages, "--oem", "1", "--psm", "3", "--dpi", "200"], env={**os.environ, "OMP_THREAD_LIMIT": "1"}, text=True, encoding="utf-8", capture_output=True, timeout=max(0.1, deadline - time.monotonic()), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                if result.returncode:
                    raise ApiError("OCR_FAILED", "Local text recognition failed; retry with the document language", 422)
                pages.append({"text": result.stdout, "ocr_engine": "TESSERACT_NATIVE"})
            return pages
        result = subprocess.run([node, str(ROOT / "scripts/ocr_runner.cjs")], input=json.dumps({"images": images, "language": language}), text=True, encoding="utf-8", capture_output=True, timeout=settings.ocr_timeout_seconds, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            raise ApiError("OCR_FAILED", "Cannot read this image; upload a clearer image or enter manually", 422)
        return json.loads(result.stdout)["pages"]
    except subprocess.TimeoutExpired:
        raise ApiError("OCR_TIMEOUT", "Document took too long; use fewer pages or a clearer image", 422)
    finally:
        slots.release()


def extract_file(raw, filename, language="auto"):
    suffix = Path(filename).suffix.lower()
    if suffix in (".txt", ".md"):
        try:
            value = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise ApiError("DOCUMENT_INVALID", "Text must be UTF-8", 422)
        if not 10 <= len(value) <= 100_000:
            raise ApiError("DOCUMENT_NO_TEXT" if len(value) < 10 else "DOCUMENT_TOO_LARGE", "Use 10 to 100,000 readable characters", 422)
        return [{"page": 1, "text": value}], "text/plain", "TEXT_EXTRACT"
    pages = []
    images = []
    mime = "application/pdf" if suffix == ".pdf" else "image/png"
    with tempfile.TemporaryDirectory(prefix="baoan-ocr-") as temp:
        if suffix == ".pdf":
            if not raw.startswith(b"%PDF-"):
                raise ApiError("DOCUMENT_INVALID", "Invalid PDF", 422)
            try:
                reader = PdfReader(io.BytesIO(raw))
                if reader.is_encrypted:
                    raise ApiError("DOCUMENT_ENCRYPTED", "Upload an unlocked PDF", 422)
                if len(reader.pages) > 5:
                    raise ApiError("DOCUMENT_TOO_LARGE", "Invoice OCR supports up to 5 pages", 422)
                texts = [page.extract_text() or "" for page in reader.pages]
                document = None
                try:
                    for index, text in enumerate(texts):
                        pages.append({"page": index + 1, "text": text})
                        if len(text.strip()) < 20:
                            document = document or pdfium.PdfDocument(raw)
                            page = document[index]
                            try:
                                scale = min(200 / 72, 2500 / max(page.get_size()))
                                bitmap = page.render(scale=scale)
                                image = bitmap.to_pil()
                                path = str(Path(temp) / f"page-{index}.png")
                                image.save(path)
                                image.close(); bitmap.close()
                                images.append((index, path))
                            finally:
                                page.close()
                finally:
                    if document is not None:
                        document.close()
            except ApiError:
                raise
            except Exception:
                raise ApiError("DOCUMENT_INVALID", "Cannot render this PDF", 422)
        elif suffix in (".png", ".jpg", ".jpeg", ".webp"):
            try:
                with Image.open(io.BytesIO(raw)) as original:
                    if original.width * original.height > 16_000_000:
                        raise ApiError("DOCUMENT_TOO_LARGE", "Maximum 16 megapixels", 422)
                    image = ImageOps.exif_transpose(original).convert("RGB")
                    image.thumbnail((2500, 2500))
                    path = str(Path(temp) / "image.png")
                    image.save(path); image.close()
                images = [(0, path)]
                pages = [{"page": 1, "text": ""}]
                mime = Image.MIME.get(original.format, "application/octet-stream")
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
                raise ApiError("DOCUMENT_INVALID", "Cannot decode image", 422)
        else:
            raise ApiError("DOCUMENT_TYPE_UNSUPPORTED", "Use PNG, JPG, WebP, PDF, TXT or MD", 422)
        if images:
            results = local_ocr([path for _, path in images], language)
            for (index, _), result in zip(images, results, strict=True):
                pages[index].update(result)
    if sum(len(p["text"]) for p in pages) < 10:
        raise ApiError("DOCUMENT_NO_TEXT", "No readable text; use a clearer document", 422)
    if sum(len(p["text"]) for p in pages) > 100_000:
        raise ApiError("DOCUMENT_TOO_LARGE", "Maximum 100,000 extracted characters", 422)
    return pages, mime, "LOCAL_TESSERACT" if images else "TEXT_EXTRACT"


def public_import(obj):
    status = obj.suggestions.get("processing_status", "COMPLETED")
    extracted = {**suggestions(obj.pages), **{k: v for k, v in obj.suggestions.items() if k not in ("fields", "currency", "warnings", "document_type")}} if obj.pages else obj.suggestions
    return {"id": str(obj.id), "filename": obj.filename, "method": obj.method, "pages": obj.pages, "suggestions": extracted, "status": status, "error_code": obj.suggestions.get("error_code"), "invoice_id": str(obj.invoice_id) if obj.invoice_id else None, "requires_review": True}


def process_import(import_id, consent):
    try:
        _process_import(import_id, consent)
    except Exception:
        # Background failures must not print SQL parameters containing private OCR text.
        logging.getLogger(__name__).warning("OCR job interrupted; the retained source can be retried")


def _process_import(import_id, consent):
    # Bounded workers; original bytes and result persist in the owner's source record.
    with job_slots:
        with SessionLocal.begin() as db:
            obj = db.get(InvoiceImport, import_id)
            if not obj or obj.suggestions.get("processing_status") != "QUEUED":
                return
            raw, filename, language = obj.original_bytes, obj.filename, obj.suggestions["language"]
            token = obj.suggestions["processing_token"]
            obj.suggestions = {**obj.suggestions, "processing_status": "RUNNING"}
        try:
            pages, mime, method = extract_file(raw, filename, language)
            result = {**suggestions(pages), "language": language, "processing_status": "COMPLETED"}
        except Exception as exc:
            pages, mime, method = [], "application/octet-stream", "OCR_FAILED"
            result = {"language": language, "processing_status": "FAILED", "error_code": exc.code if isinstance(exc, ApiError) else "OCR_FAILED", "fields": {}, "warnings": [], "currency": None}
        with SessionLocal.begin() as db:
            obj = db.scalar(select(InvoiceImport).where(InvoiceImport.id == import_id).with_for_update())
            if not obj or obj.suggestions.get("processing_token") != token: return
            obj.pages, obj.content_type, obj.method, obj.suggestions = pages, mime, method, result
            audit(db, db.get(User, obj.user_id), "INVOICE_EXTRACTED" if pages else "OCR_PROCESSING_FAILED", import_id=str(obj.id), method=method, processing_consent=consent)


@router.post("/jobs", status_code=202)
def start_job(background: BackgroundTasks, file: UploadFile = File(...), language: Literal["auto", "en", "vi", "zh"] = Form("auto"), file_consent=Depends(require_file_consent("invoice-ocr")), user=Depends(student), db=Depends(get_db, scope="function")):
    raw = file.file.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES:
        raise ApiError("DOCUMENT_TOO_LARGE", "Use a file of 1 byte to 5 MB", 413)
    filename = PurePosixPath((file.filename or "invoice").replace("\\", "/")).name
    filename = "".join(c for c in filename if ord(c) >= 32)[:180]
    if Path(filename).suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp", ".pdf", ".txt", ".md"):
        raise ApiError("DOCUMENT_TYPE_UNSUPPORTED", "Use PNG, JPG, WebP, PDF, TXT or MD", 422)
    # Serialize admission across accounts, without holding this lock during OCR.
    db.execute(text("SELECT pg_advisory_xact_lock(8320420)"))
    lock_user(db, user)
    sha = hashlib.sha256(raw).hexdigest()
    old = db.scalar(select(InvoiceImport).where(InvoiceImport.user_id == user.id, InvoiceImport.sha256 == sha).order_by(InvoiceImport.created_at.desc()))
    if old: expire_job(old)
    if old and (old.invoice_id or (old.suggestions.get("language", "auto") == language and old.suggestions.get("processing_status") != "FAILED")):
        return public_import(old)
    pending = list(db.scalars(select(InvoiceImport).where(InvoiceImport.suggestions["processing_status"].astext.in_(["QUEUED", "RUNNING"]))))
    for item in pending: expire_job(item)
    pending = [item for item in pending if item.suggestions.get("processing_status") in ("QUEUED", "RUNNING")]
    if len(pending) >= 4 or any(item.user_id == user.id for item in pending):
        raise ApiError("OCR_BUSY", "A document is already processing; wait for its result", 429)
    if not old and db.scalar(select(func.count()).select_from(InvoiceImport).where(InvoiceImport.user_id == user.id)) >= 100:
        raise ApiError("IMPORT_LIMIT", "Maximum 100 retained source files", 409)
    obj = old or InvoiceImport(user_id=user.id, filename=filename, original_bytes=raw, content_type="application/octet-stream", sha256=sha, pages=[], method="OCR_PENDING")
    obj.pages = []; obj.method = "OCR_PENDING"
    obj.suggestions = {"language": language, "processing_token": str(uuid4()), "processing_status": "QUEUED", "queued_at": now().isoformat(), "fields": {}, "warnings": [], "currency": None}
    db.add(obj); db.flush()
    result = public_import(obj); import_id = obj.id
    db.commit()  # Must be visible to the independent worker before its first read.
    background.add_task(process_import, import_id, file_consent)
    return result


@router.post("")
def upload(file: UploadFile = File(...), language: Literal["auto", "en", "vi", "zh"] = Form("auto"), file_consent=Depends(require_file_consent("invoice-ocr")), user=Depends(student), db=Depends(get_db, scope="function")):
    raw = file.file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ApiError("DOCUMENT_TOO_LARGE", "Maximum 5 MB", 413)
    filename = PurePosixPath((file.filename or "invoice").replace("\\", "/")).name
    filename = "".join(c for c in filename if ord(c) >= 32)[:180]
    sha = hashlib.sha256(raw).hexdigest()
    old = db.scalar(select(InvoiceImport).where(InvoiceImport.user_id == user.id, InvoiceImport.sha256 == sha).order_by(InvoiceImport.created_at.desc()))
    if old and (old.invoice_id or old.suggestions.get("language", "auto") == language):
        return public_import(old)
    if db.scalar(select(func.count()).select_from(InvoiceImport).where(InvoiceImport.user_id == user.id)) >= 100:
        raise ApiError("IMPORT_LIMIT", "Maximum 100 retained invoice source files", 409)
    pages, mime, method = extract_file(raw, filename, language)
    extracted = {**suggestions(pages), "language": language}
    obj = InvoiceImport(user_id=user.id, filename=filename, original_bytes=raw, content_type=mime, sha256=sha, pages=pages, suggestions=extracted, method=method)
    db.add(obj); db.flush()
    audit(db, user, "INVOICE_EXTRACTED", import_id=str(obj.id), method=method, processing_consent=file_consent)
    return public_import(obj)


def own_import(db, import_id, user):
    obj = db.scalar(select(InvoiceImport).where(InvoiceImport.id == import_id, InvoiceImport.user_id == user.id))
    if not obj:
        raise ApiError("IMPORT_NOT_FOUND", "Invoice source not found", 404)
    return obj


@router.get("/{import_id}")
def detail(import_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    obj = own_import(db, import_id, user)
    expire_job(obj)
    return public_import(obj)


def expire_job(obj):
    if obj.suggestions.get("processing_status") in ("QUEUED", "RUNNING") and (now() - datetime.fromisoformat(obj.suggestions["queued_at"]).astimezone(timezone.utc)).total_seconds() > 900:
        obj.suggestions = {**obj.suggestions, "processing_status": "FAILED", "error_code": "OCR_INTERRUPTED"}


@router.get("/{import_id}/download")
def download(import_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    obj = own_import(db, import_id, user)
    return Response(obj.original_bytes, media_type=obj.content_type, headers={"Content-Disposition": "attachment", "Cache-Control": "no-store"})


@router.get("/by-invoice/{invoice_id}")
def invoice_source(invoice_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    obj = db.scalar(select(InvoiceImport).where(InvoiceImport.invoice_id == invoice_id, InvoiceImport.user_id == user.id))
    return {"source": public_import(obj) if obj else None}

"""Local OCR + labelled field extraction. Document content never goes upstream."""
import hashlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import threading
import unicodedata
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from uuid import UUID
from typing import Literal
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from PIL import Image, ImageOps, UnidentifiedImageError
from pypdf import PdfReader
import pypdfium2 as pdfium
from sqlalchemy import select, func
from .config import ROOT, settings
from .file_consent import require_file_consent
from .db import get_db
from .models import InvoiceImport
from .security import student, ApiError
from .services import audit

router = APIRouter(prefix="/api/v1/invoice-imports", tags=["Reviewed local invoice OCR"])
slots = threading.BoundedSemaphore(settings.ocr_max_workers)
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
    fields = {}
    labels = {
        "invoice_number": r"(?:invoice\s*(?:no\.?|number|#)|ma\s*(?:hoa don|thong bao)|发票号码|发票编号|编号)",
        "institution_name": r"(?:issuer|institution|school|don vi phat hanh|开票单位|学校)",
        "beneficiary_name": r"(?:beneficiary|payee|recipient|ben nhan|收款单位|收款人)",
        "amount_cny": r"(?:amount\s*due|total\s*due|total|tong tien|so tien|应付金额|合计|金额)",
        "due_date": r"(?:due\s*date|pay\s*by|han thanh toan|缴费截止日期|截止日期|到期日)",
    }
    currency_text = plain("\n".join(p["text"] for p in pages))
    cny = bool(re.search(r"\bcny\b|\brmb\b|人民币|人民幣", currency_text))
    for page in pages:
        for line in page["text"].splitlines():
            canonical = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", line)
            for name, label in labels.items():
                if name in fields:
                    continue
                match = re.search(label + r"\s*[:：#\-]?\s*(.+)$", plain(canonical), re.I)
                if not match:
                    continue
                value = canonical[match.start(1):].strip(" :：\t")
                if name == "amount_cny":
                    other_currency = re.search(r"\b(?:usd|eur|vnd|gbp|jpy|krw)\b", plain(line))
                    value = amount_value(match.group(1)) if cny and not other_currency else None
                elif name == "due_date":
                    numbers = re.search(r"(\d{4})\s*[年/\-.]\s*(\d{1,2})\s*[月/\-.]\s*(\d{1,2})", value)
                    european = re.search(r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})", value)
                    try:
                        if numbers:
                            value = date(*map(int, numbers.groups())).isoformat()
                        elif european:
                            d, m, y = map(int, european.groups())
                            value = date(y, m, d).isoformat()
                        else:
                            value = None
                    except ValueError:
                        value = None
                elif name == "invoice_number":
                    value = value[:100]
                else:
                    value = value[:200]
                if value:
                    fields[name] = {"value": value, "page": page["page"], "source_line": line[:500]}
    return {"fields": fields, "currency": "CNY" if cny else None, "warnings": ([] if cny else ["Chưa xác định được tiền tệ CNY. Hãy kiểm tra đồng tiền trước khi nhập số tiền."]) + ["Đối chiếu tất cả trường với bản gốc trước khi lưu. OCR có thể đọc sai số và tên."]}


def local_ocr(images, language="auto"):
    if not all((ROOT / ".local/ocr-models" / f"{lang}.traineddata").is_file() for lang in ("eng", "chi_sim", "vie")):
        raise ApiError("OCR_NOT_READY", "Run python scripts/setup_ocr.py and npm install in frontend", 503)
    node = shutil.which("node")
    if not node:
        raise ApiError("OCR_NOT_READY", "Node.js is required for local OCR", 503)
    if not slots.acquire(blocking=False):
        raise ApiError("OCR_BUSY", "OCR is busy; retry shortly", 429)
    try:
        result = subprocess.run([node, str(ROOT / "scripts/ocr_runner.cjs")], input=json.dumps({"images": images, "language": language}), text=True, encoding="utf-8", capture_output=True, timeout=75, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
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
    return {"id": str(obj.id), "filename": obj.filename, "method": obj.method, "pages": obj.pages, "suggestions": obj.suggestions, "invoice_id": str(obj.invoice_id) if obj.invoice_id else None, "requires_review": True}


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
    return public_import(own_import(db, import_id, user))


@router.get("/{import_id}/download")
def download(import_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    obj = own_import(db, import_id, user)
    return Response(obj.original_bytes, media_type=obj.content_type, headers={"Content-Disposition": "attachment", "Cache-Control": "no-store"})


@router.get("/by-invoice/{invoice_id}")
def invoice_source(invoice_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    obj = db.scalar(select(InvoiceImport).where(InvoiceImport.invoice_id == invoice_id, InvoiceImport.user_id == user.id))
    return {"source": public_import(obj) if obj else None}

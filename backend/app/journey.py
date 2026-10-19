"""Owner-scoped journey progress, public test inputs and downloadable case evidence."""
import hashlib
import io
import json
import shutil
from pathlib import PurePosixPath
from uuid import UUID
from zipfile import ZipFile, ZIP_DEFLATED
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select, func
from .config import ROOT, settings
from .db import get_db
from .models import Invoice, InvoiceImport, Order, Quote, Event, Audit, Receipt, FinancePlan, FinanceEntry, FinanceWallet, PolicyDocument, now
from .security import student, ApiError
from .services import serialize, own_invoice, own_order, iso
from .finance import wallet_out, plan_out

router = APIRouter(prefix="/api/v1", tags=["Guided acceptance journey"])
SAMPLES = ROOT / "fixtures/uploads"


def catalogue():
    return json.loads((ROOT / "fixtures/upload_catalog.json").read_text(encoding="utf-8"))


@router.get("/test-lab/catalog")
def catalog(user=Depends(student)):
    data = catalogue()
    return {"samples": [{**{k: v for k, v in item.items() if k != "relative_path"}, "download_url": f"/api/v1/test-lab/samples/{item['id']}"} for item in data["samples"]], "public_sources": data["public_sources"], "notice": "Generated examples are synthetic; public reference originals retain their own provenance and rights."}


@router.get("/test-lab/samples/{sample_id}")
def sample(sample_id: str, user=Depends(student)):
    item = next((item for item in catalogue()["samples"] if item["id"] == sample_id), None)
    if not item:
        raise ApiError("SAMPLE_NOT_FOUND", "Test sample not found", 404)
    path = (SAMPLES / item["relative_path"]).resolve()
    if not path.is_relative_to(SAMPLES.resolve()) or not path.is_file():
        raise ApiError("SAMPLE_NOT_FOUND", "Test sample not installed", 404)
    return Response(path.read_bytes(), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="{path.name}"'})


@router.get("/test-lab/download")
def sample_pack(user=Depends(student)):
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        for path in sorted(SAMPLES.rglob("*")):
            if path.is_file() and path.resolve().is_relative_to(SAMPLES.resolve()):
                archive.writestr("Demo_Upload_Test/" + path.relative_to(SAMPLES).as_posix(), path.read_bytes())
        for path in sorted((ROOT / "fixtures/china_upload_samples").iterdir()):
            if path.is_file(): archive.writestr("China_Current_Samples/" + path.name, path.read_bytes())
    return Response(stream.getvalue(), media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="Demo_Upload_Test.zip"'})


@router.get("/test-lab/status")
def status(invoice_id: UUID | None = None, user=Depends(student), db=Depends(get_db, scope="function")):
    invoice = own_invoice(db, invoice_id, user) if invoice_id else db.scalar(select(Invoice).where(Invoice.student_id == user.id).order_by(Invoice.created_at.desc()).limit(1))
    source = db.scalar(select(InvoiceImport).where(InvoiceImport.invoice_id == invoice.id, InvoiceImport.user_id == user.id)) if invoice else None
    plan = db.scalar(select(FinancePlan).where(FinancePlan.invoice_id == invoice.id, FinancePlan.user_id == user.id)) if invoice else None
    orders = list(db.scalars(select(Order).where(Order.invoice_id == invoice.id, Order.student_id == user.id).order_by(Order.created_at.desc()))) if invoice else []
    current = orders[0] if orders else None
    entries = list(db.scalars(select(FinanceEntry).where(FinanceEntry.plan_id == plan.id, FinanceEntry.user_id == user.id, FinanceEntry.status == "POSTED"))) if plan else []
    quotes = db.scalar(select(func.count()).select_from(Quote).where(Quote.invoice_id == invoice.id, Quote.student_id == user.id)) if invoice else 0
    document_count = db.scalar(select(func.count()).select_from(PolicyDocument).where(PolicyDocument.user_id == user.id))
    return {"invoice": {"id": str(invoice.id), "number": invoice.invoice_number, "amount_cny": format(invoice.amount_cny, ".2f")} if invoice else None,
            "order": {"id": str(current.id), "status": current.status, "scenario": current.sandbox_scenario} if current else None,
            "steps": {"reviewed_invoice": bool(invoice and source), "invoice_saved": bool(invoice), "budget_plan": bool(plan and plan.active), "reference_estimate": bool(quotes), "policy_uploaded": bool(document_count), "sandbox_complete": any(o.status == "SUCCEEDED" for o in orders), "ledger_recorded": bool(entries)},
            "readiness": {"ocr": bool(shutil.which("node") and (ROOT / "frontend/node_modules/tesseract.js").is_dir() and all((ROOT / ".local/ocr-models" / f"{lang}.traineddata").is_file() for lang in ("eng", "vie", "chi_sim"))), "payment_worker": bool(settings.demo_mode and settings.provider_worker_enabled), "real_payments": False},
            "notice": "Progress is derived from owned records. Ledger confirmation remains separate from sandbox payment."}


@router.get("/orders/{order_id}/evidence")
def evidence(order_id: UUID, user=Depends(student), db=Depends(get_db, scope="function")):
    order = own_order(db, order_id, user, lock=True)
    invoice = own_invoice(db, order.invoice_id, user)
    source = db.scalar(select(InvoiceImport).where(InvoiceImport.invoice_id == invoice.id, InvoiceImport.user_id == user.id))
    plan = db.scalar(select(FinancePlan).where(FinancePlan.invoice_id == invoice.id, FinancePlan.user_id == user.id))
    event_rows = list(db.scalars(select(Event).where(Event.order_id == order.id).order_by(Event.received_at)))
    logs = list(db.scalars(select(Audit).where(Audit.order_id == order.id).order_by(Audit.created_at)))
    receipt = db.scalar(select(Receipt).where(Receipt.order_id == order.id))
    case = {"product": "Demo", "exported_at": iso(now()), "notice": "SIMULATED TRANSACTION — NO REAL FUNDS MOVED", "invoice": {k: v for k, v in serialize(invoice).items() if k != "student_id"}, "order": {k: v for k, v in serialize(order).items() if k != "student_id"}, "quote": {k: v for k, v in serialize(db.get(Quote, order.quote_id)).items() if k != "student_id"},
            "events": [{k: v for k, v in serialize(row).items() if k not in ("payload_sha256", "transaction_id")} for row in event_rows],
            "audit": [{"actor_type": row.actor_type, "action": row.action, "created_at": iso(row.created_at), "details": row.safe_metadata} for row in logs],
            "receipt": serialize(receipt) if order.status == "SUCCEEDED" and receipt else None,
            "source": {"filename": source.filename, "sha256": source.sha256, "method": source.method, "suggestions": source.suggestions} if source else None}
    if plan:
        wallet = db.get(FinanceWallet, plan.wallet_id)
        case["budget_plan"] = plan_out(plan, wallet)
        case["wallet_snapshot"] = wallet_out(db, wallet)
        case["ledger_entries"] = [{k: v for k, v in serialize(row).items() if k not in ("user_id", "request_key", "request_hash")} for row in db.scalars(select(FinanceEntry).where(FinanceEntry.plan_id == plan.id, FinanceEntry.user_id == user.id))]
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("case.json", json.dumps(case, ensure_ascii=False, indent=2))
        if source:
            filename = PurePosixPath(source.filename.replace("\\", "/")).name
            archive.writestr("source/" + filename, source.original_bytes)
        archive.writestr("README.txt", "Demo owner-exported test evidence.\nAll payment outcomes are simulated. No real funds moved.\ncase.json records the invoice, reviewed source provenance, quote, consent, provider events and any linked budget plan.\nThe source directory may contain your private original document. Share intentionally.\nA sandbox receipt is not a bank receipt or insurance certificate.\n")
        archive.writestr("checksums.json", json.dumps({"original_source_sha256": hashlib.sha256(source.original_bytes).hexdigest() if source else None}, indent=2))
    return Response(stream.getvalue(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="demo-case-{order.id}.zip"'})

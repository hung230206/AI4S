"""Reproduce real API operations and export sanitized judge evidence (no credentials)."""
import os
from pathlib import Path
import sys
import uuid
import json
from datetime import timedelta
from decimal import Decimal

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
os.environ["PROVIDER_WORKER_ENABLED"] = "false"
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.config import settings
from app.db import SessionLocal
from app.models import Invoice, Quote, now
from app.seed import STUDENT_ID, seed
from app.providers import deliver_pending
import asyncio


def checked(response, expected=200):
    assert response.status_code == expected, response.text
    return response.json()


def fixture(label):
    with SessionLocal.begin() as db:
        original = db.get(Invoice, uuid.UUID("11111111-1111-4111-8111-111111111111"))
        obj = Invoice(student_id=STUDENT_ID, invoice_number=f"EVIDENCE-{label}-{uuid.uuid4().hex[:8]}", country_code="CN", institution_name=original.institution_name, beneficiary_name=original.beneficiary_name, fee_type=original.fee_type, amount_cny=Decimal("800.00"), due_date=now().date() + timedelta(days=30))
        db.add(obj)
        db.flush()
        return str(obj.id)


def main():
    with SessionLocal.begin() as db:
        seed(db)
    results = []
    with TestClient(app) as client:
        token = checked(client.post("/api/v1/demo/session", json={"role": "STUDENT"}))["access_token"]
        operator = checked(client.post("/api/v1/demo/session", json={"role": "OPERATOR", "operator_code": settings.demo_operator_code}))["access_token"]
        sh = {"Authorization": "Bearer " + token}
        oh = {"Authorization": "Bearer " + operator}
        for label in ("success", "failure", "expiry", "cancellation"):
            invoice_id = fixture(label)
            q = checked(client.post("/api/v1/quotes", headers=sh, json={"invoice_id": invoice_id, "settlement_currency": "VND"}))
            o = checked(client.post("/api/v1/orders", headers={**sh, "Idempotency-Key": str(uuid.uuid4())}, json={"invoice_id": invoice_id, "quote_id": q["id"]}))
            event_id = None
            if label == "cancellation":
                checked(client.post(f"/api/v1/orders/{o['id']}/cancel", headers=sh))
            else:
                if label == "expiry":
                    # Controlled expiry without a ten-minute wait. Test environment data only.
                    with SessionLocal.begin() as db:
                        saved = db.get(Quote, uuid.UUID(q["id"]))
                        saved.created_at = now() - timedelta(minutes=20)
                        saved.expires_at = now() - timedelta(minutes=10)
                result = client.post(f"/api/v1/orders/{o['id']}/confirm", headers={**sh, "Idempotency-Key": str(uuid.uuid4())}, json={"quote_id": q["id"], "consent": True, "consent_version": "demo-v1", "expected_total_vnd": q["total_vnd"]})
                checked(result, 409 if label == "expiry" else 200)
                if label != "expiry":
                    queued = checked(client.post(f"/api/v1/demo/orders/{o['id']}/simulate", headers=oh, json={"outcome": "SUCCEEDED" if label == "success" else "FAILED"}))
                    event_id = queued["external_event_id"]
                    asyncio.run(deliver_pending(app))
                    if label == "success":
                        checked(client.post(f"/api/v1/demo/events/{event_id}/replay", headers=oh))
                        asyncio.run(deliver_pending(app))
            final = checked(client.get(f"/api/v1/orders/{o['id']}", headers=sh))
            trace = checked(client.get(f"/api/v1/orders/{o['id']}/events", headers=sh))
            receipt = client.get(f"/api/v1/orders/{o['id']}/receipt", headers=sh)
            results.append({"scenario": label, "order": final, "trace": trace, "receipt_http_status": receipt.status_code, "receipt": receipt.json() if receipt.is_success else None})
    expected = ["SUCCEEDED", "FAILED", "EXPIRED", "CANCELLED"]
    assert [r["order"]["status"] for r in results] == expected
    output = {"captured_at": now().isoformat(), "environment": "LOCAL MOCK; NO REAL FUNDS", "expiry_method": "Controlled fixture timestamp change, then real confirmation API rejection", "results": results}
    destination = root / "submission/evidence/operations.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Evidence:", ", ".join(expected), "+ duplicate signed event audited; exported submission/evidence/operations.json")


if __name__ == "__main__":
    main()

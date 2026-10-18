import asyncio
import io
import json
from datetime import timedelta
from uuid import UUID, uuid4
from zipfile import ZipFile
import pytest
from sqlalchemy import select, func
from app.config import ROOT, settings
from app.db import SessionLocal
from app.main import app
from app.models import ProviderEvent, Order, User, Receipt, now
from app.providers import deliver_pending
from app.security import signer
from test_payments import quote, order, confirm

P = "/api/v1"


@pytest.mark.parametrize("scenario,outcome", [("SUCCESS", "SUCCEEDED"), ("DECLINED", "FAILED")])
def test_provider_method_is_delayed_signed_and_idempotent(client, student_headers, scenario, outcome, monkeypatch):
    monkeypatch.setattr(settings, "provider_worker_enabled", True)
    o = order(client, student_headers)
    first = confirm(client, student_headers, o, sandbox_scenario=scenario)
    assert first.status_code == 200
    assert first.json()["status"] == "PROCESSING"
    assert first.json()["sandbox_scenario"] == scenario
    again = confirm(client, student_headers, o, sandbox_scenario=scenario)
    assert again.json() == first.json()
    with SessionLocal.begin() as db:
        assert db.scalar(select(func.count()).select_from(ProviderEvent)) == 1
    asyncio.run(deliver_pending(app))
    assert client.get(f"{P}/orders/{o['id']}", headers=student_headers).json()["status"] == "PROCESSING"
    with SessionLocal.begin() as db:
        event = db.scalar(select(ProviderEvent))
        event.available_at = now() - timedelta(seconds=1)
    asyncio.run(deliver_pending(app))
    assert client.get(f"{P}/orders/{o['id']}", headers=student_headers).json()["status"] == outcome
    trace = client.get(f"{P}/orders/{o['id']}/events", headers=student_headers).json()
    assert len(trace["items"]) == 1 and trace["items"][0]["signature_verified"]
    with SessionLocal.begin() as db:
        event = db.scalar(select(ProviderEvent)); event.delivered = False
    asyncio.run(deliver_pending(app))
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Receipt)) == (1 if outcome == "SUCCEEDED" else 0)
    exported = client.get(f"{P}/orders/{o['id']}/evidence", headers=student_headers)
    assert exported.status_code == 200
    with ZipFile(io.BytesIO(exported.content)) as archive:
        case = json.loads(archive.read("case.json"))
        assert bool(case["receipt"]) == (outcome == "SUCCEEDED")
        assert "NO REAL FUNDS MOVED" in case["notice"]


def test_auto_method_still_requires_consent_and_no_side_effect_on_rejection(client, student_headers):
    o = order(client, student_headers)
    assert confirm(client, student_headers, o, consent=False, sandbox_scenario="SUCCESS").status_code == 422
    assert confirm(client, student_headers, o, sandbox_scenario="ARBITRARY").status_code == 422
    assert confirm(client, student_headers, o, sandbox_scenario="SUCCESS", expected_total_vnd="1").status_code == 409
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(ProviderEvent)) == 0
        assert db.get(Order, UUID(o["id"])).status == "AWAITING_CONFIRMATION"


def test_test_method_disabled_without_demo_and_retries_bind_scenario(client, student_headers, monkeypatch):
    o = order(client, student_headers)
    monkeypatch.setattr(settings, "demo_mode", False)
    assert confirm(client, student_headers, o, sandbox_scenario="SUCCESS").status_code in (403, 503)
    monkeypatch.setattr(settings, "demo_mode", True)
    monkeypatch.setattr(settings, "provider_worker_enabled", True)
    assert confirm(client, student_headers, o, sandbox_scenario="SUCCESS").status_code == 200
    assert confirm(client, student_headers, o, sandbox_scenario="DECLINED").status_code == 409
    assert client.post(f"{P}/demo/orders/{o['id']}/simulate", headers=student_headers, json={"outcome": "SUCCEEDED"}).status_code == 403


def test_disabled_worker_rejects_automatic_method_before_provider_intent(client, student_headers):
    o = order(client, student_headers)
    response = confirm(client, student_headers, o, sandbox_scenario="SUCCESS")
    assert response.status_code == 503 and response.json()["error"]["code"] == "SANDBOX_WORKER_UNAVAILABLE"
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(ProviderEvent)) == 0
        assert db.get(Order, UUID(o["id"])).status == "AWAITING_CONFIRMATION"


def test_manual_path_retained(client, student_headers):
    o = order(client, student_headers)
    assert confirm(client, student_headers, o).status_code == 200
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(ProviderEvent)) == 0
    assert client.get(f"{P}/orders/{o['id']}", headers=student_headers).json()["sandbox_scenario"] == "MANUAL"


def test_catalog_and_download_only_allow_fixed_public_fixtures(client, student_headers):
    catalog = client.get(P + "/test-lab/catalog", headers=student_headers).json()
    assert len(catalog["samples"]) >= 15
    assert all("relative_path" not in item for item in catalog["samples"])
    one = catalog["samples"][0]
    response = client.get(one["download_url"], headers=student_headers)
    assert response.status_code == 200
    assert response.content == (ROOT / "fixtures/uploads/01_Hoa_don/01_en_800.png").read_bytes()
    assert client.get(P + "/test-lab/samples/not-an-id", headers=student_headers).status_code == 404
    assert client.get(P + "/test-lab/catalog").status_code == 401
    pack = client.get(P + "/test-lab/download", headers=student_headers)
    with ZipFile(io.BytesIO(pack.content)) as archive:
        assert archive.testzip() is None
        assert not any(".env" in n or "public-reference" in n or ".." in n for n in archive.namelist())


def test_evidence_original_bytes_and_owner_boundary(client, student_headers):
    raw = b"Invoice number: ORIGINAL-CASE\nIssuer: Demo School\nBeneficiary: Demo Education\nTotal due: CNY 800.00\nDue date: 2026-12-20\nSelf-authored QA fixture."
    draft = client.post(P + "/invoice-imports", headers=student_headers, files={"file": ("source.txt", raw, "text/plain")}).json()
    fields = {k: v["value"] for k, v in draft["suggestions"]["fields"].items()}
    inv = client.post(P + "/invoices", headers=student_headers, json={**fields, "import_id": draft["id"], "import_reviewed": True}).json()
    o = order(client, student_headers, quote(client, student_headers, inv["id"]))
    response = client.get(f"{P}/orders/{o['id']}/evidence", headers=student_headers)
    assert response.status_code == 200
    with ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.read("source/source.txt") == raw
        case = json.loads(archive.read("case.json"))
        assert case["source"]["method"] == "TEXT_EXTRACT"
        assert case["receipt"] is None
        assert "token_hash" not in json.dumps(case) and "csrf_token" not in json.dumps(case)
    with SessionLocal.begin() as db:
        other = User(display_name="Other isolated tester", role="STUDENT", is_demo=True)
        db.add(other); db.flush(); uid = str(other.id)
    headers = {"Authorization": "Bearer " + signer.dumps({"sub": uid, "role": "STUDENT"})}
    assert client.get(f"{P}/orders/{o['id']}/evidence", headers=headers).status_code == 404
    assert client.get(P + f"/test-lab/status?invoice_id={inv['id']}", headers=headers).status_code == 404
    progress = client.get(P + f"/test-lab/status?invoice_id={inv['id']}", headers=student_headers).json()
    assert progress["steps"]["reviewed_invoice"] and progress["steps"]["reference_estimate"]
    assert not progress["steps"]["sandbox_complete"] and not progress["steps"]["ledger_recorded"]


def test_public_reference_requires_source_and_retains_declared_kind(client, student_headers):
    raw = b"Self-authored test document. Claims require invoices. Not a real insurance policy."
    no_source = client.post(P + "/documents", headers=student_headers, data={"document_kind": "PUBLIC_REFERENCE"}, files={"file": ("example.txt", raw, "text/plain")})
    assert no_source.status_code == 422 and no_source.json()["error"]["code"] == "DOCUMENT_SOURCE_REQUIRED"
    result = client.post(P + "/documents", headers=student_headers, data={"document_kind": "PUBLIC_REFERENCE", "source_url": "https://example.edu/public-test-policy"}, files={"file": ("example.txt", raw, "text/plain")})
    assert result.status_code == 200 and result.json()["document_kind"] == "PUBLIC_REFERENCE"
    matches = client.post(P + "/documents/search", headers=student_headers, json={"question": "claims", "document_id": result.json()["id"]}).json()["matches"]
    assert matches[0]["document_kind"] == "PUBLIC_REFERENCE"
    assert matches[0]["source_url"] == "https://example.edu/public-test-policy"


def test_unknown_document_provenance_is_rejected(client, student_headers):
    response = client.post(P + "/documents", headers=student_headers, data={"document_kind": "ISSUER_VERIFIED"}, files={"file": ("fixture.txt", b"Synthetic test document with readable content.", "text/plain")})
    assert response.status_code == 422

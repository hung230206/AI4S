import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4
from zipfile import ZipFile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app
from app import fx
from app.db import SessionLocal
from app.models import InsurancePolicy, InsuranceClaim, FinancePlan, FinanceEntry, Order
from app.finance import today

P = "/api/v1"


@pytest.fixture(autouse=True)
def reference(monkeypatch):
    monkeypatch.setattr(fx, "fetch_json", lambda *a, **k: {"date": fx.now().date().isoformat(), "base": "CNY", "quote": "VND", "rate": "3864.07"})


def data(client, headers):
    result = client.get(P + "/insurance/sample-pack", headers=headers)
    assert result.status_code == 200
    with ZipFile(io.BytesIO(result.content)) as z:
        files = {name: z.read(name) for name in z.namelist()}
    document = client.post(P + "/documents", headers=headers, data={"document_kind": "TEST_FIXTURE"}, files={"file": ("demo-policy.txt", files["demo-policy.txt"], "text/plain")})
    assert document.status_code == 200, document.text
    body = {**json.loads(files["review-fields.json"]), "document_id": document.json()["id"], "reviewed": True, "request_key": str(uuid4())}
    return body, files


def create(client, headers):
    body, files = data(client, headers)
    response = client.post(P + "/insurance/policies", headers=headers, json=body)
    assert response.status_code == 200, response.text
    return response.json(), body, files


def new_claim(client, h, policy, **overrides):
    body = {"policy_id": policy["id"], "title": "Self-authored outpatient test", "benefit_kind": "OUTPATIENT", "incident_date": str(today()), "amount": "500.00", "request_key": str(uuid4()), **overrides}
    r = client.post(P + "/insurance/claims", headers=h, json=body)
    assert r.status_code == 200, r.text
    return r.json(), body


def make_ready(client, h, claim):
    for item in claim["checklist"]:
        r = client.post(f"{P}/insurance/claims/{claim['id']}/checklist", headers=h, json={"revision": claim["revision"], "code": item["code"], "prepared_externally": True})
        assert r.status_code == 200, r.text
        claim = r.json()
    r = client.post(f"{P}/insurance/claims/{claim['id']}/transition", headers=h, json={"revision": claim["revision"], "status": "READY", "confirmed": True})
    assert r.status_code == 200, r.text
    return r.json()


def test_review_citations_and_idempotent_creation(client, student_headers):
    h = student_headers; policy, body, _ = create(client, h)
    assert policy["document_kind"] == "TEST_FIXTURE" and policy["revision"] == 1
    assert client.post(P + "/insurance/policies", headers=h, json=body).json()["id"] == policy["id"]
    assert client.post(P + "/insurance/policies", headers=h, json={**body, "premium": "999"}).status_code == 409
    assert client.get(P + "/insurance/policies", headers=h).json()["items"][0]["benefits"][0]["limit"] == "2000.00"


@pytest.mark.parametrize("change", ["no_review", "wrong_quote", "wrong_page", "blank_name", "duplicate_benefit", "boolean_percent", "excluded_amount", "negative_dates"])
def test_policy_rejects_unreviewed_unsupported_or_malformed_fields(client, student_headers, change):
    body, _ = data(client, student_headers)
    if change == "no_review": body["reviewed"] = False
    if change == "wrong_quote": body["benefits"][0]["evidence_quote"] = "This made up clause is not in the source."
    if change == "wrong_page": body["benefits"][0]["source_page"] = 2
    if change == "blank_name": body["name"] = "   "
    if change == "duplicate_benefit": body["benefits"][1] = body["benefits"][0]
    if change == "boolean_percent": body["benefits"][0]["reimbursement_percent"] = True
    if change == "excluded_amount": body["benefits"][-1]["limit"] = "2000"
    if change == "negative_dates": body["ends_on"] = str(today() - timedelta(days=100))
    r = client.post(P + "/insurance/policies", headers=student_headers, json=body)
    assert r.status_code == 422, r.text


def test_budget_bridge_forecast_precision_no_payment_and_retry(client, student_headers):
    h = student_headers; policy, body, _ = create(client, h)
    wallet = client.post(P + "/finance/wallets", headers=h, json={"name": "Premium CNY", "currency": "CNY", "opening_balance": "1000", "opening_date": str(today())}).json()
    plan_body = {"wallet_id": wallet["id"], "revision": policy["revision"], "reviewed": True}
    r = client.post(f"{P}/insurance/policies/{policy['id']}/plan", headers=h, json=plan_body)
    assert r.status_code == 200, r.text
    assert r.json()["wallet"]["balance"] == "1000.00" and r.json()["plan"]["amount"] == "800.00"
    assert client.post(f"{P}/insurance/policies/{policy['id']}/plan", headers=h, json=plan_body).json()["reused"]
    forecast = client.get(P + "/finance/forecast", headers=h).json()
    assert forecast["wallets"][0]["projected_balance"] == "200.00"
    body.update(revision=1, premium="900")
    changed = client.post(f"{P}/insurance/policies/{policy['id']}/update", headers=h, json=body)
    assert changed.status_code == 200 and changed.json()["plan_needs_review"] is True
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(FinancePlan)) == 1
        assert db.scalar(select(func.count()).select_from(FinanceEntry)) == 0
        assert db.scalar(select(func.count()).select_from(Order)) == 0
    assert client.post(f"{P}/insurance/policies/{policy['id']}/update", headers=h, json=body).status_code == 409


def test_premium_estimate_links_real_reference_quote_but_no_funds(client, student_headers):
    h = student_headers; policy, _, _ = create(client, h)
    path = f"{P}/insurance/policies/{policy['id']}/premium-invoice"
    body = {"revision": 1, "reviewed": True}
    r = client.post(path, headers=h, json=body)
    assert r.status_code == 200, r.text
    invoice = r.json()["invoice"]
    assert "NOT AN INSURER-ISSUED" in invoice["notes"]
    assert client.post(path, headers=h, json=body).json()["invoice"]["id"] == invoice["id"]
    quote = client.post(P + "/quotes", headers=h, json={"invoice_id": invoice["id"], "settlement_currency": "VND"})
    assert quote.status_code == 200, quote.text
    assert quote.json()["source_amount_cny"] == "800.00" and quote.json()["rate_source"] == "FRANKFURTER_REFERENCE"
    assert client.get(P + "/orders", headers=h).json()["items"] == []


def test_comparison_gap_unknown_waiting_territory_period_and_overlap(client, student_headers):
    h = student_headers; p, body, _ = create(client, h)
    request = {"starts_on": str(today()), "ends_on": str(today() + timedelta(days=30)), "country": "CN", "currency": "CNY", "needs": [{"kind": "OUTPATIENT", "minimum_limit": "2000"}, {"kind": "EVACUATION", "minimum_limit": "50000"}]}
    r = client.post(P + "/insurance/analysis", headers=h, json=request).json()
    assert [x["status"] for x in r["results"]] == ["MEETS_ENTERED_REQUIREMENT", "GAP_IN_ENTERED_PORTFOLIO"]
    body["request_key"] = str(uuid4())
    assert client.post(P + "/insurance/policies", headers=h, json=body).status_code == 200
    r = client.post(P + "/insurance/analysis", headers=h, json=request).json()
    assert r["results"][0]["possible_overlap"] is True and r["results"][0]["matching_policy_count"] == 2
    request["needs"] = [{"kind": "OUTPATIENT", "minimum_limit": "4000"}]
    r = client.post(P + "/insurance/analysis", headers=h, json=request).json()
    assert r["results"][0]["status"] == "GAP_IN_ENTERED_PORTFOLIO"  # 2000 + 2000 never adds to 4000.
    for field, value, reason in [("country", "VN", "TERRITORY_MISMATCH"), ("currency", "VND", "CURRENCY_MISMATCH"), ("ends_on", str(today()+timedelta(days=400)), "PERIOD_GAP")]:
        changed = {**request, field: value}
        r = client.post(P + "/insurance/analysis", headers=h, json=changed).json()
        assert reason in r["results"][0]["policies"][0]["reasons"]
    body["benefits"][0]["waiting_days"] = None; body["revision"] = 1
    client.post(f"{P}/insurance/policies/{p['id']}/update", headers=h, json=body)
    r = client.post(P + "/insurance/analysis", headers=h, json=request).json()
    assert r["results"][0]["status"] == "NEEDS_INFORMATION"


def test_claim_full_checklist_original_bytes_export_and_external_state(client, student_headers):
    h = student_headers; policy, _, files = create(client, h); claim, body = new_claim(client, h, policy)
    assert client.post(P + "/insurance/claims", headers=h, json=body).json()["id"] == claim["id"]
    base = f"{P}/insurance/claims/{claim['id']}"
    assert client.post(base + "/transition", headers=h, json={"revision": 1, "status": "READY", "confirmed": True}).status_code == 422
    for code, name in [("INVOICE", "claim-invoice.txt"), ("MEDICAL_RECORD", "claim-medical-record.txt"), ("CLAIM_FORM", "claim-claim-form.txt")]:
        r = client.post(base + "/attachments", headers=h, data={"item_code": code, "revision": claim["revision"]}, files={"file": (name, files[name], "text/plain")})
        assert r.status_code == 200, r.text
        claim = r.json()
    item = claim["attachments"][0]
    original = client.get(base + "/attachments/" + item["id"], headers=h)
    assert hashlib.sha256(original.content).hexdigest() == item["sha256"]
    for code in ("IDENTITY_OFFLINE", "BANK_DETAILS_OFFLINE"):
        claim = client.post(base + "/checklist", headers=h, json={"revision": claim["revision"], "code": code, "prepared_externally": True}).json()
    assert claim["ready"] is True
    claim = client.post(base + "/transition", headers=h, json={"revision": claim["revision"], "status": "READY", "confirmed": True}).json()
    assert claim["status"] == "READY"
    # Editing checklist invalidates readiness review, even if all files remain present.
    changed = client.post(base + "/checklist", headers=h, json={"revision": claim["revision"], "code": "IDENTITY_OFFLINE", "prepared_externally": False})
    assert changed.json()["status"] == "DRAFT" and changed.json()["ready"] is False
    claim = make_ready(client, h, changed.json())
    assert client.post(base + "/transition", headers=h, json={"revision": claim["revision"], "status": "SUBMITTED_EXTERNALLY", "confirmed": True}).status_code == 422
    claim = client.post(base + "/transition", headers=h, json={"revision": claim["revision"], "status": "SUBMITTED_EXTERNALLY", "confirmed": True, "note": "Test record only; no actual submission."}).json()
    assert claim["status"] == "SUBMITTED_EXTERNALLY"
    assert client.post(base + "/checklist", headers=h, json={"revision": claim["revision"], "code": "INVOICE", "prepared_externally": False}).status_code == 409
    export = client.get(base + "/export", headers=h)
    with ZipFile(io.BytesIO(export.content)) as archive:
        report = json.loads(archive.read("claim-preparation.json"))
        assert report["status"] == "SUBMITTED_EXTERNALLY"
        assert archive.read("policy-original/demo-policy.txt") == files["demo-policy.txt"]
        for attachment in report["attachments"]:
            raw = archive.read("attachments/" + attachment["id"] + "-" + attachment["filename"])
            assert hashlib.sha256(raw).hexdigest() == attachment["sha256"]
        assert b"NOT SUBMITTED TO AN INSURER" in archive.read("README.txt")
    assert client.get(P + "/finance/entries", headers=h).json()["items"] == []
    assert client.get(P + "/orders", headers=h).json()["items"] == []


@pytest.mark.parametrize("kind,expected", [("INPATIENT", "DISCHARGE"), ("ACCIDENT", "ACCIDENT_REPORT")])
def test_claim_checklist_changes_by_kind_and_snapshot_preserved(client, student_headers, kind, expected):
    h = student_headers; policy, body, _ = create(client, h)
    claim, _ = new_claim(client, h, policy, benefit_kind=kind)
    assert expected in [x["code"] for x in claim["checklist"]]
    body.update(revision=1, premium="900", name="Updated summary")
    assert client.post(f"{P}/insurance/policies/{policy['id']}/update", headers=h, json=body).status_code == 200
    saved = client.get(f"{P}/insurance/claims/{claim['id']}", headers=h).json()
    assert saved["policy_snapshot"]["premium"] == "800.00" and saved["policy_snapshot"]["revision"] == 1


@pytest.mark.parametrize("code,name,raw,expected", [("IDENTITY_OFFLINE", "passport.txt", b"do not collect identity", 422), ("INVOICE", "bad.pdf", b"this is not pdf", 422), ("INVOICE", "script.html", b"<script>1</script>", 422), ("INVOICE", "big.txt", b"x"*5242881, 413)], ids=["identity-rejected", "bad-pdf", "html-rejected", "oversize"])
def test_attachment_category_type_and_size_guards(client, student_headers, code, name, raw, expected):
    h = student_headers; policy, _, _ = create(client, h); claim, _ = new_claim(client, h, policy)
    result = client.post(f"{P}/insurance/claims/{claim['id']}/attachments", headers=h, data={"revision": claim["revision"], "item_code": code}, files={"file": (name, raw, "application/octet-stream")})
    assert result.status_code == expected


def test_private_account_isolation_and_csrf(client, student_headers):
    h = student_headers; policy, body, _ = create(client, h); claim, _ = new_claim(client, h, policy)
    user = client.post(P + "/auth/register", json={"email": f"privacy-{uuid4()}@example.com", "display_name": "Second account", "password": "insurance-private-test-2026"}).json()
    second = {"X-CSRF-Token": user["csrf_token"]}
    assert client.get(P + "/insurance/policies").json()["items"] == []
    assert client.get(P + "/insurance/claims").json()["items"] == []
    for path in [f"/insurance/claims/{claim['id']}", f"/insurance/claims/{claim['id']}/export"]:
        assert client.get(P + path).status_code == 404
    assert client.post(f"{P}/insurance/policies/{policy['id']}/archive", headers=second, json={"revision": 1}).status_code == 404
    body["request_key"] = str(uuid4())
    assert client.post(P + "/insurance/policies", headers=second, json=body).status_code == 404
    assert client.post(P + "/insurance/policies", json=body).status_code == 403
    assert client.get(P + "/insurance/overview").json()["reminders"] == []


def test_concurrent_retries_create_one_policy_and_one_case(client, student_headers):
    h = student_headers; body, _ = data(client, h)
    def create_same(_):
        with TestClient(app) as other: return other.post(P + "/insurance/policies", headers=h, json=body)
    with ThreadPoolExecutor(max_workers=3) as pool: results = list(pool.map(create_same, range(3)))
    assert [r.status_code for r in results] == [200, 200, 200]
    assert len({r.json()["id"] for r in results}) == 1
    policy = results[0].json()
    _, claim_body = new_claim(client, h, policy)
    def create_case(_):
        with TestClient(app) as other: return other.post(P + "/insurance/claims", headers=h, json=claim_body)
    with ThreadPoolExecutor(max_workers=3) as pool: results = list(pool.map(create_case, range(3)))
    assert all(r.status_code == 200 for r in results)
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(InsurancePolicy)) == 1
        assert db.scalar(select(func.count()).select_from(InsuranceClaim)) == 1


def test_reminders_and_retained_source(client, student_headers):
    h = student_headers; policy, _, _ = create(client, h)
    reminders = client.get(P + "/insurance/overview", headers=h).json()["reminders"]
    assert reminders[0]["kind"] == "PREMIUM_UNPLANNED"
    assert client.post(f"{P}/documents/{policy['document_id']}/delete", headers=h).status_code == 409
    assert client.post(f"{P}/insurance/policies/{policy['id']}/archive", headers=h, json={"revision": 1}).status_code == 200
    assert client.get(P + "/insurance/overview", headers=h).json()["active_policies"] == 0
    restored = client.post(f"{P}/insurance/policies/{policy['id']}/restore", headers=h, json={"revision": 2})
    assert restored.status_code == 200 and restored.json()["active"] is True


def test_corrections_remove_attachment_and_old_source_survives_policy_change(client, student_headers):
    h = student_headers; policy, body, files = create(client, h); claim, _ = new_claim(client, h, policy)
    base = f"{P}/insurance/claims/{claim['id']}"
    r = client.post(base + "/attachments", headers=h, data={"revision": claim["revision"], "item_code": "INVOICE"}, files={"file": ("invoice.txt", files["claim-invoice.txt"], "text/plain")})
    claim = r.json(); item = claim["attachments"][0]
    assert client.post(base + "/attachments", headers=h, data={"revision": claim["revision"], "item_code": "INVOICE"}, files={"file": ("invoice.txt", files["claim-invoice.txt"], "text/plain")}).json()["revision"] == claim["revision"]
    removed = client.post(base + "/attachments/" + item["id"] + "/remove", headers=h, json={"revision": claim["revision"]})
    assert removed.status_code == 200 and removed.json()["attachments"] == []
    assert client.get(base + "/attachments/" + item["id"], headers=h).status_code == 404
    claim = removed.json()
    edit = {"revision": claim["revision"], "title": "Corrected case", "amount": "600.01", "incident_date": str(today()), "deadline": None, "description": "Self-authored test details only"}
    updated = client.post(base + "/update", headers=h, json=edit)
    assert updated.status_code == 200 and updated.json()["amount"] == "600.01"
    assert client.post(base + "/update", headers=h, json=edit).status_code == 409
    second = client.post(P + "/documents", headers=h, files={"file": ("new-source.txt", b"A replacement source with enough readable text for this test.", "text/plain")}).json()
    body.update(document_id=second["id"], revision=1, benefits=[{"kind": "OUTPATIENT", "status": "UNKNOWN"}])
    assert client.post(f"{P}/insurance/policies/{policy['id']}/update", headers=h, json=body).status_code == 200
    assert client.post(f"{P}/documents/{policy['document_id']}/delete", headers=h).status_code == 409
    assert client.get(base + "/export", headers=h).status_code == 200


def test_invoice_and_policy_plan_paths_share_one_expense(client, student_headers):
    h = student_headers; policy, _, _ = create(client, h)
    w = client.post(P + "/finance/wallets", headers=h, json={"name": "Budget CNY", "currency": "CNY", "opening_balance": "1000", "opening_date": str(today())}).json()
    plan = client.post(f"{P}/insurance/policies/{policy['id']}/plan", headers=h, json={"revision": 1, "reviewed": True, "wallet_id": w["id"]}).json()["plan"]
    estimate = client.post(f"{P}/insurance/policies/{policy['id']}/premium-invoice", headers=h, json={"revision": 1, "reviewed": True}).json()["invoice"]
    existing = client.post(P + "/finance/plans/from-invoice", headers=h, json={"invoice_id": estimate["id"], "wallet_id": w["id"]})
    assert existing.status_code == 200 and existing.json()["id"] == plan["id"]
    assert len(client.get(P + "/finance/plans", headers=h).json()["items"]) == 1
    assert client.post(f"{P}/finance/plans/{plan['id']}/stop", headers=h).status_code == 200
    assert client.get(P + "/insurance/policies", headers=h).json()["items"][0]["plan_needs_review"] is True


def test_vnd_precision_and_cross_currency_plan_guard(client, student_headers):
    h = student_headers; body, _ = data(client, h)
    body.update(currency="VND", premium="100.25", benefits=[{"kind": "OUTPATIENT", "status": "UNKNOWN"}])
    assert client.post(P + "/insurance/policies", headers=h, json=body).status_code == 422
    body["premium"] = "100"
    policy = client.post(P + "/insurance/policies", headers=h, json=body).json()
    assert policy["premium"] == "100"
    assert client.post(f"{P}/insurance/policies/{policy['id']}/premium-invoice", headers=h, json={"revision": 1, "reviewed": True}).status_code == 422
    w = client.post(P + "/finance/wallets", headers=h, json={"name": "Wrong currency", "currency": "CNY", "opening_balance": "1000", "opening_date": str(today())}).json()
    assert client.post(f"{P}/insurance/policies/{policy['id']}/plan", headers=h, json={"revision": 1, "reviewed": True, "wallet_id": w["id"]}).status_code == 422


def test_gemini_evidence_excludes_claim_cases_and_requires_policy_scope(client, student_headers, monkeypatch):
    from app.finance import assistant_evidence
    from app.config import settings
    monkeypatch.setattr(settings, "gemini_data_mode", "PAID_PRIVATE")
    from app.models import User
    h = student_headers; policy, _, _ = create(client, h)
    claim, _ = new_claim(client, h, policy, description="PRIVATE_MEDICAL_DETAIL_MUST_STAY_LOCAL")
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.id == InsurancePolicy.__table__.select().with_only_columns(InsurancePolicy.user_id).scalar_subquery()))
        evidence, citations = assistant_evidence("policy claim", user, db, ["insurance"])
        raw = json.dumps(evidence)
        assert "PRIVATE_MEDICAL_DETAIL_MUST_STAY_LOCAL" not in raw
        assert any(item["kind"] == "USER_REVIEWED_POLICY_SUMMARY" for item in evidence)
        assert not any(item["kind"] == "CLAIM_PREPARATION_STATUS" for item in evidence)
        assert not any(item.get("href") == f"/insurance/claims/{claim['id']}" for item in citations.values())
        assert all(item["kind"] == "APP_GUIDE" for item in assistant_evidence("policy claim", user, db)[0])

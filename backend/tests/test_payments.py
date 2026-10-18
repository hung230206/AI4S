import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta, date
from decimal import Decimal
from uuid import uuid4
import json
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.config import settings, ROOT
from app.db import SessionLocal
from app.main import app
from app.models import User, Invoice, Quote, Order, Transaction, Event, Receipt, Audit, ProviderEvent, now
from app.providers import signed, deliver_pending
from app.security import signer
from app.seed import STUDENT_ID, seed
from app.services import breakdown

P = "/api/v1"
INVOICE = "11111111-1111-4111-8111-111111111111"


def quote(client, headers, invoice=INVOICE):
    result = client.post(P + "/quotes", headers=headers, json={"invoice_id": invoice, "settlement_currency": "VND"})
    assert result.status_code == 200, result.text
    return result.json()


def order(client, headers, q=None, key="create-key-001"):
    q = q or quote(client, headers)
    body = {"invoice_id": q["invoice_id"], "quote_id": q["id"]}
    result = client.post(P + "/orders", headers={**headers, "Idempotency-Key": key}, json=body)
    assert result.status_code == 200, result.text
    return result.json()


def confirm(client, headers, o, key="confirm-key-001", **overrides):
    body = {"quote_id": o["quote_id"], "consent": True, "consent_version": "demo-v1", "expected_total_vnd": o["total_vnd"], **overrides}
    return client.post(f"{P}/orders/{o['id']}/confirm", headers={**headers, "Idempotency-Key": key}, json=body)


def event_for(o, **overrides):
    return {"external_event_id": f"evt_{uuid4()}", "provider_payment_id": f"mock_{o['id']}", "order_id": o["id"], "event_timestamp": now().isoformat(), "status": "SUCCEEDED", "amount_vnd": o["total_vnd"], "currency": "VND", **overrides}


def webhook(client, payload, timestamp=None):
    raw, headers = signed(payload, timestamp)
    return client.post(P + "/webhooks/mock", content=raw, headers=headers)


def processing(client, headers):
    o = order(client, headers)
    result = confirm(client, headers, o)
    assert result.status_code == 200, result.text
    return result.json()


def current(client, headers, o):
    return client.get(f"{P}/orders/{o['id']}", headers=headers).json()


def test_quote_fixture_and_decimal_rounding(client, student_headers):
    q = quote(client, student_headers)
    expected = json.loads((ROOT / "fixtures/expected_demo_quote.json").read_text())
    for key in ("vnd_per_cny", "converted_subtotal_vnd", "variable_fee_rate_percent", "variable_fee_vnd", "fixed_fee_vnd", "total_vnd", "rate_source"):
        assert q[key] == expected[key]
    assert q["source_amount_cny"] == "800.00" and q["expires_at"].endswith("Z")
    assert breakdown(Decimal("0.01"))["converted_subtotal_vnd"] == Decimal("35")
    assert breakdown(Decimal("0.01"))["variable_fee_vnd"] == Decimal("1")


def test_happy_path(client, student_headers):
    o = processing(client, student_headers)
    assert webhook(client, event_for(o)).status_code == 200
    assert current(client, student_headers, o)["status"] == "SUCCEEDED"
    receipt = client.get(f"{P}/orders/{o['id']}/receipt", headers=student_headers).json()
    assert receipt["is_simulated"] is True
    assert receipt["notice"] == "SIMULATED TRANSACTION — NO REAL FUNDS MOVED"
    assert receipt["total_vnd"] == "2847000"


def test_failed_payment_and_fresh_retry(client, student_headers):
    o = processing(client, student_headers)
    assert webhook(client, event_for(o, status="FAILED")).status_code == 200
    assert current(client, student_headers, o)["status"] == "FAILED"
    assert client.get(f"{P}/orders/{o['id']}/receipt", headers=student_headers).status_code == 409
    assert order(client, student_headers, key="retry-create-002")["id"] != o["id"]


def test_cancel_before_confirm(client, student_headers):
    o = order(client, student_headers)
    for _ in range(2):
        result = client.post(f"{P}/orders/{o['id']}/cancel", headers=student_headers)
        assert result.json()["status"] == "CANCELLED"
    assert confirm(client, student_headers, o).status_code == 409
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 0


def make_expired(quote_id):
    with SessionLocal.begin() as db:
        q = db.get(Quote, quote_id)
        q.created_at = now() - timedelta(minutes=20)
        q.expires_at = now() - timedelta(minutes=10)


def test_expired_quote(client, student_headers):
    o = order(client, student_headers)
    make_expired(o["quote_id"])
    result = confirm(client, student_headers, o)
    assert result.status_code == 409 and result.json()["error"]["code"] == "QUOTE_EXPIRED"
    assert current(client, student_headers, o)["status"] == "EXPIRED"
    assert order(client, student_headers, key="new-after-expiry")["id"] != o["id"]


def test_expired_quote_at_create(client, student_headers):
    q = quote(client, student_headers)
    make_expired(q["id"])
    result = client.post(P + "/orders", headers={**student_headers, "Idempotency-Key": "expired-create"}, json={"invoice_id": INVOICE, "quote_id": q["id"]})
    assert result.status_code == 409 and result.json()["error"]["code"] == "QUOTE_EXPIRED"


@pytest.mark.parametrize("overrides", [{"quote_id": str(uuid4())}, {"expected_total_vnd": "1"}])
def test_quote_mismatch(client, student_headers, overrides):
    o = order(client, student_headers)
    assert confirm(client, student_headers, o, **overrides).json()["error"]["code"] == "QUOTE_MISMATCH"


@pytest.mark.parametrize("amount", ["1", "0", "-1", 1.2])
def test_client_tamper_amount(client, student_headers, amount):
    q = quote(client, student_headers)
    result = client.post(P + "/orders", headers={**student_headers, "Idempotency-Key": "tamper-create"}, json={"invoice_id": INVOICE, "quote_id": q["id"], "amount_cny": amount})
    assert result.status_code == 422
    assert order(client, student_headers, q)["amount_cny"] == "800.00"


@pytest.mark.parametrize("consent", [False, "true", 1, None])
def test_no_implicit_consent(client, student_headers, consent):
    o = order(client, student_headers)
    assert confirm(client, student_headers, o, consent=consent).status_code == 422
    assert current(client, student_headers, o)["status"] == "AWAITING_CONFIRMATION"


def test_confirm_twice(client, student_headers):
    q = quote(client, student_headers)
    o = order(client, student_headers, q)
    assert order(client, student_headers, q) == o
    one = confirm(client, student_headers, o)
    two = confirm(client, student_headers, o)
    assert one.json() == two.json()
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 1
        assert db.scalar(select(func.count()).select_from(Order)) == 1


def test_idempotency_conflict(client, student_headers):
    o = order(client, student_headers)
    confirm(client, student_headers, o)
    result = confirm(client, student_headers, o, expected_total_vnd="1")
    assert result.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    q = quote(client, student_headers)
    result = client.post(P + "/orders", headers={**student_headers, "Idempotency-Key": "create-key-001"}, json={"invoice_id": INVOICE, "quote_id": q["id"]})
    assert result.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_duplicate_event(client, student_headers):
    o = processing(client, student_headers)
    payload = event_for(o)
    assert webhook(client, payload).json()["duplicate"] is False
    assert webhook(client, payload).json()["duplicate"] is True
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Event)) == 1
        assert db.scalar(select(func.count()).select_from(Receipt)) == 1
    trace = client.get(f"{P}/orders/{o['id']}/events", headers=student_headers).json()
    assert any(a["action"] == "DUPLICATE_WEBHOOK" for a in trace["audit"])


def test_invalid_hmac(client, student_headers):
    o = processing(client, student_headers)
    raw, headers = signed(event_for(o))
    headers["X-Mock-Signature"] = "0" * 64
    result = client.post(P + "/webhooks/mock", content=raw, headers=headers)
    assert result.status_code == 401 and result.json()["error"]["code"] == "EVENT_BAD_SIGNATURE"
    assert current(client, student_headers, o)["status"] == "PROCESSING"


@pytest.mark.parametrize("offset", [-600, 600])
def test_stale_hmac_timestamp(client, student_headers, offset):
    o = processing(client, student_headers)
    result = webhook(client, event_for(o), int(time.time()) + offset)
    assert result.status_code == 401 and result.json()["error"]["code"] == "EVENT_STALE_TIMESTAMP"


@pytest.mark.parametrize("overrides", [{"amount_vnd": "1"}, {"currency": "CNY"}, {"provider_payment_id": "mock_wrong_id"}])
def test_event_amount_mismatch(client, student_headers, overrides):
    o = processing(client, student_headers)
    assert webhook(client, event_for(o, **overrides)).status_code == 409
    assert current(client, student_headers, o)["status"] == "PROCESSING"
    with SessionLocal() as db:
        assert db.scalar(select(Event)).processing_outcome == "REJECTED"
        assert db.scalar(select(func.count()).select_from(Receipt)) == 0


def test_out_of_order_after_success(client, student_headers):
    o = processing(client, student_headers)
    webhook(client, event_for(o))
    assert webhook(client, event_for(o, status="FAILED")).json()["processing_outcome"] == "IGNORED"
    assert current(client, student_headers, o)["status"] == "SUCCEEDED"
    assert client.post(f"{P}/orders/{o['id']}/cancel", headers=student_headers).status_code == 409


def test_cross_user_access(client, student_headers):
    o = processing(client, student_headers)
    other = uuid4()
    with SessionLocal.begin() as db:
        db.add(User(id=other, display_name="Another synthetic student", role="STUDENT"))
    headers = {"Authorization": "Bearer " + signer.dumps({"sub": str(other), "role": "STUDENT"})}
    for suffix in ("", "/events", "/receipt"):
        assert client.get(f"{P}/orders/{o['id']}{suffix}", headers=headers).status_code == 404
    assert confirm(client, headers, o).status_code == 404
    assert client.post(f"{P}/orders/{o['id']}/cancel", headers=headers).status_code == 404
    assert client.get(f"{P}/invoices/{INVOICE}", headers=headers).status_code == 404
    assert client.get(P + "/orders", headers=headers).json()["items"] == []


def test_simulate_forbidden(client, student_headers):
    o = processing(client, student_headers)
    assert client.post(f"{P}/demo/orders/{o['id']}/simulate", headers=student_headers, json={"outcome": "SUCCEEDED"}).status_code == 403
    for body in ({"role": "OPERATOR"}, {"role": "OPERATOR", "operator_code": "wrong-code"}):
        assert client.post(P + "/demo/session", json=body).status_code == 403


def test_operator_disabled_prod(client, student_headers, operator_headers, monkeypatch):
    o = processing(client, student_headers)
    monkeypatch.setattr(settings, "demo_mode", False)
    assert client.post(P + "/demo/session", json={"role": "STUDENT"}).status_code == 403
    assert client.post(f"{P}/demo/orders/{o['id']}/simulate", headers=operator_headers, json={"outcome": "SUCCEEDED"}).status_code == 403
    raw, headers = signed(event_for(o))
    assert client.post(P + "/webhooks/mock", content=raw, headers=headers).status_code == 403


def test_parallel_confirms(client, student_headers):
    o = order(client, student_headers)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: confirm(client, student_headers, o), range(8)))
    assert all(r.status_code == 200 for r in results)
    assert all(r.json() == results[0].json() for r in results)
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 1


def test_parallel_creates_and_webhooks(client, student_headers):
    q = quote(client, student_headers)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: order(client, student_headers, q), range(6)))
    assert len({r["id"] for r in results}) == 1
    o = results[0]
    confirm(client, student_headers, o)
    payload = event_for(o)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: webhook(client, payload), range(6)))
    assert all(r.status_code == 200 for r in results)
    assert sum(not r.json()["duplicate"] for r in results) == 1


def test_async_provider_outbox_and_replay(client, student_headers, operator_headers):
    o = processing(client, student_headers)
    result = client.post(f"{P}/demo/orders/{o['id']}/simulate", headers=operator_headers, json={"outcome": "SUCCEEDED"})
    assert result.json()["queued"]
    assert current(client, student_headers, o)["status"] == "PROCESSING"
    asyncio.run(deliver_pending(app))
    assert current(client, student_headers, o)["status"] == "SUCCEEDED"
    event_id = result.json()["external_event_id"]
    client.post(f"{P}/demo/events/{event_id}/replay", headers=operator_headers)
    asyncio.run(deliver_pending(app))
    with SessionLocal() as db:
        outbox = db.scalar(select(ProviderEvent))
        assert outbox.delivered and outbox.attempts == 2 and outbox.last_http_status == 200
        assert db.scalar(select(func.count()).select_from(Receipt)) == 1


def test_provider_outage_rolls_back(client, student_headers, monkeypatch):
    from app.main import provider
    def unavailable(**kwargs):
        raise ConnectionError("Synthetic outage")
    monkeypatch.setattr(provider, "create_payment", unavailable)
    o = order(client, student_headers)
    result = confirm(client, student_headers, o)
    assert result.status_code == 503
    assert current(client, student_headers, o)["status"] == "AWAITING_CONFIRMATION"
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 0


def test_invoice_expired_and_changed(client, student_headers):
    o = order(client, student_headers)
    with SessionLocal.begin() as db:
        db.get(Invoice, INVOICE).amount_cny = Decimal("900")
    assert confirm(client, student_headers, o).json()["error"]["code"] == "QUOTE_MISMATCH"
    with SessionLocal.begin() as db:
        db.get(Invoice, INVOICE).due_date = date(2020, 1, 1)
    result = client.post(P + "/quotes", headers=student_headers, json={"invoice_id": INVOICE, "settlement_currency": "VND"})
    assert result.json()["error"]["code"] == "INVOICE_NOT_PAYABLE"


def test_no_auth_and_forged_token(client):
    assert client.get(P + "/invoices").status_code == 401
    assert client.get(P + "/invoices", headers={"Authorization": "Bearer forged"}).status_code == 401


def test_seed_repeatable_and_safe_trace(client, student_headers):
    with SessionLocal.begin() as db:
        seed(db)
        seed(db)
        assert db.scalar(select(func.count()).select_from(Invoice)) == 1
    o = processing(client, student_headers)
    webhook(client, event_for(o))
    trace = client.get(f"{P}/orders/{o['id']}/events", headers=student_headers).text
    for forbidden in (settings.mock_webhook_secret, settings.app_session_secret, settings.demo_operator_code, "payload_sha256", "Authorization", "card_number"):
        assert forbidden not in trace


def test_event_id_collision_rejected(client, student_headers):
    o = processing(client, student_headers)
    payload = event_for(o)
    webhook(client, payload)
    assert webhook(client, {**payload, "status": "FAILED"}).status_code == 409


def test_old_event_before_intent_ignored(client, student_headers):
    o = processing(client, student_headers)
    result = webhook(client, event_for(o, event_timestamp=(now() - timedelta(minutes=10)).isoformat()))
    assert result.json()["processing_outcome"] == "IGNORED"
    assert current(client, student_headers, o)["status"] == "PROCESSING"


def test_contract_routes_and_policy(client, student_headers):
    import yaml
    contract = yaml.safe_load((ROOT / "contracts/openapi.yaml").read_text())
    paths = client.get("/openapi.json").json()["paths"]
    assert set(contract["paths"]) <= set(paths)
    policy = client.get(P + "/policy", headers=student_headers).json()
    assert policy["source_type"] == "SYNTHETIC" and "Insufficient policy information" in policy["notice"]


def test_no_live_money_configuration():
    from app.config import Settings
    from pydantic import ValidationError
    for changes in ({"allow_real_payments": True}, {"payment_provider": "airwallex"}, {"airwallex_enabled": True}):
        with pytest.raises(ValidationError):
            Settings(**changes)


def test_quote_owned_by_another_student(client, student_headers):
    other = uuid4()
    other_invoice = uuid4()
    with SessionLocal.begin() as db:
        db.add(User(id=other, display_name="Fictional Student B", role="STUDENT"))
        db.flush()
        db.add(Invoice(id=other_invoice, student_id=other, invoice_number="OTHER-SYNTHETIC", institution_name="Fictional", beneficiary_name="Fictional", fee_type="DEMO", amount_cny=Decimal("800"), due_date=now().date() + timedelta(days=1)))
    other_headers = {"Authorization": "Bearer " + signer.dumps({"sub": str(other), "role": "STUDENT"})}
    q = quote(client, other_headers, str(other_invoice))
    result = client.post(P + "/orders", headers={**student_headers, "Idempotency-Key": "other-quote-key"}, json={"invoice_id": INVOICE, "quote_id": q["id"]})
    assert result.status_code == 404 and result.json()["error"]["code"] == "QUOTE_NOT_FOUND"


def test_parallel_confirms_different_keys(client, student_headers):
    o = order(client, student_headers)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda i: confirm(client, student_headers, o, key=f"parallel-confirm-{i}"), range(6)))
    assert sum(r.status_code == 200 for r in results) == 1
    assert all(r.status_code in (200, 409) for r in results)
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 1

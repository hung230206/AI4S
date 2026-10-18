import io
import hashlib
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from pypdf import PdfWriter
from pypdf.generic import NameObject, DictionaryObject, DecodedStreamObject
from app.main import app
from app.db import SessionLocal
from app.models import User, AuthSession, FxObservation, Quote, now
from app import fx

P = "/api/v1"
PASSWORD = "mvp-test-password-only-2026"


@pytest.fixture(autouse=True)
def fake_reference(monkeypatch):
    def upstream(path, params=None):
        value = {"date": now().date().isoformat(), "base": "CNY", "quote": "VND", "rate": Decimal("3864.07")}
        if path == "/rates":
            return [{**value, "date": (now().date() - timedelta(days=i)).isoformat()} for i in range(10)]
        return value
    monkeypatch.setattr(fx, "fetch_json", upstream)


def register(client, email=None):
    email = email or f"mvp-{uuid4().hex}@example.com"
    response = client.post(P + "/auth/register", json={"email": email, "password": PASSWORD, "display_name": "MVP Account"})
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}, response.json()


def invoice_payload(**updates):
    return {"invoice_number": "USER-INV-2026-001", "institution_name": "Institution from invoice", "beneficiary_name": "Recipient from invoice", "amount_cny": "800.00", "due_date": (now().date() + timedelta(days=10)).isoformat(), "notes": "Entered from my fee notice", **updates}


def invoice(client, headers, **updates):
    response = client.post(P + "/invoices", headers=headers, json=invoice_payload(**updates))
    assert response.status_code == 200, response.text
    return response.json()


def quote(client, headers, inv):
    response = client.post(P + "/quotes", headers=headers, json={"invoice_id": inv["id"], "settlement_currency": "VND"})
    assert response.status_code == 200, response.text
    return response.json()


def test_account_register_cookie_session_logout(client):
    headers, result = register(client)
    assert result["user"]["is_demo"] is False
    assert result["user"]["email"].endswith("@example.com")
    assert client.get(P + "/invoices").json()["items"] == []
    response = client.get(P + "/auth/session")
    assert response.json()["csrf_token"] == headers["X-CSRF-Token"]
    raw = client.cookies.get("baoan_session")
    with SessionLocal() as db:
        user = db.get(User, result["user"]["id"])
        assert user.password_hash.startswith("$argon2id$") and PASSWORD not in user.password_hash
        session = db.scalar(select(AuthSession))
        assert session.token_hash == hashlib.sha256(raw.encode()).hexdigest()
    assert client.post(P + "/auth/logout", headers=headers).status_code == 200
    assert client.get(P + "/auth/session").status_code == 401


def test_cookie_attributes_and_weak_password(client):
    weak = client.post(P + "/auth/register", json={"email": "user@example.com", "password": "short", "display_name": "User"})
    assert weak.status_code == 422
    response = client.post(P + "/auth/register", json={"email": "user@example.com", "password": PASSWORD, "display_name": "User"})
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/api/v1" in cookie
    assert client.post(P + "/auth/register", json={"email": "USER@example.com", "password": PASSWORD, "display_name": "Other"}).status_code == 409


def test_login_and_expired_session(client):
    _, result = register(client)
    email = result["user"]["email"]
    bad = client.post(P + "/auth/login", json={"email": email, "password": "wrong"})
    assert bad.status_code == 401 and bad.json()["error"]["code"] == "INVALID_CREDENTIALS"
    good = client.post(P + "/auth/login", json={"email": email.upper(), "password": PASSWORD})
    assert good.status_code == 200
    raw = client.cookies.get("baoan_session")
    with SessionLocal.begin() as db:
        session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hashlib.sha256(raw.encode()).hexdigest()))
        session.expires_at = now() - timedelta(seconds=1)
    assert client.get(P + "/invoices").status_code == 401


def test_login_throttle_is_persisted(client):
    for _ in range(10):
        assert client.post(P + "/auth/login", json={"email": "unknown@example.com", "password": "wrong"}).status_code == 401
    assert client.post(P + "/auth/login", json={"email": "unknown@example.com", "password": "wrong"}).status_code == 429


def test_cookie_csrf_and_origin_enforcement(client):
    headers, _ = register(client)
    assert client.post(P + "/invoices", json=invoice_payload()).status_code == 403
    assert client.post(P + "/invoices", headers={"X-CSRF-Token": "wrong"}, json=invoice_payload()).status_code == 403
    assert client.post(P + "/invoices", headers={**headers, "Origin": "https://attacker.example"}, json=invoice_payload()).status_code == 403
    assert client.post(P + "/auth/login", headers={"Origin": "https://attacker.example"}, json={"email": "a@example.com", "password": PASSWORD}).status_code == 403
    assert client.post(P + "/invoices", headers=headers, json=invoice_payload()).status_code == 200


def test_explicit_lan_origin_keeps_csrf_and_other_origin_protection(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "frontend_extra_origins", "http://192.168.1.2:3000")
    headers, _ = register(client)
    lan = {**headers, "Origin": "http://192.168.1.2:3000", "Sec-Fetch-Site": "same-origin"}
    assert client.post(P + "/invoices", headers=lan, json=invoice_payload()).status_code == 200
    assert client.post(P + "/invoices", headers={"Origin": lan["Origin"]}, json=invoice_payload(invoice_number="NO-CSRF")).status_code == 403
    assert client.post(P + "/invoices", headers={**headers, "Origin": "http://192.168.1.99:3000"}, json=invoice_payload(invoice_number="OTHER-HOST")).status_code == 403
    assert client.post(P + "/invoices", headers={**lan, "Sec-Fetch-Site": "cross-site"}, json=invoice_payload(invoice_number="CROSS-SITE")).status_code == 403


def test_profile_and_password_revoke_sessions(client):
    headers, result = register(client)
    response = client.post(P + "/auth/profile", headers=headers, json={"display_name": "Updated Name"})
    assert response.json()["user"]["display_name"] == "Updated Name"
    wrong = client.post(P + "/auth/password", headers=headers, json={"current_password": "wrong", "new_password": "another-password-2026"})
    assert wrong.status_code == 401
    changed = client.post(P + "/auth/password", headers=headers, json={"current_password": PASSWORD, "new_password": "another-password-2026"})
    assert changed.status_code == 200
    assert client.get(P + "/auth/session").status_code == 401
    assert client.post(P + "/auth/login", json={"email": result["user"]["email"], "password": PASSWORD}).status_code == 401
    assert client.post(P + "/auth/login", json={"email": result["user"]["email"], "password": "another-password-2026"}).status_code == 200


def test_invoice_create_edit_filter_void(client):
    headers, _ = register(client)
    inv = invoice(client, headers)
    assert inv["source_type"] == "USER_ENTERED" and inv["is_real_beneficiary"] is False
    assert client.post(P + "/invoices", headers=headers, json=invoice_payload()).status_code == 409
    update = client.post(f"{P}/invoices/{inv['id']}/update", headers=headers, json=invoice_payload(amount_cny="900.50", notes="Updated"))
    assert update.json()["amount_cny"] == "900.50"
    assert len(client.get(P + "/invoices?q=Institution").json()["items"]) == 1
    assert not client.get(P + "/invoices?q=%25").json()["items"]
    assert client.post(f"{P}/invoices/{inv['id']}/void", headers=headers).json()["status"] == "VOID"
    assert len(client.get(P + "/invoices?status=VOID").json()["items"]) == 1
    assert not client.get(P + "/invoices?status=OPEN").json()["items"]
    result = client.post(P + "/quotes", headers=headers, json={"invoice_id": inv["id"], "settlement_currency": "VND"})
    assert result.status_code == 409


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "1.234", 5.2])
def test_invoice_invalid_amounts(client, amount):
    headers, _ = register(client)
    assert client.post(P + "/invoices", headers=headers, json=invoice_payload(amount_cny=amount)).status_code == 422


def test_invoice_ownership_and_per_account_number(client):
    headers, _ = register(client)
    inv = invoice(client, headers)
    with TestClient(app) as other:
        other_headers, _ = register(other)
        assert other.get(f"{P}/invoices/{inv['id']}").status_code == 404
        assert other.post(f"{P}/invoices/{inv['id']}/update", headers=other_headers, json=invoice_payload()).status_code == 404
        assert other.post(f"{P}/invoices/{inv['id']}/void", headers=other_headers).status_code == 404
        assert invoice(other, other_headers)["invoice_number"] == inv["invoice_number"]


def test_reference_quote_snapshot_without_fabricated_fees(client):
    headers, _ = register(client)
    inv = invoice(client, headers)
    q = quote(client, headers, inv)
    assert q["rate_source"] == "FRANKFURTER_REFERENCE" and q["rate_date"] == now().date().isoformat()
    assert q["is_simulated"] is False and q["purpose"] == "REFERENCE_ESTIMATE"
    assert q["vnd_per_cny"] == "3864.070000" and q["total_vnd"] == "3091256"
    assert q["variable_fee_vnd"] == "0" and q["fixed_fee_vnd"] == "0"
    assert client.get(P + "/orders").json()["items"] == []
    with SessionLocal.begin() as db:
        db.scalar(select(FxObservation)).vnd_per_cny = Decimal("4000")
    with SessionLocal() as db:
        assert db.get(Quote, q["id"]).vnd_per_cny == Decimal("3864.070000")


def test_invoice_edit_locked_after_order(client):
    headers, _ = register(client)
    inv = invoice(client, headers)
    q = quote(client, headers, inv)
    response = client.post(P + "/orders", headers={**headers, "Idempotency-Key": "mvp-create-order"}, json={"invoice_id": inv["id"], "quote_id": q["id"]})
    assert response.status_code == 200
    assert client.post(f"{P}/invoices/{inv['id']}/update", headers=headers, json=invoice_payload(amount_cny="900")).json()["error"]["code"] == "INVOICE_LOCKED"
    client.post(f"{P}/orders/{response.json()['id']}/cancel", headers=headers)
    assert client.post(f"{P}/invoices/{inv['id']}/update", headers=headers, json=invoice_payload(amount_cny="900")).status_code == 200


def test_reference_cache_and_history(client, monkeypatch):
    register(client)
    assert client.get(P + "/fx/latest").status_code == 200
    monkeypatch.setattr(fx, "fetch_json", lambda *a, **k: pytest.fail("Fresh cache must not call upstream"))
    assert client.get(P + "/fx/latest").json()["rate"] == "3864.070000"


def test_reference_history_persisted(client):
    register(client)
    response = client.get(P + "/fx/history")
    assert response.status_code == 200 and len(response.json()["items"]) == 10
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(FxObservation)) == 10


def unavailable(*args, **kwargs):
    raise httpx.ReadTimeout("Upstream unavailable")


def test_reference_failure_never_uses_demo_rate(client, monkeypatch):
    headers, _ = register(client)
    inv = invoice(client, headers)
    monkeypatch.setattr(fx, "fetch_json", unavailable)
    result = client.post(P + "/quotes", headers=headers, json={"invoice_id": inv["id"], "settlement_currency": "VND"})
    assert result.status_code == 503 and result.json()["error"]["code"] == "FX_UNAVAILABLE"
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Quote)) == 0


def test_reference_cache_outage_is_explicit(client, monkeypatch):
    register(client)
    with SessionLocal.begin() as db:
        db.add(FxObservation(rate_date=now().date(), vnd_per_cny=Decimal("3800"), fetched_at=now() - timedelta(hours=8)))
    monkeypatch.setattr(fx, "fetch_json", unavailable)
    result = client.get(P + "/fx/latest").json()
    assert result["is_stale"] is True and result["rate"] == "3800.000000"


@pytest.mark.parametrize("row", [
    {"base": "USD", "quote": "VND", "rate": "3800"},
    {"base": "CNY", "quote": "VND", "rate": "NaN"},
    {"base": "CNY", "quote": "VND", "rate": "0"},
])
def test_invalid_reference_data_rejected(client, monkeypatch, row):
    register(client)
    monkeypatch.setattr(fx, "fetch_json", lambda *a, **k: {"date": now().date().isoformat(), **row})
    assert client.get(P + "/fx/latest").status_code == 503


def test_old_cached_reference_refused(client, monkeypatch):
    register(client)
    with SessionLocal.begin() as db:
        db.add(FxObservation(rate_date=now().date() - timedelta(days=8), vnd_per_cny=Decimal("3800"), fetched_at=now() - timedelta(hours=8)))
    monkeypatch.setattr(fx, "fetch_json", unavailable)
    assert client.get(P + "/fx/latest").status_code == 503


def test_upstream_decimal_parse(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(200, text='{"date":"2026-10-16","base":"CNY","quote":"VND","rate":3864.07}', request=httpx.Request("GET", "https://api.frankfurter.dev")))
    assert fx.fetch_json("/rate/CNY/VND")["rate"] == Decimal("3864.07")


POLICY = b"Annual premium: CNY 800. Claims require hospital invoices and a claim form.\n\nExclusions: elective cosmetic treatment is excluded. Coverage period: one academic year."


def upload(client, headers, filename="policy.txt", content=POLICY):
    return client.post(P + "/documents", headers=headers, data={"title": "Uploaded policy", "source_url": "https://example.com/policy"}, files={"file": (filename, content)})


def test_document_upload_search_citation_and_download(client):
    headers, _ = register(client)
    result = upload(client, headers)
    assert result.status_code == 200, result.text
    doc = result.json()
    assert doc["source_type"] == "USER_DOCUMENT" and doc["page_count"] == 1
    assert upload(client, headers).json()["already_uploaded"] is True
    assert len(client.get(P + "/documents").json()["items"]) == 1
    search = client.post(P + "/documents/search", headers=headers, json={"question": "ho so boi thuong", "document_id": doc["id"]}).json()
    assert search["status"] == "MATCHES_FOUND"
    assert search["matches"][0]["page"] == 1
    assert "Claims require" in search["matches"][0]["excerpt"]
    response = client.get(f"{P}/documents/{doc['id']}/download")
    assert response.content == POLICY and "attachment" in response.headers["content-disposition"]
    assert client.get(f"{P}/documents/{doc['id']}").json()["pages"][0]["text"] == POLICY.decode()
    assert client.post(f"{P}/documents/{doc['id']}/delete", headers=headers).json()["deleted"]
    assert client.get(f"{P}/documents/{doc['id']}").status_code == 404


def test_document_no_evidence_is_explicit(client):
    headers, _ = register(client)
    assert client.post(P + "/documents/search", headers=headers, json={"question": "claim"}).json()["status"] == "NO_DOCUMENTS"
    upload(client, headers)
    result = client.post(P + "/documents/search", headers=headers, json={"question": "unrelatedquasarxyz"}).json()
    assert result["status"] == "INSUFFICIENT_INFORMATION" and result["matches"] == []


def test_document_ownership(client):
    headers, _ = register(client)
    doc = upload(client, headers).json()
    with TestClient(app) as other:
        oh, _ = register(other)
        assert other.get(P + "/documents").json()["items"] == []
        assert other.get(f"{P}/documents/{doc['id']}").status_code == 404
        assert other.get(f"{P}/documents/{doc['id']}/download").status_code == 404
        assert other.post(f"{P}/documents/{doc['id']}/delete", headers=oh).status_code == 404
        assert other.post(P + "/documents/search", headers=oh, json={"question": "claim", "document_id": doc["id"]}).status_code == 404


@pytest.mark.parametrize("filename,content,expected", [("script.html", POLICY, 422), ("bad.pdf", b"not a pdf", 422), ("invalid.txt", b"\xff\xfe\x00", 422), ("huge.txt", b"a" * (5 * 1024 * 1024 + 1), 413)], ids=["unsupported-type", "invalid-pdf", "invalid-encoding", "size-limit"])
def test_document_validation(client, filename, content, expected):
    headers, _ = register(client)
    assert upload(client, headers, filename, content).status_code == expected


def pdf_bytes(blank=False, encrypted=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    if not blank:
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
        stream = DecodedStreamObject()
        stream.set_data(b"BT /F1 12 Tf 50 700 Td (Claims require hospital invoices and a claim form.) Tj ET")
        page[NameObject("/Contents")] = writer._add_object(stream)
    if encrypted:
        writer.encrypt("private-password")
    result = io.BytesIO()
    writer.write(result)
    return result.getvalue()


def test_pdf_text_extraction_and_rejections(client):
    headers, _ = register(client)
    response = upload(client, headers, "policy.pdf", pdf_bytes())
    assert response.status_code == 200, response.text
    search = client.post(P + "/documents/search", headers=headers, json={"question": "claims"}).json()
    assert search["matches"][0]["page"] == 1 and "hospital invoices" in search["matches"][0]["excerpt"]
    assert upload(client, headers, "blank.pdf", pdf_bytes(blank=True)).json()["error"]["code"] == "DOCUMENT_NO_TEXT"
    assert upload(client, headers, "locked.pdf", pdf_bytes(encrypted=True)).json()["error"]["code"] == "DOCUMENT_ENCRYPTED"


def test_accounts_work_without_demo_mode(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "demo_mode", False)
    headers, _ = register(client)
    assert client.get(P + "/auth/session").status_code == 200
    assert invoice(client, headers)["source_type"] == "USER_ENTERED"
    assert client.get(P + "/capabilities").json()["live_payments_configured"] is False

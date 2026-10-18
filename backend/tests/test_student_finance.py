import io
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4
import httpx
import pytest
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select, func
from app import fx, finance
from app.db import SessionLocal
from app.models import Invoice, FinanceEntry
from app.ocr import suggestions, extract_file

P = "/api/v1"


@pytest.fixture(autouse=True)
def reference(monkeypatch):
    monkeypatch.setattr(fx, "fetch_json", lambda *a, **k: {"date": finance.today().isoformat(), "base": "CNY", "quote": "VND", "rate": Decimal("3864.07")})


def account(client):
    response = client.post(P + "/auth/register", json={"display_name": "Finance QA", "email": f"finance-{uuid4()}@example.com", "password": "finance-test-password-2026"})
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"]}


def wallet(client, headers, currency="CNY", opening="1000", name=None, opening_date=None):
    response = client.post(P + "/finance/wallets", headers=headers, json={"name": name or f"Wallet {uuid4()}", "currency": currency, "opening_balance": opening, "opening_date": (opening_date or finance.today()).isoformat()})
    assert response.status_code == 200, response.text
    return response.json()


def entry_body(w, **overrides):
    return {"wallet_id": w["id"], "title": "Lunch", "kind": "EXPENSE", "amount": "10.25", "occurred_on": finance.today().isoformat(), "request_key": str(uuid4()), **overrides}


def plan(client, headers, w, **overrides):
    response = client.post(P + "/finance/plans", headers=headers, json={"wallet_id": w["id"], "title": "Rent", "kind": "EXPENSE", "amount": "1200", "due_date": (finance.today() + timedelta(days=5)).isoformat(), "recurrence": "NONE", **overrides})
    assert response.status_code == 200, response.text
    return response.json()


def test_ledger_preserves_native_currencies_and_decimal_precision(client):
    h = account(client)
    cny = wallet(client, h, opening="1000.50")
    vnd = wallet(client, h, currency="VND", opening="4000000")
    assert client.post(P + "/finance/entries", headers=h, json=entry_body(cny)).status_code == 200
    result = client.get(P + "/finance/forecast").json()
    assert result["totals"] == {"CNY": "990.25", "VND": "4000000"}
    assert result["projected_value_vnd"] == "7826395"
    assert client.get(P + "/finance/wallets").json()["items"][0]["holds_real_funds"] is False
    assert client.get(P + "/orders").json()["items"] == []


@pytest.mark.parametrize("currency,amount", [("VND", "1.25"), ("CNY", "1.234"), ("USD", "50"), ("VND", "-1")])
def test_wallet_precision_and_supported_currency(client, currency, amount):
    h = account(client)
    result = client.post(P + "/finance/wallets", headers=h, json={"name": "Invalid wallet", "currency": currency, "opening_balance": amount, "opening_date": finance.today().isoformat()})
    assert result.status_code == 422


def test_entry_retry_conflict_void_and_date_validation(client):
    h = account(client); w = wallet(client, h)
    body = entry_body(w)
    first = client.post(P + "/finance/entries", headers=h, json=body)
    assert first.status_code == 200
    assert client.post(P + "/finance/entries", headers=h, json=body).json()["id"] == first.json()["id"]
    assert client.post(P + "/finance/entries", headers=h, json={**body, "amount": "11"}).status_code == 409
    assert client.post(P + "/finance/entries", headers=h, json=entry_body(w, occurred_on=(finance.today() + timedelta(days=1)).isoformat())).status_code == 422
    for _ in range(2):
        assert client.post(f"{P}/finance/entries/{first.json()['id']}/void", headers=h, json={}).status_code == 200
    assert client.get(P + "/finance/wallets").json()["items"][0]["balance"] == "1000.00"


def test_finance_owner_isolation(client):
    h = account(client); w = wallet(client, h)
    p = plan(client, h, w)
    e = client.post(P + "/finance/entries", headers=h, json=entry_body(w)).json()
    other = account(client)
    assert client.get(P + "/finance/wallets").json()["items"] == []
    assert client.get(P + "/finance/plans").json()["items"] == []
    assert client.post(P + "/finance/entries", headers=other, json=entry_body(w)).status_code == 404
    assert client.post(f"{P}/finance/plans/{p['id']}/stop", headers=other, json={}).status_code == 404
    assert client.post(f"{P}/finance/entries/{e['id']}/void", headers=other, json={}).status_code == 404


def test_forecast_shortfall_then_settle_does_not_double_count(client):
    h = account(client); w = wallet(client, h)
    p = plan(client, h, w)
    forecast = client.get(P + "/finance/forecast").json()
    assert forecast["wallets"][0]["projected_balance"] == "-200.00"
    assert forecast["wallets"][0]["current_balance"] == "1000.00"
    assert forecast["recommendations"][0]["code"] == "CASH_SHORTFALL"
    body = {"occurrence_date": p["due_date"], "request_key": str(uuid4())}
    first = client.post(f"{P}/finance/plans/{p['id']}/settle", headers=h, json=body)
    assert first.status_code == 200, first.text
    assert client.post(f"{P}/finance/plans/{p['id']}/settle", headers=h, json=body).json()["id"] == first.json()["id"]
    assert client.post(f"{P}/finance/plans/{p['id']}/settle", headers=h, json={**body, "request_key": str(uuid4())}).json()["id"] == first.json()["id"]
    after = client.get(P + "/finance/forecast").json()
    assert after["wallets"][0]["projected_balance"] == "-200.00" and after["events"] == []
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(FinanceEntry)) == 1
    assert client.get(P + "/orders").json()["items"] == []


def test_void_settlement_restores_planned_occurrence(client):
    h = account(client); w = wallet(client, h); p = plan(client, h, w)
    body = {"occurrence_date": p["due_date"], "request_key": str(uuid4())}
    first = client.post(f"{P}/finance/plans/{p['id']}/settle", headers=h, json=body).json()
    client.post(f"{P}/finance/entries/{first['id']}/void", headers=h, json={})
    assert len(client.get(P + "/finance/forecast").json()["events"]) == 1
    assert client.post(f"{P}/finance/plans/{p['id']}/settle", headers=h, json={**body, "request_key": str(uuid4())}).status_code == 200


def test_stopped_plan_and_invalid_occurrence(client):
    h = account(client); w = wallet(client, h); p = plan(client, h, w)
    assert client.post(f"{P}/finance/plans/{p['id']}/settle", headers=h, json={"occurrence_date": finance.today().isoformat(), "request_key": str(uuid4())}).status_code == 422
    assert client.post(f"{P}/finance/plans/{p['id']}/stop", headers=h, json={}).json()["active"] is False
    assert client.get(P + "/finance/forecast").json()["events"] == []


def test_month_end_recurring_plan_keeps_original_day():
    p = SimpleNamespace(due_date=date(2026, 1, 31), recurrence="MONTHLY")
    assert list(finance.occurrence_dates(p, date(2026, 4, 30))) == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]


def test_native_forecast_remains_usable_without_fx(client, monkeypatch):
    h = account(client); wallet(client, h)
    def unavailable(*a, **k):
        raise httpx.ReadTimeout("Unavailable")
    monkeypatch.setattr(fx, "fetch_json", unavailable)
    result = client.get(P + "/finance/forecast")
    assert result.status_code == 200 and result.json()["projected_value_vnd"] is None
    assert result.json()["wallets"][0]["projected_balance"] == "1000.00"


def test_invoice_plan_uses_owned_server_amount_and_no_duplicate(client):
    h = account(client); w = wallet(client, h)
    inv = client.post(P + "/invoices", headers=h, json={"invoice_number": "PLAN-INV", "institution_name": "QA issuer", "beneficiary_name": "QA beneficiary", "amount_cny": "800.25", "due_date": (finance.today() + timedelta(days=7)).isoformat()}).json()
    body = {"wallet_id": w["id"], "invoice_id": inv["id"]}
    response = client.post(P + "/finance/plans/from-invoice", headers=h, json=body)
    assert response.status_code == 200 and response.json()["amount"] == "800.25"
    assert client.post(P + "/finance/plans/from-invoice", headers=h, json=body).json()["id"] == response.json()["id"]
    assert client.post(P + "/finance/plans/from-invoice", headers=h, json={**body, "amount": "1"}).status_code == 422


def test_fx_scenarios_are_decimal_budget_sensitivity_not_a_forecast(client):
    h = account(client)
    r = client.post(P + "/finance/fx-analysis", headers=h, json={"amount_cny": "800", "budget_vnd": "3100000"}).json()
    assert r["scenarios"][1]["cost_vnd"] == "3091256"
    assert r["scenarios"][1]["remaining_budget_vnd"] == "8744"
    assert r["scenarios"][2]["cost_vnd"] == "3245819"
    assert r["budget_rate_threshold"] == "3875.000000"
    assert client.post(P + "/finance/fx-analysis", headers=h, json={"amount_cny": "0"}).status_code == 422


TEXT = "Invoice number: REVIEW-2026\nIssuer: QA University\nBeneficiary: QA Insurance\nTotal due: CNY 800.00\nDue date: 2026-12-20\nSelf-authored QA input."


def test_text_import_requires_human_review_and_enforces_ownership(client):
    h = account(client)
    response = client.post(P + "/invoice-imports", headers=h, files={"file": ("invoice.txt", TEXT.encode(), "text/plain")})
    assert response.status_code == 200, response.text
    draft = response.json()
    assert draft["suggestions"]["fields"]["amount_cny"]["value"] == "800.00"
    assert draft["suggestions"]["fields"]["due_date"]["page"] == 1
    assert client.get(P + "/invoices").json()["items"] == []
    fields = {key: value["value"] for key, value in draft["suggestions"]["fields"].items()}
    assert client.post(P + "/invoices", headers=h, json={**fields, "import_id": draft["id"]}).status_code == 422
    saved = client.post(P + "/invoices", headers=h, json={**fields, "import_id": draft["id"], "import_reviewed": True})
    assert saved.status_code == 200, saved.text
    assert client.get(f"{P}/invoice-imports/by-invoice/{saved.json()['id']}").json()["source"]["id"] == draft["id"]
    assert client.get(f"{P}/invoice-imports/{draft['id']}/download").content == TEXT.encode()
    assert client.post(P + "/invoices", headers=h, json={**fields, "invoice_number": "SECOND", "import_id": draft["id"], "import_reviewed": True}).status_code == 409
    other = account(client)
    assert client.get(f"{P}/invoice-imports/{draft['id']}").status_code == 404
    assert client.post(P + "/invoices", headers=other, json={**fields, "import_id": draft["id"], "import_reviewed": True}).status_code == 404


def test_chinese_field_extraction_and_ambiguous_currency():
    fields = suggestions([{"page": 1, "text": "发票号码：CN-2026\n学校：测试大学\n收款单位：测试保险\n应付金额：CNY 1,234.56\n缴费截止日期：2026年12月20日"}])["fields"]
    assert fields["amount_cny"]["value"] == "1234.56" and fields["due_date"]["value"] == "2026-12-20"
    assert "amount_cny" not in suggestions([{"page": 1, "text": "Total: USD 800.00"}])["fields"]


def test_actual_local_neural_ocr_reads_self_authored_image():
    image = Image.new("RGB", (1500, 850), "white")
    draw = ImageDraw.Draw(image)
    draw.multiline_text((70, 50), TEXT, fill="black", font=ImageFont.load_default(size=38), spacing=28)
    buffer = io.BytesIO(); image.save(buffer, format="PNG")
    pages, mime, method = extract_file(buffer.getvalue(), "qa-invoice.png")
    assert method == "LOCAL_TESSERACT" and mime == "image/png"
    fields = suggestions(pages)["fields"]
    assert fields["amount_cny"]["value"] == "800.00", pages
    assert fields["invoice_number"]["value"] == "REVIEW-2026", pages


def test_actual_scanned_pdf_uses_local_ocr():
    image = Image.new("RGB", (1500, 850), "white")
    ImageDraw.Draw(image).multiline_text((70, 50), TEXT, fill="black", font=ImageFont.load_default(size=38), spacing=28)
    buffer = io.BytesIO(); image.save(buffer, format="PDF", resolution=150)
    pages, mime, method = extract_file(buffer.getvalue(), "scanned-qa.pdf")
    assert method == "LOCAL_TESSERACT" and mime == "application/pdf"
    assert suggestions(pages)["fields"]["amount_cny"]["value"] == "800.00"


def test_assistant_payment_request_cannot_execute_actions(client):
    h = account(client)
    response = client.post(P + "/finance/assistant", headers=h, json={"message": "Thanh toán 800 CNY cho tôi ngay"})
    assert response.status_code == 200
    assert response.json()["intent"] == "PAYMENT_REVIEW" and response.json()["executed_actions"] == []
    assert client.get(P + "/orders").json()["items"] == []
    assert client.get(P + "/finance/entries").json()["items"] == []


def test_assistant_grounded_budget_and_account_isolation(client):
    h = account(client); w = wallet(client, h); plan(client, h, w)
    response = client.post(P + "/finance/assistant", headers=h, json={"message": "30 ngay toi toi co du tien khong?"}).json()
    assert response["intent"] == "BUDGET_NEXT_STEP" and "-200.00 CNY" in response["answer"]
    assert response["citations"] and response["executed_actions"] == []
    other = account(client)
    private = client.post(P + "/finance/assistant", headers=other, json={"message": "30 ngay toi toi co du tien khong?"}).json()
    assert private["citations"] == [] and "Chưa có số dư" in private["answer"]


def test_assistant_policy_cites_uploaded_evidence_and_refuses_missing(client):
    h = account(client)
    empty = client.post(P + "/finance/assistant", headers=h, json={"message": "Ho so boi thuong gom gi?"}).json()
    assert empty["citations"] == [] and "Chưa có chứng cứ" in empty["answer"]
    policy = "Claims require hospital invoices and a signed claim form. This is self-authored QA text."
    assert client.post(P + "/documents", headers=h, files={"file": ("policy.txt", policy.encode())}).status_code == 200
    reply = client.post(P + "/finance/assistant", headers=h, json={"message": "Ho so boi thuong gom gi?"}).json()
    assert reply["citations"][0]["page"] == 1 and "hospital invoices" in reply["citations"][0]["excerpt"]


def test_chinese_query_matches_two_character_clause(client):
    h = account(client)
    text = "理赔需要医院发票和申请表。此文本仅用于软件测试，不是真实保险条款。"
    client.post(P + "/documents", headers=h, files={"file": ("chinese-policy.txt", text.encode())})
    reply = client.post(P + "/documents/search", headers=h, json={"question": "理赔"}).json()
    assert reply["status"] == "MATCHES_FOUND" and "医院发票" in reply["matches"][0]["excerpt"]


@pytest.mark.parametrize("filename,data", [("script.svg", b"<svg/>"), ("bad.png", b"not image"), ("bad.pdf", b"not pdf")])
def test_import_rejects_invalid_files(client, filename, data):
    h = account(client)
    assert client.post(P + "/invoice-imports", headers=h, files={"file": (filename, data)}).status_code == 422

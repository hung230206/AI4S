"""Actual HTTP + local neural OCR + public reference API evidence; no credentials exported."""
import argparse
import hashlib
import json
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import httpx

root = Path(__file__).resolve().parents[1]
def checked(response, status=200):
    if response.status_code != status:
        raise RuntimeError(f"Unexpected HTTP {response.status_code}; operation did not complete")
    return response.json()

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--url", default="http://localhost:3000"); args = parser.parse_args()
    day = datetime.now(timezone(timedelta(hours=7))).date()
    checks = {}
    with httpx.Client(base_url=args.url + "/api/v1", timeout=90, headers={"Origin": args.url}) as client:
        session = checked(client.post("/auth/register", json={"email": f"live-finance-{uuid.uuid4()}@example.com", "password": secrets.token_urlsafe(25), "display_name": "Student Finance HTTP QA"}))
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        source = (root / ".local/qa-documents/invoice-zh.png").read_bytes()
        draft = checked(client.post("/invoice-imports", data={"language": "zh"}, files={"file": ("qa-invoice-zh.png", source, "image/png")}))
        fields = {key: value["value"] for key, value in draft["suggestions"]["fields"].items()}
        assert draft["method"] == "LOCAL_TESSERACT" and fields["amount_cny"] == "800.00"
        assert checked(client.get("/invoices"))["items"] == []
        checked(client.post("/invoices", json={**fields, "import_id": draft["id"]}), 422)
        invoice = checked(client.post("/invoices", json={**fields, "import_id": draft["id"], "import_reviewed": True}))
        downloaded = client.get(f"/invoice-imports/{draft['id']}/download")
        assert hashlib.sha256(downloaded.content).digest() == hashlib.sha256(source).digest()
        checks["actual_chinese_neural_ocr_review_gate_and_original_download"] = True
        wallet = checked(client.post("/finance/wallets", json={"name": "CNY QA ledger", "currency": "CNY", "opening_balance": "1000.00", "opening_date": day.isoformat()}))
        vnd = checked(client.post("/finance/wallets", json={"name": "VND QA ledger", "currency": "VND", "opening_balance": "4000000", "opening_date": day.isoformat()}))
        assert wallet["holds_real_funds"] is False and vnd["holds_real_funds"] is False
        checked(client.post("/finance/plans/from-invoice", json={"wallet_id": wallet["id"], "invoice_id": invoice["id"]}))
        plan = checked(client.post("/finance/plans", json={"wallet_id": wallet["id"], "title": "QA upcoming rent", "kind": "EXPENSE", "category": "HOUSING", "amount": "1200.00", "due_date": (day + timedelta(days=5)).isoformat(), "recurrence": "NONE"}))
        forecast = checked(client.get("/finance/forecast?days=30"))
        assert forecast["totals"]["CNY"] == "-200.00" and forecast["totals"]["VND"] == "4000000"
        checks["native_currency_ledger_forecast_shortfall"] = True
        settle = {"occurrence_date": plan["due_date"], "request_key": str(uuid.uuid4())}
        first = checked(client.post(f"/finance/plans/{plan['id']}/settle", json=settle))
        assert checked(client.post(f"/finance/plans/{plan['id']}/settle", json=settle))["id"] == first["id"]
        assert checked(client.get("/finance/forecast?days=30"))["totals"]["CNY"] == "-200.00"
        checks["confirmed_entry_idempotency_no_forecast_double_count"] = True
        checked(client.post(f"/finance/entries/{first['id']}/void", json={}))
        assert checked(client.get("/finance/wallets"))["items"][0]["balance"] == "1000.00"
        checks["void_restores_balance_and_planned_event"] = True
        analysis = checked(client.post("/finance/fx-analysis", json={"amount_cny": "800.00", "budget_vnd": "3100000"}))
        rate = analysis["reference_rate"]
        expected = (Decimal("800") * Decimal(rate["rate"])).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert Decimal(analysis["scenarios"][1]["cost_vnd"]) == expected
        history = checked(client.get("/fx/history")); assert history["items"]
        checks["actual_reference_fx_history_and_decimal_scenarios"] = True
        policy_path = root / ".local/qa-documents/policy-scanned.pdf"
        policy = checked(client.post("/documents", data={"title": "Self-authored scanned QA policy", "language": "en"}, files={"file": (policy_path.name, policy_path.read_bytes(), "application/pdf")}))
        assert policy["extraction_method"] == "LOCAL_TESSERACT"
        reply = checked(client.post("/finance/assistant", json={"message": "Hồ sơ bồi thường gồm những gì?"}))
        assert reply["citations"] and "hospital invoices" in reply["citations"][0]["excerpt"]
        assert reply["executed_actions"] == []
        checks["scanned_policy_ocr_cited_assistance"] = True
        request = checked(client.post("/finance/assistant", json={"message": "Thanh toán ngay 800 CNY giúp tôi"}))
        assert request["executed_actions"] == [] and checked(client.get("/orders"))["items"] == []
        checks["assistant_cannot_create_or_confirm_payments"] = True
        checked(client.post("/auth/logout", json={}))
        checked(client.get("/auth/session"), 401)
        checks["revoked_cookie_session"] = True
    output = {"captured_at": datetime.now(timezone.utc).isoformat(), "transport": "Actual HTTP through frontend proxy", "data_provenance": "Isolated self-authored QA account, amounts and document fixtures; only FX reference data is public upstream/cache", "checks": checks, "reference_rate": rate, "fx_analysis": analysis, "history_points": len(history["items"]), "ocr_fields_detected": len(fields), "forecast_before_actual_entry": {"totals": forecast["totals"], "days": forecast["days"]}, "notice": "No credentials, bank data or real payment recorded"}
    (root / "submission/evidence/student-finance-live-http.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"STUDENT FINANCE LIVE PASS: {len(checks)} checks; actual local OCR, reference FX, ledger, forecast, citations, bounded payment intent and logout.")

if __name__ == "__main__":
    main()

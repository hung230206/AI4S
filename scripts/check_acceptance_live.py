"""Actual owner A-Z workflow; no operator credential or live payment required."""
import argparse
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import secrets
import time
from uuid import uuid4
from zipfile import ZipFile
import httpx

ROOT = Path(__file__).resolve().parents[1]


def checked(response, expected=200):
    if response.status_code != expected:
        try:
            code = response.json().get("error", {}).get("code", "UNKNOWN")
        except ValueError:
            code = "NON_JSON_PROXY_RESPONSE"
        raise AssertionError(f"Expected HTTP {expected}, got {response.status_code} ({code})")
    return response.json()


def wait_for(client, order_id, status):
    for _ in range(25):
        result = checked(client.get(f"/orders/{order_id}"))
        if result["status"] == status:
            return result
        if result["status"] in ("FAILED", "SUCCEEDED"):
            raise AssertionError("Unexpected terminal provider outcome")
        time.sleep(.5)
    raise AssertionError("Provider outcome did not arrive; check PROVIDER_WORKER_ENABLED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3000")
    parser.add_argument("--public-reference", type=Path, help="Optional original BFSU PDF downloaded using team.py fetch-reference")
    parser.add_argument("--output", type=Path, help="Separate evidence destination for a deployed environment")
    args = parser.parse_args()
    checks = {}
    source_path = ROOT / "fixtures/uploads/01_Hoa_don/01_en_800.png"
    raw = source_path.read_bytes()
    with httpx.Client(base_url=args.url.rstrip("/") + "/api/v1", headers={"Origin": args.url.rstrip("/")}, timeout=100) as client:
        session = checked(client.post("/auth/register", json={"email": f"acceptance-http-{uuid4()}@example.com", "password": secrets.token_urlsafe(25), "display_name": "Acceptance HTTP QA"}))
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        catalog = checked(client.get("/test-lab/catalog"))
        bundle = client.get("/test-lab/download")
        with ZipFile(io.BytesIO(bundle.content)) as archive:
            assert archive.testzip() is None
            assert archive.read("Demo_Upload_Test/01_Hoa_don/01_en_800.png") == raw
        checks["downloadable_inputs"] = True
        draft = checked(client.post("/invoice-imports", data={"language": "en"}, files={"file": (source_path.name, raw, "image/png")}))
        fields = {k: v["value"] for k, v in draft["suggestions"]["fields"].items()}
        assert fields["amount_cny"] == "800.00" and draft["method"] == "LOCAL_TESSERACT"
        checked(client.post("/invoices", json={**fields, "import_id": draft["id"]}), 422)
        invoice = checked(client.post("/invoices", json={**fields, "import_id": draft["id"], "import_reviewed": True, "fee_type": "TUITION"}))
        checks["ocr_human_review_and_saved_source"] = True
        wallet = checked(client.post("/finance/wallets", json={"name": "Acceptance CNY", "currency": "CNY", "opening_balance": "1000.00", "opening_date": date.today().isoformat()}))
        plan = checked(client.post("/finance/plans/from-invoice", json={"wallet_id": wallet["id"], "invoice_id": invoice["id"]}))
        forecast = checked(client.get("/finance/forecast?days=30"))
        assert forecast["totals"]["CNY"] == "200.00"
        checks["invoice_plan_native_forecast"] = True
        policy_path = ROOT / "fixtures/uploads/02_Bao_hiem/01_policy_vi_text.pdf"
        policy = checked(client.post("/documents", data={"title": "Self-authored acceptance policy", "language": "vi", "document_kind": "TEST_FIXTURE"}, files={"file": (policy_path.name, policy_path.read_bytes(), "application/pdf")}))
        assert policy["document_kind"] == "TEST_FIXTURE"
        excerpts = checked(client.post("/documents/search", json={"question": "hồ sơ bồi thường", "document_id": policy["id"]}))
        assert any(m["page"] == 2 and "hóa đơn viện phí" in m["excerpt"] for m in excerpts["matches"])
        checks["declared_test_policy_page_citation"] = True
        quote = checked(client.post("/quotes", json={"invoice_id": invoice["id"], "settlement_currency": "VND"}))
        assert quote["rate_source"] == "FRANKFURTER_REFERENCE"
        order = checked(client.post("/orders", headers={"Idempotency-Key": str(uuid4())}, json={"invoice_id": invoice["id"], "quote_id": quote["id"]}))
        body = {"quote_id": quote["id"], "consent": True, "consent_version": "demo-v1", "expected_total_vnd": quote["total_vnd"], "sandbox_scenario": "SUCCESS"}
        confirm_key = str(uuid4())
        confirmed = checked(client.post(f"/orders/{order['id']}/confirm", headers={"Idempotency-Key": confirm_key}, json=body))
        assert confirmed["status"] == "PROCESSING"
        assert checked(client.post(f"/orders/{order['id']}/confirm", headers={"Idempotency-Key": confirm_key}, json=body))["id"] == order["id"]
        wait_for(client, order["id"], "SUCCEEDED")
        trace = checked(client.get(f"/orders/{order['id']}/events"))
        assert len(trace["items"]) == 1 and trace["items"][0]["signature_verified"]
        receipt = checked(client.get(f"/orders/{order['id']}/receipt"))
        assert "NO REAL FUNDS MOVED" in receipt["notice"]
        checks["consented_automatic_signed_outcome_no_operator"] = True
        settle_body = {"occurrence_date": plan["due_date"], "request_key": str(uuid4())}
        entry = checked(client.post(f"/finance/plans/{plan['id']}/settle", json=settle_body))
        assert checked(client.post(f"/finance/plans/{plan['id']}/settle", json=settle_body))["id"] == entry["id"]
        assert checked(client.get("/finance/wallets"))["items"][0]["balance"] == "200.00"
        assert checked(client.get("/finance/forecast?days=30"))["totals"]["CNY"] == "200.00"
        checks["separate_ledger_confirmation_no_double_count"] = True
        exported = client.get(f"/orders/{order['id']}/evidence")
        with ZipFile(io.BytesIO(exported.content)) as archive:
            case = json.loads(archive.read("case.json"))
            assert archive.read("source/" + source_path.name) == raw
            assert case["wallet_snapshot"]["balance"] == "200.00"
            assert case["receipt"] and len(case["ledger_entries"]) == 1
        checks["owner_case_zip_original_quote_receipt_events_ledger"] = True
        progress = checked(client.get("/test-lab/status", params={"invoice_id": invoice["id"]}))
        assert all(progress["steps"].values())
        checks["journey_progress_from_database"] = True
        # Retry from a failed order uses a fresh quote/order and fresh consent.
        raw_text = (ROOT / "fixtures/uploads/01_Hoa_don/06_en_675.txt").read_bytes()
        d = checked(client.post("/invoice-imports", files={"file": ("retry.txt", raw_text, "text/plain")}))
        f = {k: v["value"] for k, v in d["suggestions"]["fields"].items()}
        inv = checked(client.post("/invoices", json={**f, "import_id": d["id"], "import_reviewed": True}))
        for scenario, outcome in (("DECLINED", "FAILED"), ("SUCCESS", "SUCCEEDED")):
            q = checked(client.post("/quotes", json={"invoice_id": inv["id"], "settlement_currency": "VND"}))
            o = checked(client.post("/orders", headers={"Idempotency-Key": str(uuid4())}, json={"invoice_id": inv["id"], "quote_id": q["id"]}))
            checked(client.post(f"/orders/{o['id']}/confirm", headers={"Idempotency-Key": str(uuid4())}, json={"quote_id": q["id"], "consent": True, "consent_version": "demo-v1", "expected_total_vnd": q["total_vnd"], "sandbox_scenario": scenario}))
            wait_for(client, o["id"], outcome)
            if outcome == "FAILED":
                checked(client.get(f"/orders/{o['id']}/receipt"), 409)
        checks["decline_no_receipt_fresh_consent_retry"] = True
        public = None
        if args.public_reference:
            raw_public = args.public_reference.read_bytes()
            url = next(s["url"] for s in catalog["public_sources"] if s["id"] == "bfsu-2025")
            doc = checked(client.post("/documents", data={"title": "BFSU 2025 public reference, not personal policy", "language": "zh", "source_url": url, "document_kind": "PUBLIC_REFERENCE"}, files={"file": ("bfsu-2025-original.pdf", raw_public, "application/pdf")}))
            result = checked(client.post("/documents/search", json={"question": "hospital", "document_id": doc["id"]}))
            assert result["matches"] and all(m["source_url"] == url and m["page"] == 1 for m in result["matches"])
            original = client.get(f"/documents/{doc['id']}/download")
            assert original.content == raw_public
            public = {"url": url, "sha256": hashlib.sha256(raw_public).hexdigest(), "bytes": len(raw_public), "pages": doc["page_count"], "method": doc["extraction_method"], "query": "hospital", "matches": len(result["matches"])}
            checks["original_public_pdf_ocr_citation_and_exact_download"] = True
        checked(client.post("/auth/logout", json={}))
        checked(client.get("/auth/session"), 401)
        checks["logout_revokes_session"] = True
    output = {"captured_at": datetime.now(timezone.utc).isoformat(), "transport": "Actual HTTP through frontend proxy", "synthetic_account_and_invoice_data": True, "checks": checks, "public_reference": public, "payment_provider": "MOCK", "real_funds_moved": False, "reference_rate": {"source": quote["rate_source"], "date": quote["rate_date"], "rate": quote["vnd_per_cny"]}}
    output["base_url"] = args.url.rstrip("/")
    target = args.output or ROOT / "submission/evidence/acceptance-live.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ACCEPTANCE PASS: {len(checks)} checks; actual OCR, reference FX, consent, provider callbacks, separate ledger and case ZIP.")


if __name__ == "__main__":
    main()

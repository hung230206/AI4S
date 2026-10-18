"""Real HTTP smoke against the running app and its Frankfurter integration.

Creates an isolated QA account and self-authored QA data. No credentials are printed/exported.
The endpoint fetches public reference rates; no identity or documents go to Frankfurter.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import secrets
import uuid
import httpx

root = Path(__file__).resolve().parents[1]


def checked(response, code=200):
    if response.status_code != code:
        # Error envelopes omit credentials and submitted input.
        raise RuntimeError(f"Unexpected HTTP {response.status_code}: {response.text[:300]}")
    return response.json()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    email = f"qa-{uuid.uuid4().hex}@example.com"
    password = secrets.token_urlsafe(24)
    with httpx.Client(base_url=args.url + "/api/v1", timeout=20) as client:
        capabilities = checked(client.get("/capabilities"))
        registered = checked(client.post("/auth/register", json={"email": email, "password": password, "display_name": "Automated MVP QA"}))
        csrf = {"X-CSRF-Token": registered["csrf_token"]}
        session = checked(client.get("/auth/session"))
        assert session["user"]["is_demo"] is False
        rate = checked(client.get("/fx/latest"))
        assert rate["source"] == "FRANKFURTER_REFERENCE"
        invoice = checked(client.post("/invoices", headers=csrf, json={"invoice_number": f"QA-{uuid.uuid4().hex[:10]}", "institution_name": "QA institution input", "beneficiary_name": "QA recipient input", "amount_cny": "800.00", "due_date": (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat(), "notes": "Automated QA input, not an actual invoice"}))
        quote = checked(client.post("/quotes", headers=csrf, json={"invoice_id": invoice["id"], "settlement_currency": "VND"}))
        expected = (Decimal("800.00") * Decimal(quote["vnd_per_cny"])).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        assert Decimal(quote["converted_subtotal_vnd"]) == expected
        assert quote["rate_source"] == "FRANKFURTER_REFERENCE"
        assert checked(client.get("/orders"))["items"] == []
        policy = b"Self-authored QA policy text. Claims require hospital invoices and the completed claim form. This file tests extraction only."
        doc = checked(client.post("/documents", headers=csrf, data={"title": "Self-authored QA document"}, files={"file": ("qa-policy.txt", policy, "text/plain")}))
        matches = checked(client.post("/documents/search", headers=csrf, json={"question": "ho so boi thuong", "document_id": doc["id"]}))
        assert matches["status"] == "MATCHES_FOUND" and matches["matches"][0]["page"] == 1
        downloaded = client.get(f"/documents/{doc['id']}/download")
        assert downloaded.status_code == 200 and hashlib.sha256(downloaded.content).digest() == hashlib.sha256(policy).digest()
        checked(client.post(f"/documents/{doc['id']}/delete", headers=csrf))
        assert client.get(f"/documents/{doc['id']}").status_code == 404
        assert checked(client.post(f"/invoices/{invoice['id']}/void", headers=csrf))["status"] == "VOID"
        checked(client.post("/auth/logout", headers=csrf))
        assert client.get("/auth/session").status_code == 401
    output = {"captured_at": datetime.now(timezone.utc).isoformat(), "transport": "Actual HTTP against running FastAPI", "data_provenance": "QA account and self-authored invoice/document; FX is actual upstream/cache reference data", "capabilities": capabilities, "reference_rate": rate, "quote": quote, "checks": {"registration_cookie_session": True, "user_invoice": True, "actual_reference_fx": True, "decimal_conversion": True, "no_order_on_quote": True, "document_upload_and_citation": True, "download_byte_integrity": True, "document_deleted": True, "invoice_archived": True, "logout_revoked": True}}
    target = root / "submission/evidence/mvp-live-http.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"MVP LIVE HTTP PASS: Frankfurter CNY/VND={rate['rate']}, observation={rate['rate_date']}; account/invoice/quote/document/download/delete/logout verified.")


if __name__ == "__main__":
    main()

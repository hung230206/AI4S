"""Authenticated C+D acceptance through actual HTTP endpoints; self-authored data only."""
import argparse
from datetime import datetime, timezone
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


def checked(response, status=200):
    if response.status_code != status:
        code = "NON_JSON_RESPONSE"
        try: code = response.json().get("error", {}).get("code", "UNKNOWN")
        except ValueError: pass
        raise AssertionError(f"HTTP {response.status_code}; expected {status}: {code}")
    return response.json()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3000")
    parser.add_argument("--expected-release", default="")
    parser.add_argument("--with-gemini", action="store_true", help="Explicitly consume one Gemini request using synthetic data")
    parser.add_argument("--evidence", type=Path, default=ROOT / "submission/evidence/insurance-live.json")
    args = parser.parse_args()
    evidence = {"at": datetime.now(timezone.utc).isoformat(), "origin": args.url.rstrip("/"), "checks": [], "real_funds_moved": False}
    started = time.monotonic()
    try:
        with httpx.Client(base_url=args.url.rstrip("/") + "/api/v1", timeout=90, follow_redirects=False) as client:
            health = checked(client.get("/health")); assert health["allow_real_payments"] is False
            assert health["insurance_workflow"] == "portfolio-claims-v1"
            evidence["release"] = health.get("release")
            if args.expected_release: assert health.get("release") == args.expected_release, "Live release does not match pushed commit"
            account = checked(client.post("/auth/register", json={"display_name": "C+D synthetic acceptance", "email": f"cd-{uuid4()}@example.com", "password": secrets.token_urlsafe(28)}))
            client.headers["X-CSRF-Token"] = account["csrf_token"]
            evidence["checks"].append("private_account_and_sandbox_health")
            pack = client.get("/insurance/sample-pack"); assert pack.status_code == 200
            with ZipFile(io.BytesIO(pack.content)) as archive: files = {name: archive.read(name) for name in archive.namelist()}
            source = checked(client.post("/documents", data={"title": "C+D self-authored policy", "document_kind": "TEST_FIXTURE"}, files={"file": ("demo-policy.txt", files["demo-policy.txt"], "text/plain")}))
            fields = json.loads(files["review-fields.json"])
            body = {**fields, "document_id": source["id"], "reviewed": True, "request_key": str(uuid4())}
            invalid = {**body, "reviewed": False}
            checked(client.post("/insurance/policies", json=invalid), 422)
            policy = checked(client.post("/insurance/policies", json=body))
            replay = checked(client.post("/insurance/policies", json=body)); assert replay["id"] == policy["id"]
            assert policy["document_sha256"] == hashlib.sha256(files["demo-policy.txt"]).hexdigest()
            evidence["checks"].append("source_review_citation_hash_and_idempotency")
            date = checked(client.get("/insurance/overview"))["as_of"]
            comparison = checked(client.post("/insurance/analysis", json={"starts_on": date, "ends_on": date, "country": "CN", "currency": "CNY", "needs": [{"kind": "OUTPATIENT", "minimum_limit": "2000"}, {"kind": "EVACUATION", "minimum_limit": "50000"}]}))
            assert [r["status"] for r in comparison["results"]] == ["MEETS_ENTERED_REQUIREMENT", "GAP_IN_ENTERED_PORTFOLIO"]
            evidence["checks"].append("explainable_coverage_match_and_evacuation_gap")
            wallet = checked(client.post("/finance/wallets", json={"name": "C+D CNY budget", "currency": "CNY", "opening_balance": "1000", "opening_date": date}))
            plan_body = {"wallet_id": wallet["id"], "revision": policy["revision"], "reviewed": True}
            planned = checked(client.post(f"/insurance/policies/{policy['id']}/plan", json=plan_body))
            assert planned["wallet"]["balance"] == "1000.00"
            estimate = checked(client.post(f"/insurance/policies/{policy['id']}/premium-invoice", json={"revision": policy["revision"], "reviewed": True}))["invoice"]
            duplicate_plan = checked(client.post("/finance/plans/from-invoice", json={"wallet_id": wallet["id"], "invoice_id": estimate["id"]}))
            assert duplicate_plan["id"] == planned["plan"]["id"]
            forecast = checked(client.get("/finance/forecast")); assert forecast["wallets"][0]["projected_balance"] == "200.00"
            assert len(checked(client.get("/finance/plans"))["items"]) == 1
            evidence["checks"].append("one_premium_plan_1000_current_200_projected")
            quote = checked(client.post("/quotes", json={"invoice_id": estimate["id"], "settlement_currency": "VND"}))
            assert quote["rate_source"] == "FRANKFURTER_REFERENCE"
            assert Decimal(quote["source_amount_cny"]) == Decimal("800")
            order = checked(client.post("/orders", headers={"Idempotency-Key": str(uuid4())}, json={"invoice_id": estimate["id"], "quote_id": quote["id"]}))
            checked(client.post(f"/orders/{order['id']}/confirm", headers={"Idempotency-Key": str(uuid4())}, json={"quote_id": quote["id"], "consent": True, "consent_version": "demo-v1", "expected_total_vnd": quote["total_vnd"], "sandbox_scenario": "SUCCESS"}))
            for _ in range(60):
                outcome = checked(client.get(f"/orders/{order['id']}"))
                if outcome["status"] in ("SUCCEEDED", "FAILED"): break
                time.sleep(.5)
            assert outcome["status"] == "SUCCEEDED"
            trace = checked(client.get(f"/orders/{order['id']}/events"))
            assert any(event["signature_verified"] and event["processing_outcome"] == "APPLIED" for event in trace["items"])
            receipt = checked(client.get(f"/orders/{order['id']}/receipt"))
            assert "NO REAL FUNDS MOVED" in receipt["notice"]
            assert checked(client.get("/finance/wallets"))["items"][0]["balance"] == "1000.00"
            evidence["checks"].append("explicit_consent_signed_sandbox_receipt_no_ledger_debit")
            case = checked(client.post("/insurance/claims", json={"policy_id": policy["id"], "title": "C+D self-authored outpatient case", "benefit_kind": "OUTPATIENT", "incident_date": date, "amount": "500", "description": "Synthetic test only; no actual health data.", "request_key": str(uuid4())}))
            base = f"/insurance/claims/{case['id']}"
            checked(client.post(base + "/transition", json={"revision": case["revision"], "status": "READY", "confirmed": True}), 422)
            for code, filename in [("INVOICE", "claim-invoice.txt"), ("MEDICAL_RECORD", "claim-medical-record.txt"), ("CLAIM_FORM", "claim-claim-form.txt")]:
                case = checked(client.post(base + "/attachments", data={"revision": case["revision"], "item_code": code}, files={"file": (filename, files[filename], "text/plain")}))
            for item in case["checklist"]:
                if item["offline_only"]:
                    case = checked(client.post(base + "/checklist", json={"revision": case["revision"], "code": item["code"], "prepared_externally": True}))
            case = checked(client.post(base + "/transition", json={"revision": case["revision"], "status": "READY", "confirmed": True}))
            export = client.get(base + "/export"); assert export.status_code == 200
            with ZipFile(io.BytesIO(export.content)) as archive:
                report = json.loads(archive.read("claim-preparation.json")); assert report["status"] == "READY"
                for item in report["attachments"]:
                    assert hashlib.sha256(archive.read("attachments/" + item["id"] + "-" + item["filename"])).hexdigest() == item["sha256"]
                assert hashlib.sha256(archive.read("policy-original/demo-policy.txt")).hexdigest() == report["source_document"]["sha256"]
            evidence["checks"].append("claim_checklist_original_attachments_snapshot_and_export_hashes")
            status = checked(client.get("/finance/assistant/status")); evidence["gemini_configured"] = status["gemini_configured"]
            direct = checked(client.post("/finance/assistant", json={"message": "Hồ sơ bồi thường gồm những gì?", "use_gemini": False}))
            assert direct["executed_actions"] == [] and any(a["href"] == "/insurance" for a in direct["actions"])
            if args.with_gemini:
                reply = checked(client.post("/finance/assistant", json={"message": "Tóm tắt phí và thời hạn trong bản tóm tắt bảo hiểm của tôi. Hồ sơ của tôi đang ở trạng thái nào?", "use_gemini": True}))
                assert reply.get("provider") == "GEMINI", "Gemini did not return a real provider response"
                assert reply["executed_actions"] == [] and reply["citations"]
                evidence["gemini_model"] = reply.get("model")
            evidence["checks"].append("grounded_read_only_insurance_handoff")
        evidence["status"] = "PASS"
    except Exception as exc:
        evidence["status"] = "FAIL"; evidence["error_type"] = type(exc).__name__
        # No headers, cookies, generated credentials, provider prompts or raw responses are logged.
        print("C+D acceptance failed: " + type(exc).__name__)
    evidence["elapsed_seconds"] = round(time.monotonic() - started, 3)
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

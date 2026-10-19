"""Validate generated fictional samples against the running LOCAL app only.

Uses one isolated QA account; logs no credentials, cookies or private account IDs.
Does not grant AI permissions, publish RAG or initiate a payment.
"""
import hashlib
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile
import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.documents import extract
from app.ocr import extract_file, suggestions

OUT = ROOT / "output/pdf/Demo_Upload_China_2026_10_20"
mapping = json.loads((OUT / "UPLOAD_MAP.json").read_text(encoding="utf-8"))
fields = json.loads((OUT / "REVIEW_FIELDS.json").read_text(encoding="utf-8"))
result = {"validated_at": datetime.now(timezone.utc).isoformat(), "scope": "Local API on 127.0.0.1:8000; isolated fictional QA account", "pdf": [], "ocr": [], "claims": []}
demo = "--demo" in sys.argv
if demo:
    result["scope"] = "Local API on 127.0.0.1:8000; shared STUDENT sandbox, fictional files only"

for file in sorted(OUT.glob("*.pdf")):
    pages, mime = extract(file.read_bytes(), file.name, "zh")
    assert len(pages) == (2 if file.name.startswith("04_") else 1)
    assert all("测试样本" in page["text"] and "SAMPLE - NOT VALID" in page["text"] for page in pages)
    result["pdf"].append({"file": file.name, "pages": len(pages), "text_characters": sum(len(p["text"]) for p in pages), "app_text_extraction": "PASS"})
    if file.name.startswith("07_"):
        extracted, _, _ = extract_file(file.read_bytes(), file.name)
        assert suggestions(extracted)["document_type"] == "CLAIM_FORM"
result["claim_form_classification"] = "PASS"


def checked(response):
    if response.is_error:
        try:
            code = response.json().get("error", {}).get("code", "UNKNOWN")
        except ValueError:
            code = "NON_JSON_ERROR"
        raise RuntimeError(f"Local validation request failed: HTTP {response.status_code}, {code}")
    return response.json()


with httpx.Client(base_url="http://127.0.0.1:8000/api/v1", headers={"Origin": "http://localhost:3000"}, timeout=20) as client:
    cache = ROOT / ".local/research-sample-qa-session.json"
    if demo:
        session = checked(client.post("/demo/session", json={"role": "STUDENT"}))
        client.headers["Authorization"] = f"Bearer {session['access_token']}"
        account = checked(client.get("/auth/session"))
    elif cache.exists():
        saved = json.loads(cache.read_text(encoding="utf-8"))
        client.cookies.set("baoan_session", saved["cookie"], domain="127.0.0.1", path="/api/v1")
        account = checked(client.get("/auth/session"))
    else:
        account = checked(client.post("/auth/register", json={"email": f"sample-pack-{uuid4()}@example.com", "password": f"Sample-validation-{uuid4()}", "display_name": "Fictional Sample QA"}))
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(json.dumps({"cookie": client.cookies.get("baoan_session")}), encoding="utf-8")
    if account.get("csrf_token"):
        client.headers["X-CSRF-Token"] = account["csrf_token"]
    for expected in mapping["invoices"]:
        file = OUT / expected["file"]
        started = time.monotonic()
        job = checked(client.post("/invoice-imports/jobs", files={"file": (file.name, file.read_bytes(), "image/png")}, data={"language": "zh"}, headers={"X-Processing-Consent": "invoice-ocr:files-2026-10-19-v1"}))
        deadline = time.monotonic() + 180
        while job["status"] in ("QUEUED", "RUNNING"):
            assert time.monotonic() < deadline, "Local OCR exceeded validation wait"
            time.sleep(1)
            job = checked(client.get(f"/invoice-imports/{job['id']}"))
        assert job["status"] == "COMPLETED", (file.name, job["status"], job.get("error_code"))
        extracted = job["suggestions"]["fields"]
        critical = {key: {"expected": expected[key], "actual": extracted.get(key, {}).get("value")} for key in ("invoice_number", "amount_cny", "due_date")}
        assert all(value["expected"] == value["actual"] for value in critical.values()), (file.name, critical)
        assert all(extracted.get(key, {}).get("value") for key in ("institution_name", "beneficiary_name"))
        result["ocr"].append({"file": file.name, "status": "PASS", "seconds": round(time.monotonic() - started, 2), "fields": {key: value["value"] for key, value in extracted.items()}})
        print(f"OCR PASS: {file.name}", flush=True)

    policy_file = OUT / "04_Hop_dong_bao_hiem.pdf"
    doc = checked(client.post("/documents", files={"file": (policy_file.name, policy_file.read_bytes(), "application/pdf")}, data={"title": "Research-shaped fictional policy QA", "document_kind": "TEST_FIXTURE", "language": "zh"}, headers={"X-Processing-Consent": "documents:files-2026-10-19-v1"}))
    policy = checked(client.post("/insurance/policies", json={**fields, "document_id": doc["id"], "reviewed": True, "request_key": str(uuid4())}))
    result["policy_review"] = {"status": "PASS", "benefits_with_verified_citations": len(policy["benefits"]), "document_kind": doc["document_kind"]}
    for kind, codes in [("INPATIENT", ["INVOICE", "MEDICAL_RECORD", "CLAIM_FORM", "DISCHARGE", "COST_BREAKDOWN"]), ("ACCIDENT", ["INVOICE", "MEDICAL_RECORD", "CLAIM_FORM", "ACCIDENT_REPORT"])]:
        claim = checked(client.post("/insurance/claims", json={"policy_id": policy["id"], "title": f"Fictional sample validation {kind}", "benefit_kind": kind, "incident_date": "2026-10-11", "amount": "980.00", "request_key": str(uuid4())}))
        for code in codes:
            file = OUT / next(item["file"] for item in mapping["uploads"] if item.get("item_code") == code)
            claim = checked(client.post(f"/insurance/claims/{claim['id']}/attachments", files={"file": (file.name, file.read_bytes(), "application/pdf")}, data={"item_code": code, "revision": str(claim["revision"])}, headers={"X-Processing-Consent": "claim-attachments:files-2026-10-19-v1"}))
        assert len(claim["attachments"]) == len(codes)
        response = client.get(f"/insurance/claims/{claim['id']}/export")
        response.raise_for_status()
        with ZipFile(io.BytesIO(response.content)) as archive:
            for code in codes:
                file = OUT / next(item["file"] for item in mapping["uploads"] if item.get("item_code") == code)
                match = next(name for name in archive.namelist() if name.endswith("-" + file.name))
                assert archive.read(match) == file.read_bytes()
        assert claim["ready"] is False, "Offline identity/bank preparation was not falsely confirmed"
        result["claims"].append({"kind": kind, "attachment_codes": codes, "uploaded_and_exported_original_bytes": "PASS", "offline_checks_left_unconfirmed": True})
        print(f"Claim upload/export PASS: {kind}", flush=True)
    if not demo:
        checked(client.post("/auth/logout", json={}))
        cache.unlink()

result["files"] = [{"file": item.name, "bytes": item.stat().st_size, "sha256": hashlib.sha256(item.read_bytes()).hexdigest()} for item in sorted(OUT.iterdir()) if item.suffix in (".pdf", ".png")]
result["status"] = "PASS"
(OUT / "VALIDATION.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("All 10 sample files validated; no payment or external AI request made.")

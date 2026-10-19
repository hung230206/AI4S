"""Real HTTP admin CRUD -> publication -> student RAG acceptance. Fictional data only."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import time
from uuid import uuid4
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3104")
    parser.add_argument("--admin-credentials", type=Path, default=ROOT / ".local/rag-admin-test.json")
    parser.add_argument("--with-gemini", action="store_true")
    parser.add_argument("--expected-release", default="")
    parser.add_argument("--evidence", type=Path, default=ROOT / "submission/evidence/rag-live-http.json")
    args = parser.parse_args(); base = args.url.rstrip("/"); start = time.monotonic()
    result = {"at": datetime.now(timezone.utc).isoformat(), "origin": base, "checks": [], "actual_model_calls": 0, "real_funds_moved": False}
    credentials = json.loads(args.admin_credentials.read_text(encoding="utf-8"))
    document_id = None
    def checked(response, status=200):
        if response.status_code != status: raise AssertionError(f"HTTP {response.status_code}, expected {status}")
        return response.json()
    try:
        with ExitStack() as stack:
            admin = stack.enter_context(httpx.Client(base_url=base+"/api/v1", headers={"Origin": base}, timeout=60))
            user = stack.enter_context(httpx.Client(base_url=base+"/api/v1", headers={"Origin": base}, timeout=60))
            health = checked(user.get("/health")); result["release"] = health["release"]
            if args.expected_release: assert health["release"] == args.expected_release
            assert not health["allow_real_payments"]
            auth = checked(admin.post("/auth/login", json={"email": credentials["email"], "password": credentials["password"]}))
            assert auth["user"]["is_rag_admin"] and not auth["user"]["is_demo"]
            admin.headers["X-CSRF-Token"] = auth["csrf_token"]
            def cleanup():
                try:
                    if document_id:
                        doc = checked(admin.get(f"/admin/rag/documents/{document_id}"))
                        if not doc["deleted"]: checked(admin.post(f"/admin/rag/documents/{document_id}/delete", json={"revision": doc["revision"]}))
                    state = user.get("/privacy/ai-permission")
                    if state.status_code == 200 and state.json()["enabled"]:
                        s = state.json(); checked(user.post("/privacy/ai-permission", json={"revision": s["revision"], "notice_version": s["notice_version"], "enabled": False}))
                    admin.post("/auth/logout", json={}); user.post("/auth/logout", json={})
                except (httpx.HTTPError, AssertionError, KeyError): result["cleanup"] = "unconfirmed"
            stack.callback(cleanup)
            account = checked(user.post("/auth/register", json={"email": f"rag-qa-{uuid4()}@example.com", "password": secrets.token_urlsafe(24), "display_name": "Fictional RAG QA"}))
            user.headers["X-CSRF-Token"] = account["csrf_token"]
            checked(user.get("/admin/rag/documents"), 403)
            result["checks"].append("real_admin_login_and_regular_account_denied")
            listing = checked(admin.get("/admin/rag/documents")); notice = listing["publication_notice"]
            content = "SELF-AUTHORED FICTIONAL QA POLICY. Outpatient rehabilitation has an annual sample limit of CNY 6,789. Claims require a hospital invoice and signed claim form. No actual cover or payment is created."
            meta = {"title": "QA fictional RAG source " + str(uuid4())[:8], "publisher": "Demo QA self-authored", "license_note": "CC0 team-authored fictional software acceptance material", "source_kind": "TEST_FIXTURE", "category": "POLICY", "language": "en", "jurisdiction": "CN"}
            upload_headers = {"X-Processing-Consent": "rag-corpus:files-2026-10-19-v1"}
            checked(admin.post("/admin/rag/documents/upload", data={"metadata": json.dumps(meta)}, files={"file": ("qa-source.txt", content.encode(), "text/plain")}), 403)
            doc = checked(admin.post("/admin/rag/documents/upload", headers=upload_headers, data={"metadata": json.dumps(meta)}, files={"file": ("qa-source.txt", content.encode(), "text/plain")})); document_id = doc["id"]; path = f"/admin/rag/documents/{document_id}"
            assert not doc["published"]
            checked(user.get(f"/rag/documents/{document_id}"), 404)
            question = {"document_id": document_id, "question": "According to this fictional source, what is the outpatient annual limit?", "language": "en"}
            preview = checked(admin.post("/admin/rag/preview", json=question)); assert preview["matches"] and preview["provider"] == "LOCAL"
            result["checks"].append("per_file_acknowledgement_draft_isolation_and_local_admin_preview")
            checked(admin.post(path+"/publish", json={"revision": doc["revision"], "notice_version": notice, "publication_confirmed": False}), 403)
            doc = checked(admin.post(path+"/publish", json={"revision": doc["revision"], "notice_version": notice, "publication_confirmed": True}))
            answer = checked(user.post("/rag/ask", json=question)); assert answer["provider"] == "EXTRACTIVE" and "6,789" in answer["answer"]
            match = answer["citations"][0]; source = checked(user.get(f"/rag/documents/{document_id}?revision={doc['revision']}"))
            assert match["excerpt"] == source["pages"][match["page"]-1]["text"][match["start"]:match["end"]]
            original = user.get(f"/rag/documents/{document_id}/download?revision={doc['revision']}")
            assert original.status_code == 200 and hashlib.sha256(original.content).hexdigest() == doc["sha256"]
            result["checks"].append("publication_student_answer_exact_page_offsets_and_original_hash")
            no_evidence = checked(user.post("/rag/ask", json={**question, "question": "What is the maternity benefit limit?"}))
            assert no_evidence["status"] == "INSUFFICIENT_INFORMATION" and no_evidence["citations"] == []
            result["checks"].append("unsupported_insurance_question_abstains")
            state = checked(user.get("/privacy/ai-permission"))
            checked(user.post("/rag/ask", json={**question, "use_gemini": True, "privacy_revision": 1}), 403)
            state = checked(user.post("/privacy/ai-permission", json={"revision": state["revision"], "notice_version": state["notice_version"], "enabled": True, "preset": "SAMPLE_ASSISTANT"}))
            cloud = {**question, "use_gemini": True, "privacy_revision": state["revision"]}
            pending = checked(user.post("/rag/preview", json=cloud)); assert not pending["sent"] and len(pending["excerpts"]) <= 3
            if args.with_gemini:
                result["actual_model_calls"] = 1
                generation_started = time.monotonic()
                generated = checked(user.post("/rag/ask", json=cloud))
                result["generation_elapsed_seconds"] = round(time.monotonic()-generation_started, 3)
                result["generated_model"] = generated.get("model")
                result["model_fallback_from"] = generated.get("model_fallback_from")
                result["provider"] = generated["provider"]; result["fallback_reason"] = generated.get("fallback_reason")
                result["provider_status"] = "PASS" if generated["provider"] == "GEMINI" else "FALLBACK"
                if generated["provider"] == "GEMINI":
                    assert generated["citations"] and generated["executed_actions"] == []
                    assert generated["method"] == "BM25_RAG_GEMINI"
                    assert "6789" in "".join(c for c in generated["answer"] if c.isdigit())
                    result["generated_sample_answer"] = generated["answer"]
            result["checks"].append("session_consent_gate_and_no_dispatch_preview")
            old_revision = doc["revision"]
            updated = {**meta, "title": meta["title"] + " revised", "revision": doc["revision"]}
            doc = checked(admin.post(path+"/update", json=updated)); assert not doc["published"]
            checked(admin.post(path+"/update", json=updated), 409); checked(user.post("/rag/ask", json=question), 404)
            replacement = content.replace("6,789", "7,890")
            doc = checked(admin.post(path+"/file", headers=upload_headers, data={"revision": str(doc["revision"])}, files={"file": ("qa-replacement.txt", replacement.encode(), "text/plain")}))
            doc = checked(admin.post(path+"/publish", json={"revision": doc["revision"], "notice_version": notice, "publication_confirmed": True}))
            checked(user.get(f"/rag/documents/{document_id}?revision={old_revision}"), 409)
            answer = checked(user.post("/rag/ask", json=question)); assert "7,890" in answer["answer"] and "6,789" not in answer["answer"]
            result["checks"].append("edit_and_replace_reindex_unpublish_old_revision_rejected")
            doc = checked(admin.post(path+"/delete", json={"revision": doc["revision"]})); assert doc["deleted"]
            checked(user.get(f"/rag/documents/{document_id}"), 404)
            doc = checked(admin.post(path+"/restore", json={"revision": doc["revision"]})); assert not doc["deleted"] and not doc["published"]
            history = checked(admin.get(path)); assert len(history["history"]) >= 6
            result["checks"].append("trash_restore_draft_and_revision_history")
        result["core_status"] = "PASS"
        result["status"] = "PROVIDER_FALLBACK" if result.get("provider_status") == "FALLBACK" else "PASS"
    except Exception as exc:
        result["status"] = "FAIL"; result["failure"] = type(exc).__name__ + ": " + str(exc)[:160]
        raise
    finally:
        result["elapsed_seconds"] = round(time.monotonic()-start,3)
        args.evidence.parent.mkdir(parents=True, exist_ok=True); args.evidence.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"{result['status']}: {len(result['checks'])} RAG/admin groups; provider: {result.get('provider', 'not called')}")
    if result["status"] == "PROVIDER_FALLBACK": raise SystemExit(2)


if __name__ == "__main__": main()

"""Actual HTTP privacy acceptance; fictional data, at most one opt-in Gemini call."""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import time
from uuid import uuid4
import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3103")
    parser.add_argument("--with-gemini", action="store_true")
    parser.add_argument("--expected-release", default="")
    parser.add_argument("--evidence", type=Path, default=Path("submission/evidence/privacy-live-http.json"))
    args = parser.parse_args(); start = time.monotonic()
    evidence = {"at": datetime.now(timezone.utc).isoformat(), "origin": args.url.rstrip("/"), "checks": [], "real_funds_moved": False, "real_model_calls": 0}
    def checked(response, status=200):
        if response.status_code != status:
            raise AssertionError(f"HTTP {response.status_code}; expected {status}")
        return response.json()
    base = args.url.rstrip("/")
    try:
        with ExitStack() as stack:
            client = stack.enter_context(httpx.Client(base_url=base + "/api/v1", headers={"Origin": base}, timeout=60))
            def revoke_remaining_permission():
                try:
                    response = client.get("/privacy/ai-permission")
                    if response.status_code == 200 and response.json()["enabled"]:
                        state = response.json()
                        checked(client.post("/privacy/ai-permission", json={"enabled": False, "revision": state["revision"], "notice_version": state["notice_version"]}))
                except (httpx.HTTPError, AssertionError, KeyError, ValueError):
                    evidence["permission_cleanup"] = "unconfirmed"
            stack.callback(revoke_remaining_permission)
            health = checked(client.get("/health")); evidence["release"] = health["release"]
            assert not health["allow_real_payments"] and health["payment_provider"] == "MOCK"
            if args.expected_release: assert health["release"] == args.expected_release
            email = f"privacy-qa-{uuid4()}@example.com"; password = secrets.token_urlsafe(28)
            session_response = client.post("/auth/register", json={"email": email, "password": password, "display_name": "Fictional privacy QA"})
            session = checked(session_response)
            cookie = session_response.headers.get("set-cookie", "").lower()
            assert "httponly" in cookie and "samesite=lax" in cookie
            if base.startswith("https://"): assert "; secure" in cookie
            assert session_response.headers.get("cache-control") == "no-store"
            client.headers["X-CSRF-Token"] = session["csrf_token"]
            permission = checked(client.get("/privacy/ai-permission")); assert not permission["enabled"] and permission["scopes"] == []
            status = checked(client.get("/finance/assistant/status")); assert status["gemini_configured"]
            checked(client.post("/finance/assistant", json={"message": "Explain sample policy", "use_gemini": True, "privacy_revision": 1}), 403)
            evidence["checks"].append("default_off_server_gate_and_no_financial_actions")
            grant = {"enabled": True, "revision": permission["revision"], "notice_version": permission["notice_version"], "scopes": ["documents"], "acknowledged": True, "adult_confirmed": True, "non_sensitive_confirmed": True}
            csrf = checked(client.post("/privacy/ai-permission", headers={"X-CSRF-Token": ""}, json=grant), 403)
            assert csrf["error"]["code"] == "CSRF_INVALID"
            checked(client.post("/privacy/ai-permission", json={**grant, "acknowledged": False}), 403)
            if permission["data_mode"] == "DEMO_ONLY":
                checked(client.post("/privacy/ai-permission", json={**grant, "scopes": ["finance"]}), 403)
            permission = checked(client.post("/privacy/ai-permission", json=grant))
            evidence["checks"].append("explicit_versioned_grant_and_unpaid_scope_restriction")
            for name, content, kind in [
                ("private-qa.txt", b"Insurance claim requires PRIVATE_LOCAL_SENTINEL. claim claim claim.", "USER_PROVIDED"),
                ("sample-qa.txt", b"Self-authored fictional insurance policy for software QA. Claims require a hospital invoice and signed claim form. No insurer submission or actual payment occurs.", "TEST_FIXTURE")]:
                checked(client.post("/documents", files={"file": (name, content, "text/plain")}, data={"document_kind": kind}))
            body = {"message": "According to the sample policy, what documents are needed for a claim?", "use_gemini": True, "privacy_revision": permission["revision"], "history": [{"role": "user", "content": "LOCAL_HISTORY_SENTINEL"}]}
            preview = checked(client.post("/finance/assistant/preview", json=body))
            assert preview["conversation"] == [] and "LOCAL_HISTORY_SENTINEL" not in json.dumps(preview)
            if permission["data_mode"] == "DEMO_ONLY": assert "PRIVATE_LOCAL_SENTINEL" not in json.dumps(preview)
            assert "hospital invoice" in json.dumps(preview)
            assert all(e["kind"] not in ["BUDGET", "USER_REVIEWED_POLICY_SUMMARY", "CLAIM_PREPARATION_STATUS"] for e in preview["server_evidence"])
            evidence["checks"].append("preview_is_local_and_filters_ungranted_history_and_private_sources")
            blocked = checked(client.post("/finance/assistant", json={**body, "message": "Email: fake-student@example.com"}), 422)
            assert blocked["error"]["code"] == "AI_SENSITIVE_DATA"
            evidence["checks"].append("sensitive_data_tripwire_before_provider")
            if args.with_gemini:
                evidence["real_model_calls"] = 1
                reply = checked(client.post("/finance/assistant", json=body))
                evidence["provider_result"] = reply.get("provider")
                evidence["fallback_reason"] = reply.get("fallback_reason")
                assert reply.get("provider") == "GEMINI" and reply["executed_actions"] == [], "Gemini fallback: " + str(reply.get("fallback_reason"))
                assert any(c.get("source_id", "").startswith("D") for c in reply["citations"])
                evidence["gemini_model"] = reply["model"]
                evidence["checks"].append("one_real_gemini_answer_from_permitted_fictional_excerpt")
            permission = checked(client.post("/privacy/ai-permission", json={"revision": permission["revision"], "notice_version": permission["notice_version"], "enabled": False}))
            assert not permission["enabled"] and permission["scopes"] == []
            checked(client.post("/finance/assistant", json=body), 403)
            checked(client.post("/finance/assistant/preview", json=body), 403)
            local = checked(client.post("/finance/assistant", json={"message": "Hồ sơ bồi thường gồm gì?", "use_gemini": False}))
            assert local["method"] == "GROUNDED_WORKFLOW" and local["executed_actions"] == []
            evidence["checks"].append("revoke_stops_future_dispatch_and_direct_lookup_remains")
            with httpx.Client(base_url=base + "/api/v1", headers={"Origin": base}, timeout=30) as second:
                checked(second.post("/auth/login", json={"email": email, "password": password}))
                assert checked(second.get("/privacy/ai-permission"))["enabled"] is False
                checked(client.post("/auth/logout-all", json={}))
                checked(second.get("/auth/session"), 401)
                checked(client.get("/auth/session"), 401)
            evidence["checks"].append("session_permission_isolation_and_all_device_logout")
            page = client.get(base + "/privacy"); assert page.status_code == 200
            assert "camera=()" in page.headers.get("permissions-policy", "")
            assert "geolocation=()" in page.headers.get("permissions-policy", "")
            assert page.headers.get("x-frame-options") == "DENY" and page.headers.get("x-content-type-options") == "nosniff"
            evidence["checks"].append("public_privacy_notice_and_unused_device_permissions_disabled")
        evidence["status"] = "PASS"
    except Exception as exc:
        evidence["status"] = "FAIL"; evidence["failure"] = type(exc).__name__ + ": " + str(exc)[:180]
        raise
    finally:
        evidence["elapsed_seconds"] = round(time.monotonic() - start, 3)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {len(evidence['checks'])} privacy groups, {evidence['real_model_calls']} actual model call; evidence: {args.evidence}")


if __name__ == "__main__": main()

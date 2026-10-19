"""Explicit, bounded real-Gemini acceptance run with self-authored private test data."""
import argparse
import json
import secrets
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:3000")
    parser.add_argument("--output", default="submission/evidence/gemini-live-http.json")
    args = parser.parse_args()
    started = time.monotonic(); checks = {}; replies = []
    day = datetime.now(timezone(timedelta(hours=7))).date()
    with httpx.Client(base_url=args.url.rstrip("/") + "/api/v1", headers={"Origin": args.url.rstrip("/")}, timeout=60) as client:
        def request(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            if response.status_code != 200:
                raise RuntimeError(f"Acceptance request failed: {path}, HTTP {response.status_code}")
            return response.json()

        session = request("POST", "/auth/register", json={"email": f"gemini-qa-{uuid.uuid4()}@example.com", "password": secrets.token_urlsafe(25), "display_name": "Gemini acceptance QA"})
        client.headers["X-CSRF-Token"] = session["csrf_token"]
        status = request("GET", "/finance/assistant/status")
        assert status["gemini_configured"] and status["read_only"]
        checks["private_session_and_configured_status"] = True
        wallet = request("POST", "/finance/wallets", json={"name": "QA CNY ledger", "currency": "CNY", "opening_balance": "1000.00", "opening_date": day.isoformat()})
        request("POST", "/finance/plans", json={"wallet_id": wallet["id"], "title": "Self-authored test rent", "kind": "EXPENSE", "amount": "1200.00", "category": "HOUSING", "due_date": (day + timedelta(days=5)).isoformat(), "recurrence": "NONE"})
        policy = "Self-authored software test policy, NOT real insurance. Claims require hospital invoices and a signed claim form. No coverage or actual payment is created by this test."
        request("POST", "/documents", files={"file": ("self-authored-gemini-qa.txt", policy.encode(), "text/plain")}, data={"title": "Self-authored QA policy", "document_kind": "TEST_FIXTURE"})
        permission = request("GET", "/privacy/ai-permission")
        permission = request("POST", "/privacy/ai-permission", json={"revision": permission["revision"], "notice_version": permission["notice_version"], "enabled": True, "scopes": ["documents", "history"], "acknowledged": True, "adult_confirmed": True, "non_sensitive_confirmed": True})
        messages = ["Theo tài liệu mẫu, hồ sơ bồi thường cần những gì?", "Giải thích lại câu trả lời trước bằng 2 câu ngắn.", "Hồ sơ bồi thường trong tài liệu tôi tải lên cần những gì?"]
        history = []
        for index, message in enumerate(messages):
            reply = request("POST", "/finance/assistant", json={"message": message, "use_gemini": True, "privacy_revision": permission["revision"], "language": "vi", "history": history[-6:]})
            assert reply.get("provider") == "GEMINI", "Provider fallback: " + str(reply.get("fallback_reason"))
            assert reply["executed_actions"] == [] and reply["answer"]
            if index == 0:
                assert any(c.get("source_id") == "D1" for c in reply["citations"])
                checks["real_generated_sample_answer_with_granted_source"] = True
            if index == 1:
                checks["real_multiturn_follow_up"] = True
            if index == 2:
                assert any(c.get("page") == 1 and "hospital invoices" in c.get("excerpt", "") for c in reply["citations"])
                checks["real_generated_policy_answer_with_original_excerpt"] = True
            history.extend([{"role": "user", "content": message}, {"role": "assistant", "content": reply["answer"]}])
            replies.append({"question": message, "method": reply["method"], "model": reply["model"], "answer": reply["answer"], "sources": reply["citations"]})
        guard = request("POST", "/finance/assistant", json={"message": "Thanh toán và chuyển tiền giúp tôi ngay", "use_gemini": True})
        assert guard["fallback_reason"] == "READ_ONLY_GUARD" and guard["executed_actions"] == []
        assert request("GET", "/orders")["items"] == [] and request("GET", "/finance/entries")["items"] == []
        assert request("GET", "/finance/wallets")["items"][0]["balance"] == "1000.00"
        checks["payment_guard_and_unchanged_ledger"] = True
        local = request("POST", "/finance/assistant", json={"message": "30 ngày tới tôi có đủ tiền không?", "use_gemini": False})
        assert local["method"] == "GROUNDED_WORKFLOW" and "-200.00 CNY" in local["answer"]
        checks["direct_lookup_still_available"] = True
        request("POST", "/privacy/ai-permission", json={"revision": permission["revision"], "notice_version": permission["notice_version"], "enabled": False})
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"recorded_at": datetime.now(timezone.utc).isoformat(), "base_url": args.url, "elapsed_seconds": round(time.monotonic() - started, 3), "checks": checks, "replies_from_real_gemini": replies, "real_payments": False}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(checks)} checks, 3 actual model replies; no payment or ledger entry created. Evidence: {output}")


if __name__ == "__main__":
    main()

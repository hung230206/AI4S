"""Explicit real-provider acceptance on China public references; no private records."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import httpx

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://ai4s-demo.onrender.com")
    parser.add_argument("--credentials", type=Path, default=ROOT / ".local/rag-admin-test.json")
    parser.add_argument("--import-receipt", type=Path, default=ROOT / "submission/evidence/china-rag-render-import.json")
    parser.add_argument("--evidence", type=Path, default=ROOT / "submission/evidence/china-rag-render-answers.json")
    args = parser.parse_args(); creds = json.loads(args.credentials.read_text(encoding="utf-8"))
    ids = {item["slug"]: item["document_id"] for item in json.loads(args.import_receipt.read_text(encoding="utf-8"))["items"]}
    result = {"at": datetime.now(timezone.utc).isoformat(), "origin": args.url, "public_official_content_only": True, "actual_generation_requests": 0, "answers": []}
    def checked(response):
        if response.status_code != 200: raise RuntimeError("Acceptance HTTP status " + str(response.status_code))
        return response.json()
    with httpx.Client(base_url=args.url.rstrip("/") + "/api/v1", headers={"Origin": args.url.rstrip("/")}, timeout=60) as client:
        auth = checked(client.post("/auth/login", json={"email": creds["email"], "password": creds["password"]}))
        client.headers["X-CSRF-Token"] = auth["csrf_token"]
        try:
            listing = checked(client.get("/rag/documents"))["items"]
            assert len(listing) == 8 and all(d["source_kind"] == "PUBLIC_REFERENCE" and d["jurisdiction"] == "CN" for d in listing)
            result["published_china_reference_count"] = len(listing)
            negative = checked(client.post("/rag/ask", json={"question": "Bitcoin price tomorrow?", "language": "en"}))
            assert negative["status"] == "INSUFFICIENT_INFORMATION" and not negative["citations"]
            result["unrelated_question_abstains"] = True
            unscoped = checked(client.post("/rag/ask", json={"question": "Bảo hiểm sức khỏe ngắn hạn có bảo đảm tái tục không?", "language": "vi"}))
            assert any(c["document_id"] == ids["nfra-shortterm-notice-2021"] for c in unscoped["citations"])
            result["all_sources_retrieval_finds_shortterm_regulation"] = True
            permission = checked(client.get("/privacy/ai-permission"))
            permission = checked(client.post("/privacy/ai-permission", json={"revision": permission["revision"], "notice_version": permission["notice_version"], "enabled": True, "preset": "SAMPLE_ASSISTANT"}))
            cases = [
                ("shortterm-renewal", "nfra-shortterm-notice-2021", "Bảo hiểm sức khỏe ngắn hạn có bảo đảm tái tục không?"),
                ("social-versus-commercial", "nhsa-student-insurance-2025", "Bảo hiểm thương mại 学生平安险 có thay thế bảo hiểm y tế cơ bản không? Tài liệu này có tự động chứng minh du học sinh Việt Nam đủ điều kiện tham gia医保 không?"),
                ("metadata-is-not-coverage", "iac-picc-product-info", "Chỉ dựa vào thông tin sản phẩm 健康金福 này, có thể khẳng định tôi được bồi thường 3 triệu VND không?")
            ]
            for name, slug, question in cases:
                started = time.monotonic(); result["actual_generation_requests"] += 1
                answer = checked(client.post("/rag/ask", json={"question": question, "document_id": ids[slug], "language": "vi", "use_gemini": True, "privacy_revision": permission["revision"]}))
                result["last_response"] = {key: answer.get(key) for key in ("provider", "model", "fallback_reason", "status", "answer")}
                assert answer["executed_actions"] == [] and answer["provider"] == "GEMINI" and answer["citations"]
                assert all(c["document_id"] == ids[slug] and c["document_kind"] == "PUBLIC_REFERENCE" for c in answer["citations"])
                result["answers"].append({"case": name, "question": question, "provider": answer["provider"], "model": answer["model"], "model_fallback_from": answer.get("model_fallback_from"),
                    "answer": answer["answer"], "elapsed_seconds": round(time.monotonic()-started, 3), "sources": [{"href": c["href"], "original_url": c["source_url"], "page": c["page"]} for c in answer["citations"]]})
            result["status"] = "PASS"
        except Exception as error:
            result.update(status="FAIL", error=type(error).__name__); raise
        finally:
            state = client.get("/privacy/ai-permission")
            if state.status_code == 200 and state.json()["enabled"]:
                state = state.json(); checked(client.post("/privacy/ai-permission", json={"enabled": False, "revision": state["revision"], "notice_version": state["notice_version"]}))
            client.post("/auth/logout", json={})
            args.evidence.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: China-only corpus, global retrieval, abstention and three actual grounded Gemini answers")


if __name__ == "__main__": main()

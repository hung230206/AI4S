import json
from datetime import timedelta
from uuid import uuid4
import pytest
from pydantic import SecretStr
from sqlalchemy import select
from app import gemini
from app.config import settings
from app.db import SessionLocal
from app.models import AiPermission, Audit, now

P = "/api/v1"


def account(client):
    r = client.post(P + "/auth/register", json={"email": f"privacy-{uuid4()}@example.com", "display_name": "Privacy QA", "password": "private-qa-password-2026"})
    assert r.status_code == 200
    return {"X-CSRF-Token": r.json()["csrf_token"]}


def grant(client, headers, scopes=None, **extra):
    state = client.get(P + "/privacy/ai-permission", headers=headers).json()
    return client.post(P + "/privacy/ai-permission", headers=headers, json={"revision": state["revision"], "notice_version": state["notice_version"], "enabled": True, "preset": ("ACCOUNT_ASSISTANT" if set(scopes or []) & {"finance", "insurance"} else "SAMPLE_ASSISTANT" if scopes else "QUESTION_ONLY"), **extra})


def ask(client, headers, revision=None, **extra):
    return client.post(P + "/finance/assistant", headers=headers, json={"message": "Explain the insurance claim checklist", "use_gemini": True, "privacy_revision": revision, **extra})


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(settings, "gemini_enabled", True)
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("fake_privacy_key"))
    monkeypatch.setattr(settings, "gemini_data_mode", "DEMO_ONLY")
    captured = []
    def fake(question, history, language, evidence):
        captured.append({"question": question, "history": history, "evidence": evidence})
        return gemini.GeneratedAnswer(answer="Read the cited original and confirm manually.", source_ids=["G1"])
    monkeypatch.setattr(gemini, "generate", fake)
    return captured


def test_default_no_consent_is_fail_closed_and_direct_still_works(client, provider):
    h = account(client)
    state = client.get(P + "/privacy/ai-permission").json()
    assert state["enabled"] is False and state["scopes"] == [] and state["revision"] == 0
    assert ask(client, h).status_code == 403
    assert ask(client, h, 1).status_code == 403
    assert client.post(P + "/finance/assistant", headers=h, json={"message": "policy claim", "use_gemini": False}).status_code == 200
    assert provider == []


@pytest.mark.parametrize("change", [{"preset": None}, {"notice_version": "old"}])
def test_no_preticked_or_old_notice_consent(client, provider, change):
    h = account(client)
    assert grant(client, h, **change).status_code == 403
    assert ask(client, h, 1).status_code == 403 and not provider


def test_question_only_ignores_ungranted_history_and_private_context(client, provider):
    h = account(client)
    assert grant(client, h).status_code == 200
    r = ask(client, h, 1, history=[{"role": "user", "content": "PRIVATE_LOCAL_HISTORY"}])
    assert r.status_code == 200 and r.json()["provider"] == "GEMINI"
    assert provider[0]["history"] == []
    assert [e["kind"] for e in provider[0]["evidence"]] == ["APP_GUIDE"]
    with SessionLocal() as db:
        audit = list(db.scalars(select(Audit).where(Audit.action.like("AI_%"))))
        assert {a.action for a in audit} == {"AI_PERMISSION_GRANTED", "AI_REQUEST_DISPATCHED"}
        assert "PRIVATE_LOCAL_HISTORY" not in json.dumps([a.safe_metadata for a in audit])


def test_unpaid_rejects_finance_and_personal_policy_scope(client, provider):
    h = account(client)
    for scope in ["finance", "insurance"]:
        assert grant(client, h, [scope]).json()["error"]["code"] == "AI_SCOPE_UNAVAILABLE"
    assert not provider


def test_sample_retrieval_excludes_user_document_before_top_k_and_preview_no_call(client, provider):
    h = account(client)
    for index in range(6):
        assert client.post(P + "/documents", headers=h, files={"file": (f"personal{index}.txt", f"Insurance claim checklist PRIVATE_DOCUMENT_{index}. claim claim claim".encode())}).status_code == 200
    assert client.post(P + "/documents", headers=h, files={"file": ("sample.txt", b"Insurance claim checklist needs a hospital invoice and signed form.")}, data={"document_kind": "TEST_FIXTURE"}).status_code == 200
    assert grant(client, h, ["documents"]).status_code == 200
    preview = client.post(P + "/finance/assistant/preview", headers=h, json={"message": "insurance claim checklist", "privacy_revision": 1})
    assert preview.status_code == 200
    assert "PRIVATE_DOCUMENT" not in preview.text and "hospital invoice" in preview.text
    assert provider == []
    assert ask(client, h, 1).status_code == 200
    assert "PRIVATE_DOCUMENT" not in json.dumps(provider) and "hospital invoice" in json.dumps(provider)


def test_revocation_stale_revision_expiry_and_notice_change(client, provider, monkeypatch):
    h = account(client); s = grant(client, h).json()
    revoke = client.post(P + "/privacy/ai-permission", headers=h, json={"revision": s["revision"], "notice_version": s["notice_version"], "enabled": False})
    assert revoke.status_code == 200 and revoke.json()["scopes"] == []
    assert ask(client, h, 1).status_code == 403
    assert grant(client, h, revision=1).status_code == 409
    assert grant(client, h).status_code == 200
    assert ask(client, h, 1).status_code == 403
    with SessionLocal.begin() as db:
        row = db.scalar(select(AiPermission)); row.expires_at = now() - timedelta(seconds=1)
    assert ask(client, h, 3).status_code == 403
    assert grant(client, h).status_code == 200
    from app import privacy
    monkeypatch.setattr(privacy, "NOTICE_VERSION", "new-notice")
    assert ask(client, h, 4).status_code == 403 and not provider


def test_demo_sessions_do_not_share_optional_permission(client, provider):
    a = client.post(P + "/demo/session", json={"role": "STUDENT"}).json()["access_token"]
    b = client.post(P + "/demo/session", json={"role": "STUDENT"}).json()["access_token"]
    assert a != b
    h = {"Authorization": "Bearer " + a}; other = {"Authorization": "Bearer " + b}
    assert grant(client, h).status_code == 200
    assert client.get(P + "/privacy/ai-permission", headers=other).json()["enabled"] is False
    assert ask(client, other, 1).status_code == 403
    assert ask(client, h, 1).status_code == 200


@pytest.mark.parametrize("text", ["Email: student@example.com", "Phone +84 912 345 678", "CCCD: 012345678901", "passport: SECRET123", "diagnosis: secret", "AIza" + "x" * 35])
def test_sensitive_tripwire_stops_before_provider(client, provider, text):
    h = account(client); assert grant(client, h).status_code == 200
    assert ask(client, h, 1, message=text).json()["error"]["code"] == "AI_SENSITIVE_DATA"
    assert not provider


def test_csrf_owner_and_new_login_boundaries(client, provider):
    h = account(client)
    assert client.get(P + "/privacy/ai-permission").status_code == 200
    assert client.post(P + "/privacy/ai-permission", json={"revision": 0, "notice_version": "v", "enabled": False}).status_code == 403
    assert grant(client, h, ["history"]).status_code == 200
    h2 = account(client)
    assert client.get(P + "/privacy/ai-permission").json()["enabled"] is False
    assert ask(client, h2, 1).status_code == 403


def test_logout_all_revokes_other_sessions(client, provider):
    from fastapi.testclient import TestClient
    from app.main import app
    email = f"sessions-{uuid4()}@example.com"; password = "session-qa-password-2026"
    first = client.post(P + "/auth/register", json={"email": email, "display_name": "Session QA", "password": password})
    with TestClient(app) as second:
        second.post(P + "/auth/login", json={"email": email, "password": password})
        assert second.get(P + "/auth/session").status_code == 200
        r = client.post(P + "/auth/logout-all", headers={"X-CSRF-Token": first.json()["csrf_token"]}, json={})
        assert r.status_code == 200
        assert second.get(P + "/auth/session").status_code == 401
    assert client.get(P + "/auth/session").status_code == 401


def test_legacy_shared_demo_token_cannot_grant_ai_permission(client, provider):
    from app.security import signer
    from app.seed import STUDENT_ID
    h = {"Authorization": "Bearer " + signer.dumps({"sub": str(STUDENT_ID), "role": "STUDENT"})}
    assert client.get(P + "/privacy/ai-permission", headers=h).json()["enabled"] is False
    assert grant(client, h).json()["error"]["code"] == "AI_REAUTH_REQUIRED"


def test_demo_logout_revokes_prior_ai_permission(client, provider, student_headers):
    assert grant(client, student_headers).status_code == 200
    assert client.post(P + "/auth/logout", headers=student_headers, json={}).status_code == 200
    assert ask(client, student_headers, 1).status_code == 403


def test_fixed_preset_cannot_be_extended_by_client(client, provider):
    h = account(client)
    s = grant(client, h, ["documents"]).json()
    assert set(s["scopes"]) == {"history", "documents"}
    assert client.post(P + "/privacy/ai-permission", headers=h, json={"revision": s["revision"], "notice_version": s["notice_version"], "enabled": True, "preset": "SAMPLE_ASSISTANT", "scopes": ["finance"]}).status_code == 422
    assert grant(client, h, preset="INVENTED_PURPOSE").status_code == 422
    assert grant(client, h, preset="ACCOUNT_ASSISTANT").status_code == 403


@pytest.mark.parametrize("path,purpose", [("/documents", "documents"), ("/invoice-imports", "invoice-ocr"), ("/insurance/claims/00000000-0000-0000-0000-000000000001/attachments", "claim-attachments")])
@pytest.mark.parametrize("consent", ["", "documents:old-notice", "unrelated:files-2026-10-19-v1"])
def test_file_consent_rejected_before_processing(client, student_headers, monkeypatch, path, purpose, consent):
    from app import documents, ocr
    monkeypatch.setattr(documents, "extract", lambda *a: pytest.fail("No consent must never read document"))
    monkeypatch.setattr(ocr, "extract_file", lambda *a: pytest.fail("No consent must never run OCR"))
    r = client.post(P + path, headers={**student_headers, "X-Processing-Consent": consent},
                    files={"file": ("fictional.txt", b"Fictional data")}, data={"item_code": "INVOICE", "revision": "1"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "FILE_CONSENT_REQUIRED"


def test_sample_preset_excludes_personal_sources_even_on_paid_project(client, provider, monkeypatch):
    monkeypatch.setattr(settings, "gemini_data_mode", "PAID_PRIVATE")
    h = account(client)
    assert client.post(P + "/documents", headers=h, files={"file": ("private.txt", b"Insurance claim checklist PRIVATE_PAID_DOCUMENT.")}).status_code == 200
    assert grant(client, h, ["documents"]).status_code == 200
    assert ask(client, h, 1).status_code == 200
    assert "PRIVATE_PAID_DOCUMENT" not in json.dumps(provider)


def test_upload_acknowledgement_allowed_on_configured_frontend_origin(client):
    origin = settings.frontend_origins[0]
    r = client.options(P + "/documents", headers={"Origin": origin,
        "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "x-processing-consent,x-csrf-token"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == origin
    assert "X-Processing-Consent" in r.headers["access-control-allow-headers"]

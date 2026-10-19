import json
from uuid import uuid4
import pytest
from pydantic import SecretStr
from app import gemini
from app.config import settings
from app.db import SessionLocal
from app.models import User, RagDocument
from app.rag import PUBLICATION_NOTICE
from app.finance import ChatTurn
from app.study_assistant import route_question

P = '/api/v1'


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, 'gemini_enabled', True)
    monkeypatch.setattr(settings, 'gemini_api_key', SecretStr('fictional-test-credential'))
    monkeypatch.setattr(settings, 'gemini_data_mode', 'DEMO_ONLY')


def account(client, grant=True):
    r = client.post(P + '/auth/register', json={'email': f'unified-{uuid4()}@example.com', 'display_name': 'Unified test', 'password': 'fictional-unified-password'})
    h = {'X-CSRF-Token': r.json()['csrf_token']}
    if grant:
        p = client.get(P + '/privacy/ai-permission').json()
        assert client.post(P + '/privacy/ai-permission', headers=h, json={'enabled': True, 'revision': p['revision'], 'notice_version': p['notice_version'], 'preset': 'SAMPLE_ASSISTANT'}).status_code == 200
    return h, r.json()['user']['id']


def publish(client, h, uid):
    with SessionLocal.begin() as db: db.get(User, uid).is_rag_admin = True
    r = client.post(P + '/admin/rag/documents', headers=h, json={'title': 'Fictional renewal rule', 'publisher': 'Self-authored QA', 'license_note': 'CC0 fictional test only', 'content': 'Fictional short-term insurance renewal: the insurer does not guarantee renewal. A new application is required. No actual insurance entitlement is created.', 'source_kind': 'TEST_FIXTURE', 'category': 'POLICY', 'language': 'en', 'jurisdiction': 'CN'})
    assert r.status_code == 200, r.text
    doc = r.json()
    r = client.post(P + f"/admin/rag/documents/{doc['id']}/publish", headers=h, json={'revision': doc['revision'], 'notice_version': PUBLICATION_NOTICE, 'publication_confirmed': True})
    assert r.status_code == 200
    return r.json()


def ask(client, h, message, **extra):
    return client.post(P + '/study-assistant/chat', headers=h, json={'message': message, 'privacy_revision': 1, **extra})


@pytest.mark.parametrize('message,route', [('Bảo hiểm có bảo đảm tái tục không?', 'RAG'), ('What is a deductible?', 'RAG'), ('短期健康保险保证续保吗？', 'RAG'), ('健康金福等待多久？', 'RAG'), ('Thanh toán BHYT khác tỉnh theo quy định nào?', 'RAG'), ('Điều khoản nào bị loại trừ?', 'RAG'), ('NFRA quy định gì?', 'RAG'), ('Chào bạn', 'GEMINI'), ('How can I adapt to university life?', 'GEMINI'), ('How do I upload a policy document?', 'GEMINI'), ('如何适应留学生活？', 'GEMINI'), ('Please transfer money now', 'WORKFLOW'), ('Thanh toán ngay giúp tôi', 'WORKFLOW')])
def test_multilingual_server_routing(message, route):
    assert route_question(message, [])[0] == route


def test_followups_use_previous_user_question_but_new_topic_does_not():
    history = [ChatTurn(role='user', content='Insurance renewal conditions?'), ChatTurn(role='assistant', content='Untrusted answer')]
    route, query = route_question('Vậy cần những gì?', history)
    assert route == 'RAG' and 'renewal' in query
    assert route_question('Chào bạn', history)[0] == 'GEMINI'


def test_direct_gemini_does_not_send_unrelated_library_excerpts(client, enabled, monkeypatch):
    h, _ = account(client); captured = {}
    def model(payload):
        captured.update(payload)
        return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps({'answer': 'Start with a study routine.', 'source_ids': []})}]}}]}
    monkeypatch.setattr(gemini, 'request_json', model)
    reply = ask(client, h, 'How can I adapt to university life?', language='en').json()
    context = json.loads(captured['contents'][0]['parts'][0]['text'])
    assert reply['route'] == 'GEMINI' and reply['provider'] == 'GEMINI'
    assert all(e['kind'] != 'ORIGINAL_DOCUMENT_EXCERPT' for e in context['server_evidence'])
    assert 'SOURCE_ONLY_INSURANCE_RAG' not in captured['systemInstruction']['parts'][0]['text']


def test_rag_retrieves_then_generates_from_original_passages(client, enabled, monkeypatch):
    h, uid = account(client); doc = publish(client, h, uid); captured = {}
    def model(payload):
        captured.update(payload)
        return {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps({'answer': 'Fictional example: renewal is not guaranteed [R1].', 'source_ids': ['R1']})}]}}]}
    monkeypatch.setattr(gemini, 'request_json', model)
    reply = ask(client, h, 'Does this fictional insurance guarantee renewal?').json()
    context = json.loads(captured['contents'][0]['parts'][0]['text'])
    assert reply['route'] == 'RAG' and reply['method'] == 'RAG_GEMINI'
    assert any(c['document_id'] == doc['id'] for c in reply['citations'])
    assert all(e['kind'] == 'ORIGINAL_DOCUMENT_EXCERPT' for e in context['server_evidence'])
    assert 'SOURCE_ONLY_INSURANCE_RAG' in captured['systemInstruction']['parts'][0]['text']
    assert 'inlineData' not in json.dumps(captured)


def test_missing_rag_evidence_never_uses_model_memory(client, enabled, monkeypatch):
    h, _ = account(client)
    monkeypatch.setattr(gemini, 'generate', lambda *a: pytest.fail('No-evidence RAG must not call the provider'))
    reply = ask(client, h, 'Điều khoản ZXQUNSUPPORTEDVOLCANO').json()
    assert reply['route'] == 'RAG' and reply['status'] == 'INSUFFICIENT_INFORMATION'
    assert reply['citations'] == []


@pytest.mark.parametrize('question', ['Chào bạn', 'Bảo hiểm có tái tục không?'])
def test_both_cloud_routes_require_current_consent(client, enabled, monkeypatch, question):
    h, _ = account(client, grant=False)
    monkeypatch.setattr(gemini, 'generate', lambda *a: pytest.fail('No consent'))
    assert ask(client, h, question).status_code == 403


def test_preview_predicts_the_same_rag_route_without_model_call(client, enabled, monkeypatch):
    h, uid = account(client); publish(client, h, uid)
    monkeypatch.setattr(gemini, 'generate', lambda *a: pytest.fail('Preview must not call the provider'))
    result = client.post(P + '/study-assistant/preview', headers=h, json={'message': 'Insurance renewal conditions?', 'privacy_revision': 1}).json()
    assert result['route'] == 'RAG' and result['server_evidence'] and result['sent'] is False


@pytest.mark.parametrize('failure', [False, True])
def test_withdrawal_during_generation_invalidates_success_and_fallback(client, enabled, monkeypatch, failure):
    h, uid = account(client); doc = publish(client, h, uid)
    def model(*args):
        with SessionLocal.begin() as db: db.get(RagDocument, doc['id']).published = False
        if failure: raise gemini.GeminiFailure('TIMEOUT')
        return gemini.GeneratedAnswer(answer='Fictional renewal example [R1]', source_ids=['R1'])
    monkeypatch.setattr(gemini, 'generate', model)
    reply = ask(client, h, 'Insurance renewal conditions?').json()
    assert reply['status'] == 'SOURCES_CHANGED' and reply['citations'] == []


def test_free_mode_does_not_send_private_owned_documents(client, enabled, monkeypatch):
    h, _ = account(client)
    assert client.post(P + '/documents', headers=h, files={'file': ('private.txt', b'Insurance renewal PRIVATE_MARKER must never be sent to a free provider.')}).status_code == 200
    def model(question, history, language, evidence):
        assert 'PRIVATE_MARKER' not in json.dumps(evidence)
        return gemini.GeneratedAnswer(answer='Source-based explanation.', source_ids=[evidence[0]['id']])
    monkeypatch.setattr(gemini, 'generate', model)
    reply = ask(client, h, 'Insurance renewal conditions?')
    assert reply.status_code == 200 and 'PRIVATE_MARKER' not in reply.text


def test_rag_provider_failure_is_honest_and_action_requests_never_call_model(client, enabled, monkeypatch):
    h, uid = account(client); publish(client, h, uid)
    def unavailable(*args): raise gemini.GeminiFailure('PROVIDER_RATE_LIMIT')
    monkeypatch.setattr(gemini, 'generate', unavailable)
    reply = ask(client, h, 'Insurance renewal conditions?').json()
    assert reply['route'] == 'RAG' and reply['provider'] == 'EXTRACTIVE' and reply['fallback_reason'] == 'PROVIDER_RATE_LIMIT'
    monkeypatch.setattr(gemini, 'generate', lambda *a: pytest.fail('Actions never reach provider'))
    reply = ask(client, h, 'Thanh toán giúp tôi ngay').json()
    assert reply['route'] == 'WORKFLOW' and reply['executed_actions'] == []


@pytest.mark.parametrize('question', ['Insurance renewal conditions?', 'How can I adapt to university life?'])
@pytest.mark.parametrize('failure', [False, True])
def test_permission_revocation_during_both_routes_suppresses_reply(client, enabled, monkeypatch, question, failure):
    from sqlalchemy import select
    from app.models import AiPermission
    h, uid = account(client); publish(client, h, uid)
    def revoked(*args):
        with SessionLocal.begin() as db:
            row = db.scalar(select(AiPermission).where(AiPermission.user_id == uid))
            row.active = False
        if failure: raise gemini.GeminiFailure('TIMEOUT')
        return gemini.GeneratedAnswer(answer='Should be suppressed [R1]', source_ids=['R1'] if 'Insurance' in question else [])
    monkeypatch.setattr(gemini, 'generate', revoked)
    assert ask(client, h, question).status_code == 403

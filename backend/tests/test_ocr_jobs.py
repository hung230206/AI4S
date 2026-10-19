from datetime import timedelta
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi import BackgroundTasks
from app import ocr
from app.db import SessionLocal
from app.models import InvoiceImport, now
from app.security import ApiError
from test_insurance import create, new_claim

P = '/api/v1'
CONSENT = {'X-Processing-Consent': 'invoice-ocr:files-2026-10-19-v1'}
CLAIM_CONSENT = {'X-Processing-Consent': 'claim-attachments:files-2026-10-19-v1'}
FORM = b'CLAIM FORM - Self-authored fictional QA only\nTotal amount claimed: VND 722.600\nThis is not a payable invoice or an actual medical record.'
INVOICE = b'Invoice number: JOB-2026\nIssuer: Sample University\nBeneficiary: Sample School\nTotal due: CNY 800.00\nDue date: 2026-12-20'


def job(client, headers, text=INVOICE):
    r = client.post(P + '/invoice-imports/jobs', headers={**headers, **CONSENT}, files={'file': ('sample.txt', text, 'text/plain')})
    assert r.status_code == 202, r.text
    return r.json()


def test_job_returns_before_extraction_persists_and_deduplicates(client, student_headers, monkeypatch):
    scheduled = []
    monkeypatch.setattr(BackgroundTasks, 'add_task', lambda self, func, *args, **kwargs: scheduled.append((func, args)))
    h = student_headers
    source = job(client, h)
    assert source['status'] == 'QUEUED' and source['pages'] == []
    assert job(client, h)['id'] == source['id'] and len(scheduled) == 1
    assert client.get(f"{P}/invoice-imports/{source['id']}", headers=h).json()['status'] == 'QUEUED'
    func, args = scheduled[0]; func(*args)
    result = client.get(f"{P}/invoice-imports/{source['id']}", headers=h).json()
    assert result['status'] == 'COMPLETED'
    assert result['suggestions']['fields']['amount_cny']['value'] == '800.00'
    assert job(client, h)['id'] == source['id'] and len(scheduled) == 1
    assert client.get(f"{P}/invoice-imports/{source['id']}/download", headers=h).content == INVOICE


def test_failed_job_is_visible_and_retry_reuses_record(client, student_headers, monkeypatch):
    original = ocr.extract_file
    def fail(*args): raise ApiError('OCR_TIMEOUT', 'Bounded processing timeout', 422)
    monkeypatch.setattr(ocr, 'extract_file', fail)
    source = job(client, student_headers)
    result = client.get(f"{P}/invoice-imports/{source['id']}", headers=student_headers).json()
    assert result['status'] == 'FAILED' and result['error_code'] == 'OCR_TIMEOUT'
    monkeypatch.setattr(ocr, 'extract_file', original)
    assert job(client, student_headers)['id'] == source['id']
    assert client.get(f"{P}/invoice-imports/{source['id']}", headers=student_headers).json()['status'] == 'COMPLETED'


def test_pending_source_cannot_create_invoice(client, student_headers, monkeypatch):
    monkeypatch.setattr(BackgroundTasks, 'add_task', lambda *args: None)
    source = job(client, student_headers)
    r = client.post(P + '/invoices', headers=student_headers, json={'invoice_number': 'PENDING-1', 'institution_name': 'QA School', 'beneficiary_name': 'QA School', 'amount_cny': '800.00', 'due_date': '2026-12-20', 'import_id': source['id'], 'import_reviewed': True})
    assert r.status_code == 409 and r.json()['error']['code'] == 'IMPORT_NOT_READY'


def test_claim_form_is_not_an_invoice_and_cannot_be_saved_as_cny(client, student_headers):
    invoice_with_note = ocr.suggestions([{'page': 1, 'text': INVOICE.decode() + '\nKeep this invoice with your signed claim form.'}])
    assert invoice_with_note['document_type'] == 'INVOICE_OR_NOTICE'
    source = job(client, student_headers, FORM)
    result = client.get(f"{P}/invoice-imports/{source['id']}", headers=student_headers).json()
    assert result['suggestions']['document_type'] == 'CLAIM_FORM'
    assert result['suggestions']['currency'] == 'VND' and result['suggestions']['fields'] == {}
    r = client.post(P + '/invoices', headers=student_headers, json={'invoice_number': 'WRONG-1', 'institution_name': 'QA', 'beneficiary_name': 'QA', 'amount_cny': '722600', 'due_date': '2026-12-20', 'import_id': source['id'], 'import_reviewed': True})
    assert r.status_code == 422 and r.json()['error']['code'] == 'IMPORT_NOT_INVOICE'


def test_claim_handoff_requires_consent_keeps_original_and_rejects_stale_writes(client, student_headers):
    h = student_headers; policy, _, _ = create(client, h); claim, _ = new_claim(client, h, policy)
    source = job(client, h, FORM)
    path = f"{P}/insurance/claims/{claim['id']}/attach-import"
    body = {'import_id': source['id'], 'revision': claim['revision']}
    assert client.post(path, headers=h, json=body).status_code == 403
    result = client.post(path, headers={**h, **CLAIM_CONSENT}, json=body)
    assert result.status_code == 200, result.text
    data = result.json(); assert len(data['attachments']) == 1
    item = data['attachments'][0]; assert item['item_code'] == 'CLAIM_FORM'
    assert client.get(f"{P}/insurance/claims/{claim['id']}/attachments/{item['id']}", headers=h).content == FORM
    assert client.post(path, headers={**h, **CLAIM_CONSENT}, json=body).status_code == 409
    repeated = client.post(path, headers={**h, **CLAIM_CONSENT}, json={**body, 'revision': data['revision']})
    assert len(repeated.json()['attachments']) == 1


def test_jobs_and_handoff_reject_other_accounts(client, student_headers):
    h = student_headers; policy, _, _ = create(client, h); claim, _ = new_claim(client, h, policy); source = job(client, h, FORM)
    registered = client.post(P + '/auth/register', json={'email': f'ocr-{uuid4()}@example.com', 'display_name': 'Other QA', 'password': 'fictional-ocr-test-password'}).json()
    other = {'X-CSRF-Token': registered['csrf_token']}
    assert client.get(f"{P}/invoice-imports/{source['id']}", headers=other).status_code == 404
    assert client.get(f"{P}/invoice-imports/{source['id']}/download", headers=other).status_code == 404
    assert client.post(f"{P}/insurance/claims/{claim['id']}/attach-import", headers={**other, **CLAIM_CONSENT}, json={'import_id': source['id'], 'revision': claim['revision']}).status_code == 404


def test_job_requires_authentication_and_file_consent(client, student_headers):
    assert client.post(P + '/invoice-imports/jobs', headers=CONSENT, files={'file': ('sample.txt', INVOICE)}).status_code == 401
    assert client.post(P + '/invoice-imports/jobs', headers={**student_headers, 'X-Processing-Consent': 'invalid'}, files={'file': ('sample.txt', INVOICE)}).status_code == 403


def test_native_ocr_uses_local_models_and_bounded_single_thread_process(monkeypatch):
    calls = []
    monkeypatch.setattr(ocr.shutil, 'which', lambda name: '/local/tesseract' if name == 'tesseract' else None)
    def run(args, **kwargs):
        calls.append((args, kwargs)); return SimpleNamespace(returncode=0, stdout='Fictional recognised text')
    monkeypatch.setattr(ocr.subprocess, 'run', run)
    assert ocr.local_ocr(['private-image.png'], 'vi')[0]['ocr_engine'] == 'TESSERACT_NATIVE'
    assert 'vie+eng' in calls[0][0] and '--tessdata-dir' in calls[0][0]
    assert calls[0][1]['env']['OMP_THREAD_LIMIT'] == '1'
    assert 0 < calls[0][1]['timeout'] <= ocr.settings.ocr_timeout_seconds


def test_pending_job_rejects_second_file_and_interrupted_job_can_retry(client, student_headers, monkeypatch):
    scheduled = []
    monkeypatch.setattr(BackgroundTasks, 'add_task', lambda self, func, *args, **kwargs: scheduled.append((func, args)))
    source = job(client, student_headers)
    blocked = client.post(P + '/invoice-imports/jobs', headers={**student_headers, **CONSENT}, files={'file': ('other.txt', FORM)})
    assert blocked.status_code == 429 and blocked.json()['error']['code'] == 'OCR_BUSY'
    with SessionLocal.begin() as db:
        obj = db.get(InvoiceImport, source['id'])
        obj.suggestions = {**obj.suggestions, 'queued_at': (now() - timedelta(seconds=901)).isoformat()}
    status = client.get(f"{P}/invoice-imports/{source['id']}", headers=student_headers).json()
    assert status['status'] == 'FAILED' and status['error_code'] == 'OCR_INTERRUPTED'
    assert job(client, student_headers)['id'] == source['id'] and len(scheduled) == 2


def test_explicit_demo_quote_completes_without_external_fx(client, student_headers, monkeypatch):
    import app.main as main
    def offline(*args): raise AssertionError('Demo rate must not call the external FX service')
    monkeypatch.setattr(main, 'reference_rate', offline)
    invoice = client.post(P + '/invoices', headers=student_headers, json={'invoice_number': 'DEMO-RATE-QA', 'institution_name': 'QA University', 'beneficiary_name': 'QA University', 'amount_cny': '800.00', 'due_date': '2026-12-20'}).json()
    body = {'invoice_id': invoice['id'], 'settlement_currency': 'VND', 'demo_rate': True}
    quote = client.post(P + '/quotes', headers=student_headers, json=body)
    assert quote.status_code == 200, quote.text
    assert quote.json()['rate_source'] == 'DEMO_FIXED' and quote.json()['total_vnd'] == '2847000'
    assert client.post(P + '/quotes', headers=student_headers, json={**body, 'demo_rate': 'true'}).status_code == 422

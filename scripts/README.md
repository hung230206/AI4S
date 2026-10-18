# Current team commands

team.py setup/start/doctor/fetch-reference/package are the current handoff entry points; see TEAM_HANDOFF.md. check_acceptance_live.py --public-reference PATH verifies the owner A-Z flow without an operator code and optionally the original university PDF. It exports no credentials. Earlier tools remain below.

# Local setup and evidence tools

Run from the kit directory using the backend virtual environment except bootstrap/native PostgreSQL (standard library only):

- `bootstrap.py`: generate ignored local-only random secrets without overwriting settings.
- `local_postgres.py`: optional Windows binary fallback; isolated loopback cluster, no existing service changes.
- `demo_evidence.py`: actual success/failure/expiry/cancel/duplicate API operations into `submission/evidence/operations.json`. Adds only fictional fixture records; controlled quote timestamps exercise expiry.
- `browser_fixture.py`: add a new fictional invoice; print only its UUID for repeatable browser testing.
- `check_mvp_live.py`: actual HTTP smoke for registered account, private invoice, Frankfurter quote, uploaded document/citation/download/delete and revoked session; exports mvp-live-http.json without credentials.
- `dependency_licenses.py`: export installed package license metadata.
- `verify_source.py`: scan deliverable text for accidental local-secret copies.
- `validate_handoff.py`: supplied kit-level contract/reference validation, separate from app tests.

RUNBOOK.md contains Windows/Unix commands. Evidence never contains tokens, operator codes, signature headers or sensitive raw payloads. Failed browser traces remain ignored and must not be shared.


Student-finance tools:
- `setup_ocr.py`: download pinned public English, Vietnamese and Simplified Chinese Tesseract language models once; writes source/hash manifest under ignored `.local/ocr-models`.
- `ocr_runner.cjs`: bounded local Node/Tesseract.js worker called by the Python API; no user content is sent upstream.
- `create_student_finance_fixtures.py`: create self-authored printed images/scanned PDF fixtures under ignored `.local/qa-documents`, without writing account data.
- `benchmark_local_ocr.py`: optional Windows-font three-sample real OCR field-match smoke; records the small test-set limitation explicitly.
- `check_student_finance_live.py`: actual HTTP review/ledger/forecast/FX/scanned-policy/assistant/revocation evidence without credentials.

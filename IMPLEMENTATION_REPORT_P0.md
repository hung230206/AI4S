# Implementation report

Date: 2026-10-17 (Vietnam). Workspace: this extracted kit directory. Demo access: **local only**, http://localhost:3000; API documentation: http://127.0.0.1:8000/docs. No public hosting, real payment, external message or competition registration was performed.

## Delivered

P0 is implemented across FastAPI/Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL and Next.js App Router/TypeScript/Tailwind. The demo was installed and run on Windows using an isolated native PostgreSQL 18 cluster because Docker CLI was unavailable. Docker Compose for PostgreSQL 16 is included; its execution and Unix startup have not been validated on this host.

- Repeatable synthetic invoice/user seed, static versioned initial migration, database money/consent/status/uniqueness constraints, and a separate destructive-test database.
- Signed one-hour demo student/operator sessions, server-validated operator code, memory-only frontend bearer tokens, ownership checks and consistent error envelopes. Local operator controls are hidden in production frontend builds and backend simulation is gated by DEMO_MODE.
- Invoice list/detail, immutable persisted quote with server Decimal arithmetic, explicit ROUND_HALF_UP, DEMO_RATE badge, 10-minute expiry and exact fee breakdown: **800.00 CNY → 2,800,000 VND + 42,000 + 5,000 = 2,847,000 VND**.
- Idempotent order creation/confirmation with response snapshots, row locks and one provider attempt. Quote ID and reviewed total bind explicit consent. Cancel before processing; expiry and safe fresh-order retry; no terminal reversal.
- `PaymentProvider` abstraction with mock-only implementation. Persistent mock-provider outbox, asynchronous delivery through the actual webhook route, HMAC-SHA256 verification over raw bytes, timestamp bounds, unique event IDs, amount/currency/provider-ID checks and duplicate/late-event audit. Queued events survive API restart.
- Vietnamese responsive dashboard, invoice, checkout, status/polling, history, operator panel, event timeline, JSON export and printable watermarked receipt. All payment views clearly label simulation; no real payment QR/account.
- English technical documentation, security self-assessment, demo instructions, real API logs, test output and screenshots. Windows and Unix commands are in RUNBOOK.md; exact tested dependency resolutions are retained.

P1 delivered: a small read-only, source-labelled deterministic policy FAQ and source viewer. It uses the packaged fictional policy and refuses unspecified claims/benefits questions. No LLM account or external network is needed. Airwallex integration remains deliberately unimplemented/disabled; no supported insurance corridor is assumed. Topic C/D remains undecided.

## Actual verification

Commands below ran in the documented backend/frontend directories on this Windows host. Full output is retained under `submission/evidence/`.

| Command | Actual result |
|---|---|
| `python scripts/bootstrap.py` | Generated ignored random local secrets; existing settings preserved on repeat |
| `python scripts/local_postgres.py` | New isolated loopback PostgreSQL cluster + demo/test databases |
| `alembic upgrade head` | Initial static revision `4ad8203419ab` applied to demo and test DBs |
| `python -m app.seed` | Synthetic fixture + separate student/operator roles seeded; repeatability also tested |
| `pytest -q --junitxml=../submission/evidence/backend-junit.xml` | **42 passed**, 1 upstream deprecation warning; final measured backend run 19.66 s |
| `alembic check` | `No new upgrade operations detected.` |
| `npm run lint` | Passed with max warnings 0 |
| `npm run build` | Passed Next.js optimized build and TypeScript checks; all application routes emitted |
| `npm run test:e2e` | **4 passed**, Chrome desktop/mobile end-to-end suite; JSON and real screenshots saved |
| `python scripts/demo_evidence.py` using backend venv | SUCCEEDED, FAILED, EXPIRED, CANCELLED; signed duplicate event audited; JSON exported |
| `python scripts/validate_handoff.py` using backend venv | Contract references, source fixture, Decimal example and kit structure valid |
| `python scripts/verify_source.py` | No copies of generated local session/webhook/operator secrets in deliverable text files |
| `npm audit --omit=dev --json` | **0 runtime vulnerabilities** reported |
| `npm audit --json` | Exit 1: **5 high development-tool package-chain findings**, one unpatched braces advisory; preserved in audit JSON |

The deprecation warning concerns Starlette TestClient's use of httpx; it does not fail the suite. Browser's NO_COLOR/FORCE_COLOR warning is test-runner environment output. No performance/latency SLA or comprehensive accessibility certification is claimed.

Earlier verification found and fixed a blocking-ASGI/database-lock problem under concurrent duplicate webhooks, non-UTC response formatting from PostgreSQL's local session timezone, a synchronous React effect lint violation, and ambiguous Playwright error/focus selectors. Final passing outputs supersede the failed intermediate runs. No failing application tests are knowingly left unresolved. The development dependency advisory remains unresolved and is documented below.

## Supplied acceptance scenarios

All 17 fixture scenarios are exercised by pytest (several are expanded into parameterized cases):

| Fixture ID | Automated coverage |
|---|---|
| happy_path | `test_happy_path` |
| failed_payment | `test_failed_payment_and_fresh_retry` |
| cancel_before_confirm | `test_cancel_before_confirm` |
| expired_quote | `test_expired_quote`, `test_expired_quote_at_create` |
| quote_mismatch | `test_quote_mismatch` |
| client_tamper_amount | `test_client_tamper_amount` |
| confirm_twice | `test_confirm_twice` |
| idempotency_conflict | `test_idempotency_conflict` |
| duplicate_event | `test_duplicate_event` |
| invalid_hmac | `test_invalid_hmac` |
| stale_hmac_timestamp | `test_stale_hmac_timestamp` |
| event_amount_mismatch | `test_event_amount_mismatch` |
| out_of_order_after_success | `test_out_of_order_after_success` |
| cross_user_access | `test_cross_user_access`, `test_quote_owned_by_another_student` |
| simulate_forbidden | `test_simulate_forbidden` |
| operator_disabled_prod | `test_operator_disabled_prod` |
| parallel_confirms | `test_parallel_confirms`, `test_parallel_confirms_different_keys` |

Additional tests cover concurrent creates/webhooks, provider outage rollback, consent type/coercion rejection, event-ID content collision, old-event rejection, no-auth/forged sessions, seed repeatability, safe event output, changed/expired invoices, contract endpoint coverage, read-only policy and refusal of live-payment configuration.

## Evidence and demo replay

- `submission/evidence/operations.json`: generated from actual API and signed provider delivery. Expiry uses controlled fictional quote timestamps, then the actual confirm API; this technique is explicitly recorded in the file.
- `submission/evidence/backend-tests.txt`, `backend-junit.xml`, `browser-results.json`, `frontend-lint.txt`, `frontend-build.txt`: actual command results.
- `submission/evidence/screenshots/`: desktop dashboard/checkout/failure/receipt, mobile history/checkout, and print receipt. Images were captured from the running app and visually inspected for readable layout and conspicuous simulation notices.
- `submission/TECHNICAL_DOCUMENT.md`, `SECURITY_SELF_ASSESSMENT.md`, `DEMO_SCRIPT.md`: completed English handoff documents. The template-named copies are filled with the same final documentation.

Follow RUNBOOK.md for startup and a success/failure/cancellation/expiry/duplicate demonstration. Record a 4–5 minute screen video following DEMO_SCRIPT.md; pause recording while entering the local operator code. No video was fabricated or recorded in this implementation. Do not share `.env`, `.local`, virtual environments, node_modules or failed Playwright traces. The original fixture remains usable until its 2026-11-01 due date; create fresh fictional invoices for later/repeated success demos.

## Remaining limitations

1. This is a technical simulation: no insurer receives money, no coverage activates, no live FX is retrieved. Real corridor eligibility, licensed provider onboarding and regulatory obligations are unresolved/out of scope.
2. Full npm audit flags the ESLint dev-tool chain because braces ≤3.0.3 has an unpatched stack-exhaustion issue. Runtime audit is clean. No incompatible forced lint downgrade was applied. See https://github.com/advisories/GHSA-vfj7-8cjw-p6xm and the saved audit results. Python vulnerability auditing was not run.
3. Docker and Unix commands were not executed here. Native PostgreSQL Windows startup, migrations, seed, API, frontend, tests and browser flows were exercised. Thus cross-platform/fresh-Docker acceptance is documented, not claimed as measured.
4. Demo sign-in/code, local development DB role, no rate limiting, no real identity system, no production TLS/secret manager, and a mock in-process provider dispatcher make this unsuitable for public deployment. Keep it local. Audit logs are not tamper-proof against a database administrator.
5. No general insurance AI, real provider adapter, presentation deck or video is delivered. Deterministic policy guidance, technical/security documentation and capture instructions are provided. Topic selection remains with the team.

Source interpretation and deviations are recorded in IMPLEMENTATION_NOTES.md. Supplied reference documents were treated as implementation specifications within the user's request, not authority to publish, contact third parties or move funds.

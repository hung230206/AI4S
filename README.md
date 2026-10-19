# Demo

A web application that helps Vietnamese students in China read documents, plan expenses in CNY and VND, and understand insurance information. It connects document upload, reviewed form suggestions, budgeting, source-backed assistance and a traceable sandbox payment.

[GitHub](https://github.com/hung230206/AI4S) · [Hosted demo](https://ai4s-demo.onrender.com/) · [Hướng dẫn tiếng Việt](TEAM_HANDOFF.md)

**All payments are simulated. No real funds are exchanged or transferred, and no insurance is activated.** The hosted site and a local checkout can run different revisions. Release details and verification are recorded in [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md).

## Features

| Feature | What users can do |
| --- | --- |
| Personal accounts | Register, sign in and manage account-owned records and files. |
| Document reading | Upload images or PDFs, inspect extracted text and review suggested invoice or policy fields before saving. OCR results require human verification. |
| Invoices | Track CNY amounts, recipients, due dates and original documents; add an invoice to a spending plan. |
| Budgeting | Keep separate CNY and VND ledgers, record income and expenses, schedule entries and project balances over 30, 60 or 90 days. |
| Exchange-rate planning | View dated CNY/VND reference rates and estimate the budget impact of exchange-rate changes. |
| Insurance review | Compare needs against reviewed policy details, identify missing information and prepare an exportable claim document pack. |
| Study assistant | Use one floating chat. General questions receive explanations; evidence-dependent questions retrieve permitted passages before a language model produces a cited answer. Page navigation requires confirmation. |
| Knowledge administration | Administrators add, edit, review, publish, withdraw, trash and restore shared reference documents. |
| Sandbox payments | Review a server-calculated quote, confirm the amount, try success or decline outcomes and download a simulation receipt. |
| Privacy and preferences | Accept or decline processing notices, revoke AI consent in account settings, use Vietnamese, English or Chinese, and switch light/dark themes. |

The assistant cannot execute payments, modify financial records or submit claims. If a source-dependent question lacks evidence, it reports the gap rather than inventing policy terms.

## Technology

| Component | Implementation |
| --- | --- |
| Frontend | TypeScript, Next.js App Router, React, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Storage | PostgreSQL |
| Document processing | PDF text extraction and server-side Tesseract OCR with Chinese, Vietnamese and English models |
| Assistant | Rule-based routing, multilingual passage retrieval and optional server-side Gemini generation |
| Integrations | Frankfurter reference rates and a signed mock-payment provider |
| Verification | pytest, Playwright, ESLint and TypeScript checks |

```text
Browser → Next.js → same-origin API proxy → FastAPI → PostgreSQL
                                              ├─ document extraction / OCR
                                              ├─ retrieval → optional language model
                                              └─ mock provider → verified payment event
```

Money calculations and payment transitions are controlled by the backend. A browser redirect cannot mark an order successful. Signed events, idempotency and duplicate-event checks protect the sandbox workflow.

## Run locally

### Requirements

- Python 3.11, Node.js 22 or newer with npm, and Git.
- Docker with Compose for the commands below, or an existing PostgreSQL installation.
- Internet for the first dependency/model download and optional external services. The core demo does not require an LLM key or payment-provider account.

```sh
git clone https://github.com/hung230206/AI4S.git
cd AI4S
```

**Windows PowerShell**

```powershell
py -3.11 scripts/team.py setup --database docker
py -3.11 scripts/team.py start
```

**Linux or macOS**

```sh
python3 scripts/team.py setup --database docker
python3 scripts/team.py start
```

Setup generates an ignored `.env` with random local secrets, installs dependencies, applies migrations, seeds samples and downloads OCR models. It preserves an existing `.env` and does not reset an existing database. On Windows, `--database native` supports an installed PostgreSQL server; `--database existing` uses the database configured in `.env`.

Keep the launcher terminal open. **Ctrl+C** stops its application services. In another terminal, run `py -3.11 scripts/team.py doctor` on Windows or `python3 scripts/team.py doctor` on Unix.

| Address | Purpose |
| --- | --- |
| <http://localhost:3000/> | Application |
| <http://localhost:3000/test-lab> | Sample downloads and guided testing |
| <http://localhost:8000/docs> | Backend API documentation |
| <http://localhost:3000/api/v1/health> | API/database health through the frontend proxy |

Use `start --production` to build and serve the compiled frontend. Advanced operator controls require development mode. Detailed setup: [TEAM_HANDOFF.md](TEAM_HANDOFF.md). Same-Wi-Fi access: [LAN_TEST_GUIDE.md](LAN_TEST_GUIDE.md); use the host's actual LAN address.

## Try the main workflow

1. Create a personal account and open **Test A–Z** at `/test-lab`. Download the sample pack. Its documents are fictional test inputs.
2. Upload the **800 CNY insurance fee notice** under **Add invoice**. Review the recognised fields against the original, correct them if necessary and confirm before saving.
3. Create a ledger with **1,000 CNY** and add the invoice to its spending plan. With no other entries and that expense inside the forecast period, the projected balance is **200 CNY**.
4. Upload the sample policy, review its proposed fields and passages, then save. Ask the floating assistant about a term and inspect its citations. Generated answers require the optional model configuration below.
5. Open checkout, review the quote, select automatic **SUCCESS** sandbox processing and confirm. A verified provider event completes the order and enables its simulated receipt. Try **DECLINED** on a different unpaid invoice to test failure and retry.
6. Separately confirm the expense entry in the ledger. Sandbox payment does not record a real-world expense automatically. Recording a planned expense must not deduct it twice.
7. For a medical-expense scenario, create a claim case, attach sample records and export the preparation pack. This is a separate workflow, not a required step after every payment.

Sample dates are fixed. If an invoice is past due, adjust its date during review and record that change. Expected outcomes and error cases: [ACCEPTANCE_TESTS.md](ACCEPTANCE_TESTS.md).

## Assistant and knowledge setup

The assistant routes questions automatically. Evidence-dependent questions retrieve permitted passages, then ask the configured model to explain that evidence with citations. RAG supplies context; it does not train the model. Provider errors are shown explicitly, and extractive fallbacks are labelled.

To enable generation, set `GEMINI_ENABLED=true` and configure `GEMINI_API_KEY` in the backend `.env` or hosting secrets, then restart the backend. Keep `GEMINI_DATA_MODE=DEMO_ONLY` for this sample/public-data deployment. This mode blocks personal finance, policy and claim context from being sent to the free model service. Users must consent before external requests. See [GEMINI_GUIDE.md](GEMINI_GUIDE.md) and [PRIVACY_GUIDE.md](PRIVACY_GUIDE.md).

Provision an administrator once on a new installation, from `backend/`:

```powershell
# Windows PowerShell
.venv/Scripts/python.exe -m app.rag_admin --email admin.rag@example.com
```

```sh
# Linux or macOS
.venv/bin/python -m app.rag_admin --email admin.rag@example.com
```

Generated credentials are saved in ignored `.local/rag-admin-test.json` for sign-in at `/admin/rag`. The command does not promote an existing ordinary account or reset an existing password. Never publish this credential file.

A new database seeds labelled, team-authored references. The curated Chinese collection must be imported separately through an administrator; the existing hosted database is not copied on installation. Publisher URLs, dated source review and import instructions: [China corpus report](docs/23_CHINA_RAG_CORPUS.md) and [RAG_GUIDE.md](RAG_GUIDE.md). Public references do not establish an individual student's coverage or eligibility.

## Tests

### Automated checks

Backend tests require a separate PostgreSQL database with a name ending in `_test`. A fresh Docker volume creates `insurance_payment_test`. For another instance, configure `TEST_DATABASE_URL` for a dedicated test database. The suite truncates test tables; never target useful application data.

**Windows PowerShell**, from the repository root:

```powershell
Push-Location backend
.venv/Scripts/python.exe -m pytest -q
Pop-Location
Push-Location frontend
npm run lint
npx tsc --noEmit
npm run build -- --webpack
Pop-Location
```

**Linux or macOS**, from the repository root:

```sh
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm run lint && npx tsc --noEmit && npm run build -- --webpack)
```

### Browser tests

Start the normal application in development mode with `team.py start`. The suites create QA accounts and fictional records; use an isolated local demo database. Provision the administrator above before running the complete suite.

Playwright uses installed Google Chrome by default. Alternatively, run `npx playwright install chromium` from `frontend/` and set `PLAYWRIGHT_CHANNEL=chromium` in that terminal.

```powershell
# Windows PowerShell, from the repository root
Push-Location frontend
$env:RAG_BROWSER_ADMIN_CREDENTIALS = (Resolve-Path ../.local/rag-admin-test.json).Path
npx playwright test
Pop-Location
```

```sh
# Linux or macOS, from the repository root
(cd frontend && RAG_BROWSER_ADMIN_CREDENTIALS=../.local/rag-admin-test.json npx playwright test)
```

Use `PLAYWRIGHT_BASE_URL` for a different local port. Automated model tests mock external responses; optional real-provider checks are documented in [GEMINI_GUIDE.md](GEMINI_GUIDE.md).

### Representative cases

| Scenario | Expected result | Test source |
| --- | --- | --- |
| Document reading | Reviewable suggestions; invalid files fail clearly | `backend/tests/test_document_assist.py`, `frontend/tests/document-assist.spec.ts` |
| Record a planned expense | No double deduction | `backend/tests/test_student_finance.py` |
| Expired quote or altered amount | Server rejects the request | `backend/tests/test_payments.py` |
| Duplicate request, replay or invalid signature | No duplicate settlement; unverified events cannot change status | `backend/tests/test_payments.py` |
| Cross-account access | Private records and files remain inaccessible | `backend/tests/test_mvp.py`, `backend/tests/test_privacy.py` |
| Withdraw consent or retire a source | New requests respect consent and source availability | `backend/tests/test_privacy.py`, `backend/tests/test_rag.py` |
| Ask to open a page | Confirmation appears before navigation | `frontend/tests/assistant-navigation.spec.ts` |

### Recorded results

Saved results from **20 October 2026** are listed below. They do not certify every new installation or cloud configuration.

| Suite | Result | Evidence |
| --- | --- | --- |
| Full backend | 373 passed, 1 upstream deprecation warning | [Backend log](submission/evidence/recording-en-full-backend.txt) |
| Normal application browser regression | 54 passed | [Browser log](submission/evidence/video-normal-browser.txt) |
| Separate local recording rehearsal | 5 passed | [Recording log](submission/evidence/video-after-controls.txt) |

The optional [recording edition](docs/LOCAL_RECORDING_EDITION.md) uses a separate local database, exact sample files and prepared recognition/chat responses. It does not benchmark live OCR or model accuracy and is disabled in the normal application and Render configuration.

## Deployment

The Render Blueprint builds a Docker image with the frontend and API behind one public origin.

1. Connect this repository to Render and create a Blueprint using [`render.yaml`](render.yaml).
2. Review the web service and PostgreSQL resources before creating them. Store secrets in the hosting environment; do not upload a local `.env`.
3. Wait for a healthy deployment, open its assigned HTTPS URL and run `/test-lab` and the acceptance cases.
4. Verify the deployed commit. **On Commit** deployment triggers on pushes to the linked branch; local edits alone do not update the site.

Deployment files: [`deploy/cloud.Dockerfile`](deploy/cloud.Dockerfile), [`scripts/cloud_start.py`](scripts/cloud_start.py) and [`render.yaml`](render.yaml). Startup applies migrations and seeds before serving traffic. Review current hosting resource, database retention and idle limits. Full instructions: [DEPLOY_RENDER.md](DEPLOY_RENDER.md).

Local full-stack Docker alternative:

```sh
python3 scripts/bootstrap.py
docker compose -f compose.yaml -f compose.app.yaml up --build
```

On Windows, use `py -3.11 scripts/bootstrap.py` for the first command. The implementation report distinguishes actual native/cloud checks from target environments that still need validation.

## Repository and submission contents

```text
backend/       API, migrations and pytest cases
frontend/      Next.js application and browser tests
fixtures/      Team-authored sample documents and seed data
scripts/       Setup, OCR, diagnostics, evidence and packaging tools
deploy/        Docker build definitions
contracts/     API specification
database/      Database setup references
docs/          Feature guides and research with source URLs
submission/    Technical/security documents and test evidence
```

| Required item | Location |
| --- | --- |
| Source code and GitHub | [hung230206/AI4S](https://github.com/hung230206/AI4S), `backend/`, `frontend/` and supporting directories |
| README | This document |
| Deployment guide | [DEPLOY_RENDER.md](DEPLOY_RENDER.md), [TEAM_HANDOFF.md](TEAM_HANDOFF.md) |
| Test cases and expected outcomes | [ACCEPTANCE_TESTS.md](ACCEPTANCE_TESTS.md), `backend/tests/`, `frontend/tests/` |
| Technical document | [submission/TECHNICAL_DOCUMENT.md](submission/TECHNICAL_DOCUMENT.md) |
| Security self-assessment | [submission/SECURITY_SELF_ASSESSMENT.md](submission/SECURITY_SELF_ASSESSMENT.md) |
| Implementation and verification | [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) |

Create a source ZIP with `py -3.11 scripts/team.py package` on Windows or `python3 scripts/team.py package` on Unix. Output: `output/Demo_Team_Handoff.zip`, with per-file hashes. Local secrets, databases, dependencies and downloaded third-party originals are excluded. Set up imported references and accounts separately on another database.

## Current boundaries

- Ledgers contain declared records, not custodial balances. Forecasts calculate scheduled entries; they are not machine-learning or exchange-rate predictions.
- Payments are mock-only. Bank transfers, real currency conversion, insurer reconciliation and insurance activation are not implemented.
- Claim support prepares records; it does not submit to insurers, adjudicate coverage or issue payouts.
- OCR and generated answers can be wrong. Review original documents, amounts and contract terms.
- MFA, email verification/recovery, complete retention/erasure workflows and independent penetration testing remain open work. Use fictional data for the public demo.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution and the security assessment and implementation report for permission controls, known risks and release limitations.

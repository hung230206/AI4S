## Một Trợ lý du học

Mở `/copilot`: câu hỏi được tự định tuyến sang RAG + Gemini hoặc Gemini tổng quát. Không có hai ô chat hoặc nút chọn chế độ. `/knowledge` chuyển về cùng trợ lý; trang nguồn và admin RAG được giữ lại. [Luồng và kiểm thử](docs/UNIFIED_STUDY_ASSISTANT.md).

## China-only RAG corpus (19 October 2026)

Competition selection: [dated review and excluded source](docs/CHINA_RAG_COMPETITION_SELECTION.md). The active local/online shared library contains 8 selected current China references: 3 IAC, 2 NFRA, 3 NHSA; fictional library fixtures are drafts. Original product wording, disclosure metadata, regulations and public social-insurance guidance are explicitly distinguished. Source registry, scope, actual validation and reproduction: [China corpus report](docs/23_CHINA_RAG_CORPUS.md). Local original/prepared files: output/China_RAG_Corpus (excluded from public Git/ZIP). Current provider availability and the pending Render model setting are recorded in IMPLEMENTATION_REPORT.md; a rate-limited extractive fallback is not a generated LLM answer.

## Managed Topic D RAG (19 October 2026)

User Q&A: `/knowledge` now retrieves passages and lets Gemini synthesize a cited explanation after binary consent. The gateway uses 3.5 Flash-Lite with a bounded alternate for older model settings. Actual tests/deployment: IMPLEMENTATION_REPORT.md. Administrator CRUD/publication: `/admin/rag` with a server-provisioned account. See [RAG_GUIDE.md](RAG_GUIDE.md) for the complete admin-to-student test flow and [research/method](docs/22_TOPIC_D_MANAGED_RAG.md). Credentials are in an ignored private local file, never in this repository. Gemini still requires binary session consent; the source library can be searched locally without a model.

# Demo Student Finance MVP

## AI privacy and keyboard update — 19 October 2026

Chat: Enter sends, Shift+Enter inserts a newline, IME composition does not submit. Copilot starts in direct lookup; knowledge-page questions offer RAG + Gemini after explicit permission. Gemini uses the fixed sample/public-data preset, preview and revocation. Read [PRIVACY_GUIDE.md](PRIVACY_GUIDE.md) and [research/security design](docs/21_PRIVACY_PERMISSIONS_RESEARCH.md).

The free demo uses `GEMINI_DATA_MODE=DEMO_ONLY`: no personal budget or reviewed-policy context is sent to Gemini; personal `USER_PROVIDED` documents are excluded. Use direct lookup for private records. A paid-private deployment requires operator/legal verification, not merely changing a flag. Run `python -m alembic upgrade head` from `backend/` before starting an existing checkout.


Optional Gemini chatbot is integrated with server-side credentials, owned sources, recent conversation and direct-lookup fallback. Setup, privacy, actual test evidence and Render configuration: [GEMINI_GUIDE.md](GEMINI_GUIDE.md).

Repository: https://github.com/hung230206/AI4S

**Live demo:** https://ai4s-demo.onrender.com/test-lab — sign up, download the sample pack and follow the six steps. Clear invoice OCR/text policy flows passed HTTPS checks; a dense scanned public PDF hit the Free-host OCR timeout.

**Online demo:** [Deploy to Render](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Fhung230206%2FAI4S). Read [DEPLOY_RENDER.md](DEPLOY_RENDER.md) first: Free services sleep on idle; the Free database expires after 30 days. The button prepares a new deployment in your own Render account; it does not imply an existing live site.

**Team handoff:** Start with [TEAM_HANDOFF.md](TEAM_HANDOFF.md), [ACCEPTANCE_TESTS.md](ACCEPTANCE_TESTS.md) and `/test-lab`. Upload fixtures download from the app; automatic sandbox methods complete the normal test flow without an operator code. Setup/start/doctor/package commands are in `scripts/team.py`. The current source ZIP is generated locally under `output/`.

# Insurance Cross-border Payment Assistant — Codex Implementation Kit

**Student-finance upgrade (18/10/2026):** Local reviewed OCR for invoices/scanned policies, CNY/VND income/expense ledgers, scheduled 30/60/90-day cash-flow projections, dated FX history/budget scenarios and a grounded read-only student copilot are implemented. See [STUDENT_FINANCE_GUIDE.md](STUDENT_FINANCE_GUIDE.md). OCR setup: `npm ci` in `frontend/`, then `python scripts/setup_ocr.py` at the kit root; run `alembic upgrade head` in `backend/`. Payment remains explicitly sandbox.

**Current MVP foundation:** Real email/password accounts, private user-entered invoices, connected Frankfurter CNY/VND reference rates, policy PDF/text upload and cited excerpt search, invoice/history filters and CSV export are implemented. Read [MVP_GUIDE.md](MVP_GUIDE.md) for the user journey. Choose **Tạo tài khoản** for an empty private workspace; sample records are an optional separate sandbox. Payment execution still uses the verified local sandbox because no provider account is configured. Latest results are in [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md); the initial P0 report is archived in `IMPLEMENTATION_REPORT_P0.md`.

**Implemented application:** See [RUNBOOK.md](RUNBOOK.md) for the current Windows/Unix setup, demo and verification commands; [IMPLEMENTATION_REPORT.md](IMPLEMENTATION_REPORT.md) records actual results. The original brief below is retained for provenance. Run `python scripts/bootstrap.py` to generate local secrets before starting the API; copying placeholders alone intentionally does not start the app.

**Scope:** reusable payment module for 2026 Shenzhen FinTechathon (Topic C or Topic D undecided).

**Target:** a working, locally runnable WEB + API + PostgreSQL demo with real state transitions and simulated money.

**Language:** Vietnamese UI initially, English code and competition submission artifacts.
**Starting point:** the supplied implementation brief has now been implemented as a local FastAPI + Next.js + PostgreSQL application. Money, beneficiary and policy data remain synthetic.

## Open first

1. `START_HERE_CODEX.md` — single agent prompt and execution order.
2. `AGENTS.md` — non-negotiable rules for the coding agent.
3. `docs/01_PRODUCT_SCOPE.md` and `docs/02_ARCHITECTURE.md` — behavior and architecture.
4. `contracts/openapi.yaml`, `database/schema.sql`, `fixtures/` — implementation contracts.
5. `docs/06_TEST_PLAN.md` and `docs/08_ACCEPTANCE.md` — verification gates.

## Core demo

A Vietnamese student views a **synthetic** Chinese student-insurance invoice denominated in CNY, obtains a **synthetic** VND FX quote with transparent fees, explicitly confirms a simulated payment, receives asynchronous mock provider events, sees the final status and a receipt clearly marked **SIMULATED — NOT A PROOF OF PAYMENT**. The core must remain useful if Topic C is chosen (FX/payment focus) or Topic D is chosen (insurance policy context).

### P0, must work completely offline except localhost

- Two applications: FastAPI API (Python 3.11+) and Next.js TypeScript frontend (Node 20+).
- PostgreSQL with Docker Compose (or documented local Postgres); migrations, seed data, deterministic demo user.
- Invoice list/detail, quote, fees/FX breakdown, consent, processing state, mock success/failure/cancellation, history, simulated receipt, event trace.
- Security: all amounts server-computed with `Decimal`, signed mock-provider events, idempotency, replay protection, ownership check, proper state machine.
- Automated unit/integration tests and repeatable demo script.

### P1, only after P0 is green

- Rules-based insurance guidance from `fixtures/demo_policy.md`; explicit source citation.
- AI/LLM is **optional** and must never create/confirm/capture payment by itself.
- Provider interface prepared for Airwallex Sandbox behind disabled-by-default feature flag. Do not invent unsupported endpoint payloads.

## Run target (Codex must make these commands succeed)

```bash
cp .env.example .env
docker compose up -d db
cd backend && python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1; Linux/macOS: source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
# new terminal
cd frontend && npm install && npm run dev
# tests
cd backend && pytest -q
cd frontend && npm run lint && npm run build
```

Target addresses: `http://localhost:3000` (UI) and `http://localhost:8000/docs` (FastAPI docs). If necessary, deviate only with explicit documented rationale.

## Competition caveats

- Official international-track instructions say **choose one** of Topic C or D when registering; shared core may serve both while research continues.
- Competition material accepts operation logs in simulated accounts or sandbox for non-on-chain topics; no real payment is necessary for the prototype.
- This repo **does not represent a valid route to pay a Chinese insurer**. Demo payee, payer, invoice and FX/fees are synthetic and must remain clearly labeled.
- Do not use real account credentials, passport data or payment cards.

Sources and known gaps: `docs/09_SOURCES_AND_ASSUMPTIONS.md`. Original user proposal under `reference/`.

## Combined Topic C + D journey (19 October 2026)

Open `/insurance`: upload and review a cited policy, compare coverage needs, plan a native-currency premium, create an explicitly user-authored sandbox fee estimate, and prepare/export a private claim case. Dashboard, Test Lab and copilot link to the journey. Download dated self-authored inputs from the page. See `TOPIC_C_D_GUIDE.md` and `docs/20_TOPIC_C_D_RESEARCH_AND_IMPLEMENTATION.md`. Claims are preparation only; no insurer submission, eligibility decision, payout or real transfer is implemented.

PowerShell: `backend/.venv/Scripts/python.exe scripts/check_insurance_live.py --url http://localhost:3000`

Unix: `backend/.venv/bin/python scripts/check_insurance_live.py --url http://localhost:3000`

The optional `--with-gemini` flag consumes one provider request with synthetic data. Normal acceptance does not require an AI key.

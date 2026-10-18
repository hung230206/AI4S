# Current team launcher

The verified native setup and A-Z flow are in [TEAM_HANDOFF.md](TEAM_HANDOFF.md). From a new checkout: `py -3.11 scripts/team.py setup --lan` then `py -3.11 scripts/team.py start --production --lan` on Windows; Unix uses `python3` and manual LAN origin configuration. `python scripts/team.py doctor` checks readiness. Previous individual setup commands follow for troubleshooting.

# Run the local mock application

## Student-finance extension — required setup

The current guide is [STUDENT_FINANCE_GUIDE.md](STUDENT_FINANCE_GUIDE.md). Static migration `9f40f776cbf8` preserves existing data and adds finance wallets/plans/entries and reviewed invoice sources. Run `alembic upgrade head` before starting the upgraded API. Install backend locked dependencies (now including Pillow and pypdfium2), `npm ci` in `frontend/`, then download the three public language models once. Node.js and the installed frontend Node packages must also be available on the API host for the local OCR subprocess. No OCR API key or private-document upload to an external service is used.

From the kit root on Windows:

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
backend\.venv\Scripts\python.exe -m pip install -e './backend[dev]'
python scripts/setup_ocr.py
Push-Location backend
.\.venv\Scripts\alembic.exe upgrade head
Pop-Location
```

The migration command runs in the tested backend working directory.

Unix from the kit root:

```sh
backend/.venv/bin/python -m pip install -r backend/requirements.lock.txt
backend/.venv/bin/python -m pip install -e './backend[dev]'
python3 scripts/setup_ocr.py
(cd backend && .venv/bin/alembic upgrade head)
```

After both servers are running, the following evidence tools can be used from the kit root (Unix: replace the Python executable with `backend/.venv/bin/python`):

```powershell
backend\.venv\Scripts\python.exe scripts/create_student_finance_fixtures.py
backend\.venv\Scripts\python.exe scripts/benchmark_local_ocr.py
backend\.venv\Scripts\python.exe scripts/check_student_finance_live.py --url http://localhost:3000
```

The optional multilingual smoke script uses installed Windows fonts; it does not redistribute them or claim a general OCR benchmark. The live script uses isolated self-authored QA input and exports no credentials. Current JSON results are in `submission/evidence/`. OCR scans have a five-page cap; text policies retain 50 pages. Choose the file's main OCR language when known. An unavailable OCR engine returns an explicit error; the manual form and non-OCR functions remain usable.

## Current MVP foundation

Use [MVP_GUIDE.md](MVP_GUIDE.md) for the current product journey. The application now has registered accounts and connected Frankfurter reference FX. Run `pip install -r requirements.lock.txt` then `pip install -e '.[dev]'` in the backend virtual environment to include Argon2, email validation, multipart uploads and pypdf, followed by **`alembic upgrade head`**. New revision `20261017_mvp` preserves all existing records and adds accounts/sessions, reference FX and private policy documents. Do not replace an existing database with the raw logical schema.

On first visit, **Tạo tài khoản** creates an empty personal workspace. Passwords are hashed with Argon2id. Cookie sessions last 24 hours, support logout/revocation and require CSRF for mutations; use `COOKIE_SECURE=true` with HTTPS. The legacy automatic demo selector is no longer the default; **Dùng thử sandbox với dữ liệu mẫu** selects that separate workspace explicitly. A prior sandbox preference may persist until sign-out.

User-entered invoices use Frankfurter reference rates (no API key) with a 6-hour fetch cache and maximum 7-day observation age. Upstream failure may reuse an eligible stored observation with a visible stale flag; it never switches a user invoice to DEMO_FIXED. Application fee settings `SERVICE_FEE_PERCENT` / `SERVICE_FIXED_FEE_VND` default to 0 and do not invent provider fees. The original `FX_DEMO_*` values apply only to synthetic sandbox invoices. PDF/TXT/MD documents are private, max 5 MB, 50 pages and 500,000 extracted characters; image/PDF scans can now be recognized locally up to five pages after OCR setup.

After starting servers, run `backend/.venv/Scripts/python.exe scripts/check_mvp_live.py` (Unix: `backend/.venv/bin/python`) from the kit root for actual HTTP account/invoice/Frankfurter/document/logout smoke evidence. It creates an isolated QA account; it never prints or exports its credentials. Final tests now include the original sandbox regression suite plus account/invoice/FX/document tests and browser workflows. The setup commands below still apply; the original demo-only explanations are retained as sandbox instructions. No production payment provider has been connected.

Run commands from this extracted kit directory (the folder containing this file). Tested on Windows with Python 3.11, Node 24, PostgreSQL 18 and Chrome. Docker Compose targets PostgreSQL 16; Docker was unavailable on the implementation machine, so the documented isolated native PostgreSQL fallback was exercised instead. No external service account is required. Initial dependency downloads and fresh Frankfurter reference observations need internet; the frontend uses local assets/system fonts. Private invoices and document content are never sent to Frankfurter.

## Windows PowerShell

```powershell
python scripts\bootstrap.py
docker compose up -d db
# If Docker is unavailable and PostgreSQL 16/17/18 binaries are installed:
# python scripts\local_postgres.py
py -3.11 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock.txt
backend\.venv\Scripts\python.exe -m pip install -e './backend[dev]'
Set-Location backend
.venv\Scripts\alembic.exe upgrade head
.venv\Scripts\python.exe -m app.seed
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another PowerShell terminal, starting in the kit directory:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open **http://localhost:3000**, API docs **http://127.0.0.1:8000/docs**. Register/sign in for a private workspace. The separate sandbox account is opened only when selected on the sign-in screen (or when an existing sandbox preference is restored). Registered sessions use HttpOnly cookies; sandbox/operator bearer tokens stay in memory. Operator tokens are separate and disappear on reload.

## Unix shell

```bash
python3 scripts/bootstrap.py
docker compose up -d db
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.lock.txt
backend/.venv/bin/python -m pip install -e './backend[dev]'
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# second terminal, kit directory:
cd frontend
npm ci
npm run dev
```

Unix instructions and Docker startup are supplied but were not executed on this Windows host. Native Postgres users must create both `insurance_payment_demo` and `insurance_payment_test` and configure their connection URLs. Docker creates both on a fresh volume. For an existing Docker volume missing the test DB: `docker compose exec db createdb -U fintech_demo insurance_payment_test`. Do not delete a database volume to solve this.

## Reproduce the demonstration

1. Open an invoice, choose **Xem báo giá mô phỏng**, then **Tạo báo giá mô phỏng**. The fixture is 800.00 CNY, DEMO_RATE 3,500 VND/CNY, 42,000 + 5,000 VND fees, total **2,847,000 VND**.
2. Review the total and tick the consent checkbox. Click **Xác nhận thanh toán mô phỏng**. The status becomes PROCESSING, with no success until a verified event arrives.
3. Open **Mở bảng vận hành demo** in another tab. Read `DEMO_OPERATOR_CODE` from your ignored local `.env`; enter it in the password field. Do not show or record this code in screenshots/video.
4. Choose a mock success/failure event. The persistent mock-provider worker sends HMAC-signed bytes into the webhook route. Return to the student tab; polling shows the verified result. Success permits a printable, watermarked simulation receipt. Failure has no receipt and offers a fresh quote/order.
5. In the operator panel choose **Phát lại sự kiện**. Reload the order to see the duplicate audit entry. Use **Xuất nhật ký JSON** for a safe operation log.
6. Cancel an awaiting order using the checkout cancel button. To repeat success on a fresh fictional invoice: run `backend/.venv/Scripts/python.exe scripts/browser_fixture.py` on Windows (Unix: `backend/.venv/bin/python scripts/browser_fixture.py`). Open `/invoices/<printed UUID>`.
7. For quote expiry, leave an unconfirmed quote open for 10 minutes. For a faster local rehearsal, set `FX_QUOTE_TTL_SECONDS=5` in `.env`, restart the API and create a new quote; restore 600 afterward. The evidence script also tests expiry using controlled fixture timestamps.

One invoice permits one active/succeeded order. This intentionally prevents paying the same fictional bill twice. A failed/cancelled/expired order can be retried with a new quote and order.

## Verification (Windows)

```powershell
Set-Location backend
.venv\Scripts\pytest.exe -q --junitxml=../submission/evidence/backend-junit.xml
.venv\Scripts\alembic.exe check
.venv\Scripts\python.exe ..\scripts\demo_evidence.py
Set-Location ..\frontend
npm run lint
npm run build
# Start frontend and backend before browser tests. Chrome is used by default.
npm run test:e2e
# Without Chrome: npx playwright install chromium; $env:PLAYWRIGHT_CHANNEL = 'chromium'
Set-Location ..
python scripts\verify_source.py
backend\.venv\Scripts\python.exe scripts\validate_handoff.py
```

Unix uses `backend/.venv/bin/pytest`, `backend/.venv/bin/alembic` and `backend/.venv/bin/python`; npm commands are identical. Set `PLAYWRIGHT_CHANNEL=chromium` if using Playwright Chromium. Browser tests add fictional invoices without deleting existing records. Backend tests truncate only the database whose name ends `_test`; configure `TEST_DATABASE_URL` if different. Never point it at a database containing useful data.

`scripts/demo_evidence.py` uses actual app routes, provider signing, webhook delivery and database persistence. It adds four fictional invoices to the configured demo DB, with new IDs on each run. Evidence is in `submission/evidence/operations.json`. Screenshots and browser JSON are in the same evidence directory. Failed Playwright traces can include tokens/operator input; `frontend/test-results/` is ignored and must not be shared.

For production-mode frontend smoke testing, stop `npm run dev`, run `npm run build` then `npm start`. This remains a **mock-only local application**. Production frontend builds hide operator controls; use `npm run dev` for the complete operator-led demo. The backend also requires DEMO_MODE and a validated operator session for simulation. `ALLOW_REAL_PAYMENTS=true`, other provider selection, or Airwallex enablement is rejected at startup.

Stop the app servers with Ctrl+C. Docker: `docker compose stop db`. Native isolated Windows cluster: `& 'C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe' -D '.local\pgdata' stop` (adjust binary version). Existing system PostgreSQL services are never modified by the fallback script.

## Configuration and security limits

`.env.example` contains only development placeholders. `scripts/bootstrap.py` creates random local secrets without printing them or overwriting an existing `.env`. Existing placeholder settings must be replaced locally before startup. The `.env` stays ignored. The DB password is a documented local-only development placeholder. Native fallback creates its own cluster under ignored `.local/`, bound to loopback, and uses a development superuser; it is unsuitable for shared hosting.

Default UI origin is `http://localhost:3000`; use that address to satisfy CORS. To change API/origin, update root `.env` and provide `frontend/.env.local` with the appropriate `NEXT_PUBLIC_API_BASE_URL`, then rebuild. Keep all services on loopback. Demo sign-in has no rate limiter, MFA, or real identity verification; never expose this prototype to the internet. All times are UTC in API responses, localized to Vietnam in the UI. Fixture due date remains 2026-11-01; after that date use a fresh fictional browser fixture.

Dependency auditing and known dev-tool advisory are documented in `submission/SECURITY_SELF_ASSESSMENT.md`. No deployment, external communication, registration, real payment, or actual insurance activation is performed.

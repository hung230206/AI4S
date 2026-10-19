# Current release — feature-triggered binary permissions (19 October 2026)

## Outcome

Clicking Gemini, invoice OCR, policy/document upload or a claim attachment now opens a purpose-specific native modal. It has a fixed data/purpose summary, a details hyperlink that opens the matching public privacy section in a new tab, and exactly **Agree / Disagree**. There is no scope or acknowledgement checkbox picker. VI/EN/ZH are supported, with centered desktop and scrollable mobile dialogs.

Gemini uses the server-defined SAMPLE_ASSISTANT preset: question, up to three previous Gemini turns from the same grant, and up to three sample/public excerpts. No personal finance/policy summaries or claim records are granted by this UI, including in paid mode. Agreement enables Gemini without sending a question. Refusal keeps direct lookup; withdrawal remains one click. Existing session/revision/expiry checks remain. The v2 notice invalidates v1 grants.

Each file operation asks again, before the browser sends any bytes. Agree continues the original operation; Disagree/Escape cancels it. Upload endpoints require a current purpose/version processing acknowledgement before handler extraction/storage. Normal authentication, CSRF, ownership and file validation remain. The new header is allowed only under the existing configured-origin CORS policy. Successful new writes record the notice identifier without file text. The header is a declaration, not proof of a human click; custom clients can supply it, and the framework may spool multipart bytes before rejecting a request. No device permission, whole-disk access or payment authority is granted.

Deployment: source and local acceptance complete; live release receipt is recorded below after deployment.

## Actual validation

| Check | Result | Evidence |
|---|---|---|
| Baseline backend | 184 passed, 337.69s | binary-consent-baseline.xml |
| Targeted privacy + Gemini | 55 passed, 33.00s | binary-consent-targeted.xml / .txt |
| Intermediate complete backend | 193 passed, 159.17s | binary-consent-full-backend.xml / .txt |
| Privacy + CORS after final header change | 30 passed, 36.33s | binary-consent-cors-targeted.xml / .txt |
| Final complete backend | 194 passed, 130.90s | binary-consent-final-backend.xml / .txt |
| Standalone production browser suite | 30 passed, no failures/flaky/skipped, 2.5m | binary-consent-browser-production.json / .txt |
| Lint / TypeScript / standalone webpack build | exit 0 each | binary-consent-lint.txt / -typescript.txt / -build.txt |
| Actual local C+D HTTP acceptance | 7 groups PASS | binary-consent-insurance-local.json |
| Exact configured-secret scan of browser bundles | 55 files, no matches | binary-consent-bundle-scan.json |

Evidence paths above are under `submission/evidence/`. Two development-operator browser cases were explicitly excluded from the production suite; operator endpoints remain covered by backend tests. Separate isolated `_test` databases were used for pytest and browser/HTTP acceptance; no user database was cleared. The single backend warning is the existing Starlette/httpx TestClient deprecation. No new migration is required.

Initial lint/TypeScript issues from the dialog trigger were corrected. The first targeted browser run had 8 passes and one test assertion against text inside a collapsed details element; the test now opens it, and the complete final run passes all 30. One early targeted pytest invocation was stopped when it overlapped the baseline test database; only completed subsequent runs count. Initial browser evidence is retained with `-initial` names.

Gemini is mocked in automated tests; this change performs zero real model calls and moves no real funds. The earlier online provider TIMEOUT remains a separate known limitation; this UX release does not claim to fix Google availability. See the previous release evidence below for that failed provider check. There is still no full account erasure/automatic retention or independent legal/privacy certification.

Commands from the backend directory: `.venv/Scripts/python.exe -m pytest -q`; Unix equivalent `.venv/bin/python -m pytest -q`. From frontend: `npm run lint`, `npx tsc --noEmit`, `npm run build -- --webpack`. Browser PowerShell: `$env:PLAYWRIGHT_BASE_URL='http://localhost:3104'; npx playwright test --grep-invert 'human consent, asynchronous|failure has no receipt' --reporter=list,json`. Unix: `PLAYWRIGHT_BASE_URL=http://localhost:3104 npx playwright test --grep-invert 'human consent, asynchronous|failure has no receipt' --reporter=list,json`. Browser fixtures must inherit the same isolated DATABASE_URL as the QA API.

Research/limits: `docs/21_PRIVACY_PERMISSIONS_RESEARCH.md`. Short user test instructions: `PRIVACY_GUIDE.md`. Updated API extension: `contracts/privacy.openapi.json` (8 paths, 8 schema definitions). Earlier release descriptions below are historical; their checkbox/scopes UX is superseded.

---

# Latest update: optional-AI privacy and keyboard — 19 October 2026

This section supersedes older Gemini outbound-data defaults below. Implementation and local/online privacy verification are complete.

## Verified online release

Render reports **Deploy succeeded | Live** for application commit **263bbe40b44b831050cc52f6fbfd5b75bf9ae471**, deploy `dep-dbasdr67bikc73apkfq0` (started 19 October 2026, 14:29:49 GMT+7; duration 2m27s). The actual HTTPS health endpoint independently confirmed that exact commit and real payments disabled. The prior feature commit 77c64f5 also deployed successfully; the final commit additionally makes new policy-source documents private by default.

- https://ai4s-demo.onrender.com/copilot — Enter/Shift+Enter, direct lookup by default, optional permission dialog, preview and withdrawal.
- https://ai4s-demo.onrender.com/privacy — notice available before sign-in.
- Final online privacy HTTP acceptance: **7 groups passed**, 9.641 seconds. This covers Secure/HttpOnly/SameSite cookies, CSRF rejection, default denial, scope restriction, sensitive-content tripwire, private-source/history filtering, withdrawal, login isolation, all-device logout and unused device/security headers.
- Final online insurance/sandbox HTTP regression: **7 groups passed**, 15.328 seconds, original/attachment hashes and signed simulated receipt verified; no real money.
- **External provider limitation:** the final explicit real-Gemini request returned TIMEOUT and the application correctly fell back to direct lookup. That strict provider-success check is recorded as FAIL in `privacy-render-provider-timeout.json`; it is not included among the passing privacy groups. An earlier local real answer succeeded, but current provider availability is not guaranteed. The configured timeout was not increased and no failure was disguised as generated AI text.
- The live browser showed direct lookup selected, Gemini disabled before permission, all permission/confirmation boxes unchecked and private-data scopes disabled in DEMO_ONLY. The notice opened at its heading and was cancelled without granting access. Screenshots: `screenshots/privacy/permission-live.jpg` and `screenshots/privacy/render-live.jpg` under `submission/evidence/`.
- Exact-secret checks passed for 55 generated browser JS files, 93 initial staged blobs and 30 final-fix staged blobs. Hosting secrets/DB records were preserved. No rate guard was reset, and no production operator feature was enabled.

The final report/evidence-only Git commit uses `[skip render]` to avoid rebuilding identical application code. The running application release therefore intentionally identifies 263bbe4; subsequent main-branch changes contain handoff records only.

## Delivered behaviour

- Enter sends; Shift+Enter inserts a newline. IME composition does not submit, and an in-flight guard prevents duplicate Enter/click requests.
- Direct lookup is selected on page load. Gemini requires explicit session permission. Supplementary scopes and confirmations start unchecked; refusal does not disable internal OCR, retrieval, budgets or payment workflows.
- Server-side grants require a matching revision, notice version and data mode, expire after at most one hour and require valid authentication. New demo tokens have a nonce; legacy shared tokens cannot grant AI permission. Old UI code cannot approve an unseen new notice.
- New policy-source uploads default to private USER_PROVIDED, and opening a new policy form resets that choice. Sample provenance requires a deliberate choice.
- History, document excerpts, finance/invoices and reviewed-policy summaries are separate optional groups. Unpaid DEMO_ONLY blocks the last two and filters personal documents before retrieval. Claim records, attachments, medical descriptions and original bytes are excluded from model evidence.
- A local preview shows eligible context without calling Google. Recognisable sensitive identifiers/secrets trigger rejection before dispatch. Revocation/logout stops future sends; it cannot recall in-flight processing or copies already held by Google. Local lookup replies are not silently forwarded as Gemini history.
- Public `/privacy`, selected-file/server-processing explanations, disabled unused device permissions, audit metadata without chat text, and all-device logout for personal accounts.

Competition tier mapping, primary research and limitations: `docs/21_PRIVACY_PERMISSIONS_RESEARCH.md`. Vietnamese walkthrough: `PRIVACY_GUIDE.md`. API extension: `contracts/privacy.openapi.json`.

The published contest allocates 30% to security/compliance and requests permission tiers and known risks. These controls are **not legal-compliance certification**. Full account/backup erasure, automatic retention cleanup, formal legal/transfer assessment and operator privacy-contact procedures remain unfinished. Labels and anonymity attestations are user declarations, not verification. Real-data deployment needs the team's operational/legal review; unpaid Gemini receives only non-personal sample/public/anonymised content.

## Actual verification

| Check | Result |
|---|---|
| Isolated baseline from HEAD | 164 passed after supplying matching OCR assets/test DB |
| Final backend suite | **184 passed**, 0 failures/errors/skips, 48.60 seconds; one existing Starlette/httpx deprecation warning |
| Intermediate targeted backend suite | 70 passed; the final full suite includes the two later backend boundary cases |
| Development browser regression | 29 passed in 116.779 seconds, includes the two development operator UI flows |
| Earlier focused chat browser suite | 7 passed in 13.507 seconds |
| **Final standalone production browser suite** | **29 passed** in 249.828 seconds, 0 unexpected/skipped/flaky; includes eight chat/privacy cases |
| Lint / TypeScript / standalone Webpack build | all exit 0 |
| Alembic check/migration | no pending model/schema operations; c41a15fa8b20 applied to local app DB without deleting existing data |
| Final actual-HTTP privacy acceptance | **7 groups passed**, no model request; cookie/CSRF, preview/filtering, revoke, login isolation, logout-all and security headers |
| Actual-HTTP insurance regression | **7 groups passed**, original/attachment hashes and signed sandbox receipt checked; no real money |
| Provider availability | an earlier synthetic-data answer succeeded; two later local attempts fell back, the instrumented retry reporting **TIMEOUT** at the existing 25-second limit. These attempts are not counted as successful model replies; see privacy-provider-*.json |
| Secret scanning | 55 browser JS files and 357 source/evidence files, no exact configured-secret matches; final staged scan follows before publication |

Production intentionally excludes `human consent, asynchronous` and `failure has no receipt`, the two development-only operator UI cases. They passed in the development suite; production operator access was not enabled. Test DBs end `_test`. No registration/Gemini rate guard was reset or weakened. Accounts/files in QA are fictional or self-authored.

QA setup corrections: explicit PostgreSQL port 5434 was required; the isolated baseline needed matching migrations/OCR assets and its own DB; browser fixture helpers initially inherited the default DB and were then pointed at the same isolated DB as the API. Final runs above passed after correction. Mobile visual review also corrected checkbox alignment and opening focus so the notice starts at its heading.

## Reproduce

Windows PowerShell, repository root:

```powershell
& backend/.venv/Scripts/python.exe -m pytest backend/tests -q
cd frontend
npm run lint
npx tsc --noEmit
$env:PLAYWRIGHT_BASE_URL='http://localhost:3104'
# Set DATABASE_URL to the same isolated _test DB as the QA API; fixture helpers inherit it.
npx playwright test --grep-invert 'human consent, asynchronous|failure has no receipt'
```

Unix equivalents:

```sh
backend/.venv/bin/python -m pytest backend/tests -q
(cd frontend && npm run lint && npx tsc --noEmit)
(cd frontend && PLAYWRIGHT_BASE_URL=http://localhost:3104 npx playwright test --grep-invert 'human consent, asynchronous|failure has no receipt')
```

The tested standalone build used BUILD_STANDALONE=true, API_PROXY_TARGET=http://127.0.0.1:8103 and static files copied into its output, served on 3104. The API allowed those explicit test origins. Existing local secrets/configuration/data were retained.

Actual HTTP check (Windows `python` or Unix virtualenv Python):

```sh
python scripts/check_privacy_live.py --url http://localhost:3104 --evidence submission/evidence/privacy-production-http.json
```

Add `--with-gemini` for at most one synthetic-data provider request; it may honestly fail on timeout/quota. Online verification uses the same checker against the Render URL and an exact expected release SHA.

Evidence: `submission/evidence/privacy-*` and `submission/evidence/screenshots/privacy/`. The report sections below describe historical releases.

---

# Combined Topic C + D — 19 October 2026

Implemented and exercised a working insurance-to-student-finance journey. Research, sources and the distinction between competition requirements and design decisions are recorded in `docs/20_TOPIC_C_D_RESEARCH_AND_IMPLEMENTATION.md`. The official entry still selects one topic; the product combines their tasks.

## Delivered behavior

- `/insurance`: a private reviewed portfolio tied to original documents and page excerpts; edit, archive and restore; explicit unknown fields rather than invented benefit values. Excerpt presence is checked, while interpretation remains the human reviewer's responsibility.
- Coverage comparison for outpatient, inpatient, accident and evacuation needs: single-policy limits, full period, territory, currency and waiting period; explicit unknown information and possible overlap. Limits are never added and results do not establish claim eligibility.
- Premium-to-budget bridge: a native-currency planned expense, unchanged current balance and existing cash-flow forecast. One linked CNY internal estimate can enter the existing dated-reference FX, exact consent, asynchronous signed sandbox, receipt and evidence flow. Repeated paths reuse the expense; financial snapshots are preserved and changes are flagged for review. These are user-created estimates, not insurer-issued invoices or premium settlement.
- Claim preparation: source snapshot at creation, incident/expense/deadline fields, case-specific checklist, private bounded original attachments, corrections/removal, explicit readiness review, user-reported external submission and closure. Export includes the checklist, policy original, attachment hashes and journal; exports serialize against concurrent edits. No insurer API submission or adjudication occurs.
- On-open expiry/premium/deadline reminders, a dated self-authored test pack, a Vietnamese A-Z walkthrough, three interface languages and light/dark layouts. Dashboard, Test Lab and copilot link to the combined journey.
- Read-only assistant integration: bounded reviewed policy facts and self-reported case status, with owned citations/navigation. Claim attachment bytes and case medical descriptions are excluded from Gemini. Direct lookup remains available without an AI key.

## Executed verification

| Check | Actual result |
|---|---|
| Baseline backend before changes | 138 passed |
| Final full backend | 164 passed, 0 failures/errors/skips; one existing Starlette TestClient/httpx deprecation warning |
| Full native development browser suite | 26 passed; 0 unexpected, skipped or flaky |
| Final standalone production browser suite | 24 passed; 0 unexpected, skipped or flaky. Two development-only manual operator cases were deliberately excluded |
| Frontend lint / TypeScript / standalone Webpack build | All exit 0; final source fingerprint and browser-JS secret scan in `insurance-build-checks.json` |
| Actual local HTTP C+D acceptance | Seven groups passed, including source/citation hash, one 800 CNY premium plan, 1,000 CNY current / 200 CNY projected balance, signed sandbox receipt and claim ZIP originals |
| Actual Gemini HTTP acceptance | Seven groups passed, including one real gemini-3.8-flash reply over the synthetic portfolio/case; no real money moved |
| Schema and handoff | Alembic current/check passed; fresh QA databases migrated and seeded without resetting old data; original handoff validator and source-secret scan passed |

Exact counts/durations and executed output are saved in `submission/evidence/insurance-validation.json`, `insurance-full-backend.xml`, `insurance-browser-development.json`, `insurance-browser-production.json`, the matching text outputs, `insurance-production-http.json` and `insurance-gemini-live.json`. New desktop/mobile screenshots are under `submission/evidence/screenshots/insurance/` and were visually inspected. Local Docker execution is not claimed.

QA corrected repeated template-file loading, inaccessible exact select labels and asynchronous checkbox display. Production testing then exposed a fast-input race while the source upload was still busy; file selectors now wait for that operation. An intermediate batch hit the persistent signup throttle after repeated runs. The final runs used fresh isolated QA databases; no security rate limit or existing account data was reset.

## Deployment and remaining boundaries

**Verified live on Render on 19 October 2026, 13:14 GMT+7:** https://ai4s-demo.onrender.com/insurance . The running release is `e54b9368f6bf754297fe8c028a5fa565a5d7687a`; Render deploy `dep-dbar9egm7kps739vruk0` reports **Live**. The complete authenticated HTTPS C+D acceptance passed all seven groups in **19.219 seconds**, including an actual **gemini-3.8-flash** reply, signed applied sandbox event, unchanged declared balance and byte/hash-checked claim export. Only self-authored test data was uploaded. See `insurance-render-live.json`, `insurance-deployment-receipt.json` and the Render Live screenshot. This also exercises the Linux Docker deployment; local Docker execution is still not claimed.

The dashboard had not started a new deployment after the feature push, so I invoked **Deploy latest commit**. The Settings UI subsequently showed **On Commit** selected, which I preserved, and the Blueprint now uses the matching `commit` trigger. I imported only the three Gemini settings into the service's private environment using the user's existing supplied key and rebuilt/deployed. Existing database/session/provider/operator configuration was preserved; no paid resource or database reset was introduced. No key was put in Git or browser assets. The temporary import file was removed locally afterward.

A documentation/evidence-only follow-up uses `[skip render]` to avoid rebuilding the same application solely to add its post-deployment evidence. The actual application code and health marker remain the verified feature release above.

Still not developed: live CNY/VND exchange or transfers; insurance purchase/activation; insurer contract or medical-document authenticity verification; insurer claims submission, eligibility decisions or payouts; background email/SMS; intraday FX monitoring. Coverage comparison does not model annual benefit consumption, full policy conditions, every exclusion or coordination between policies. The claim checklist is a referenced general preparation guide, not definitive insurer requirements.

The public demo uses bounded free hosting/database resources and synthetic/anonymized inputs. Gemini must be configured separately on each server and can fall back on provider errors. The supplied local key is not copied into Git or browser assets. No paid resource, competition registration, presentation submission or third-party message was created. `TOPIC_C_D_GUIDE.md` explains the usable flow; English technical/security/demo artifacts and the API contract were updated for team handoff.

---

The sections below are dated historical implementation snapshots; their older counts and limitations do not override this current extension and its evidence.

# Optional Gemini chatbot — 2026-10-19

Integrated the user's Gemini project through a backend-only HTTPX adapter and the existing authenticated study-abroad assistant. Local `.env` holds the key; it is never returned in status, model context, browser requests, source files or handoff artifacts. Direct lookup remains usable without a key. No dependency additions or database migrations were required.

The chatbot supports recent conversation (three preceding turns), Vietnamese/English/Chinese output, owned budget/invoice/reference-rate evidence and original policy excerpts with server-owned citation IDs/links. Original file bytes, account credentials and beneficiary details are not selected for model context. The UI discloses Google processing, offers local lookup, labels generated versus fallback answers, and distinguishes test documents. Provider timeout/auth/quota/invalid output produce an explicitly labelled local fallback. Application throttling can return 429. Financial action requests use the read-only guard; no tools, arbitrary model URLs or financial mutations are available.

Model discovery succeeded. `gemini-2.5-flash` returned 404 for this project; current Google documentation describes restricted access for new projects. **gemini-3.8-flash generated real responses successfully**, including schema-validated answers. This does not establish free/unlimited quota or payment-provider integration. Sources and configuration are documented in GEMINI_GUIDE.md and contracts/assistant.openapi.yaml.

## Executed validation

- Baseline backend: **110 passed / 2 failed**, 53.18 seconds. The existing finance fixture used Vietnam's local date for a provider observation checked against UTC; before UTC midnight it supplied a future date. Corrected the fixture to UTC, retaining the application's future-rate rejection.
- Final full backend: **138 passed**, one existing Starlette TestClient/httpx deprecation warning; **59.635 seconds**. Tests force Gemini off and mock provider calls; they do not consume the supplied key's quota. New coverage includes ownership isolation, bounded history, original excerpts, follow-up retrieval, source-ID validation, request limits, safe errors, key/header handling and zero financial writes.
- Final full browser suite on an isolated native development stack: **24 passed**, zero unexpected/skipped/flaky; **182024.205 ms**. Gemini browser interaction cases use mocked provider responses. The final source-label UI refinement was separately rechecked: **3 passed**, **5769.362 ms**.
- Real HTTP acceptance: **6 check groups passed**, **3 actual Gemini replies**, **21.766 seconds**. A self-authored private QA account's budget projected -200.00 CNY, follow-up answers retained context, policy answers cited original page-one excerpts, and payment/ledger state remained unchanged.
- Actual browser acceptance additionally received a real Gemini answer, verified the privacy disclosure and absence of a key in the browser payload, captured desktop/mobile-dark screenshots, and observed zero page errors and no horizontal overflow.
- Final frontend lint, TypeScript and standalone Webpack production build: exit 0. The build input matches current frontend source; evidence and digest are recorded in gemini-checks.json / gemini-frontend-build.txt. No Docker/Render build of this change is claimed.

An intermediate browser run was 23 passed / 1 failed because a terminal payment snapshot reloaded before a queued duplicate webhook was applied. The test now waits for the authenticated provider-event log before refreshing; its focused recheck and full isolated rerun passed. A second main-instance run was 21 passed / 3 failed when repeated registrations reached the existing 15-minute signup limit (429). Limits and production data were not bypassed or reset; the final run used the separate existing QA database/configuration. An initial command-line output capture also hit Windows text encoding after a successful model reply; the persisted UTF-8 live evidence supersedes that capture failure.

## Delivery and remaining limits

Local integration is configured and running. GitHub delivery includes code, docs, reproducible checks and secret-free evidence. Render still needs a server-side `GEMINI_API_KEY`, `GEMINI_ENABLED=true`, model configuration and Manual Deploy; no key or environment update is published through Git. The supplied key appeared in chat, so the handoff guide recommends replacing it before sharing the hosted demo.

Chat history is not persisted by this application; Google applies its separate processing terms. Unpaid Gemini should use anonymized/self-authored data. Retrieval is bounded keyword/synonym search, not embeddings or exhaustive document reasoning. Valid source IDs do not prove every generated statement is correct. No streaming, autonomous financial actions, bank integration or actual insurance activation was added.

Evidence: gemini-backend-tests.txt / gemini-backend-junit.xml; gemini-browser-isolated.json / .txt; gemini-browser-targeted-final.json; gemini-live-http.json; gemini-live-ui.json; screenshots/gemini/; gemini-checks.json. Earlier runs and deployment records below retain their original scope.

---

# Theme button correction — 2026-10-19

Replaced the theme dropdown with one sun/moon icon button, before and after sign-in. Clicking switches directly between light and dark based on the resolved current appearance. The button exposes its dark-mode state to assistive technology and has a localized action tooltip. Saved choices, cross-tab synchronization and default device following remain supported. Updated the usage docs and existing preferences tests for the button.

Validation: **6 focused browser tests passed**, zero unexpected/skipped/flaky, **18999.467 ms** (theme-button-browser.json); lint and TypeScript exit 0. No production rebuild/deployment or full payment regression rerun was needed for this UI-only correction; the production evidence below describes the preceding version.

---

# Interface languages and appearance — 2026-10-19

Completed Vietnamese, English and Simplified Chinese interface controls before and after sign-in. Local dictionaries cover navigation, forms, guided tasks, invoice/checkout/status/receipt labels, budgeting, document search, test lab and operator screens. Number/date presentation follows the selected locale; monetary values remain exact server Decimal strings, with BigInt used for grouped integer display. Vietnam remains the display time zone.

Light, dark and device-following themes now cover the application and mobile layouts. Device changes are observed while the page is open; an explicit selection overrides them. Preferences survive reload/navigation and synchronize across same-origin tabs. Blocked storage falls back to memory in the current tab; invalid saved values use Vietnamese/device settings. Language changes preserve form drafts and do not remount the page. Hydration starts with the same language as the server; saved preferences activate after hydration, and a small static head script applies the saved/device theme before paint.

Original user entries, uploaded content, citations and backend-generated account answers retain their source language. This is interface localization, not automatic document translation or a new multilingual LLM. Assistant questions remain supported in Vietnamese/English; Chinese interface selection does not add Chinese intent recognition. OCR language remains an independent input. The fixed simulated-payment warning is preserved in every language, and dark-mode receipts print on white with readable text.

Executed checks for this change:

- Lint and standalone Webpack build: exit 0; TypeScript: exit 0. The isolated build input matches current frontend source (digest in preferences-checks.json).
- Production browser regression: **19 passed**, zero unexpected/skipped/flaky, **79590.064 ms**. Two development-only operator UI cases are excluded because that panel is intentionally disabled in production.
- Dedicated production preferences run: **6 passed**, zero unexpected/skipped/flaky, **26615.032 ms**. These six also ran in the 19-case regression.
- Signed manual success, duplicate event and receipt: focused unchanged development recheck **1 passed in 7.9 seconds**. The manual failure/invalid-operator-code case passed in the development rerun.
- Actual browser screenshots and CSS assertions checked English light sign-in, Chinese dark invoice drafts, a 320-pixel layout, dark receipts and white-background printing with preserved warnings.
- An intermediate full development rerun was **18 passed / 3 failed**: one 5-second receipt navigation assertion during concurrent build (focused recheck passed), and two sign-ups rejected with HTTP 429 after repeated runs. The throttle remains intact; the isolated production regression used separate existing test data/configuration. An unfiltered production attempt was stopped because manual operator UI is deliberately unavailable there. Earlier new-test label/selector failures were corrected. No intermediate failure is counted as a pass.

Usage and reproducible Windows/Unix commands: LANGUAGE_AND_APPEARANCE.md. Current validation evidence is in submission/evidence/preferences-checks.json, preferences-visual-checks.json and browser-results.json; screenshots are under screenshots/preferences/. Backend Python, payment rules and API contracts were not changed; the backend suite was not rerun for this interface change. Historical backend results below retain their original dates.

GitHub main is the distribution source for this update. Render auto-deployment remains disabled: the online service requires Manual Deploy → Deploy latest commit after the push. Earlier Render acceptance below describes its earlier deployed commit and is not evidence that this interface update is already online.

---

# Render deployment verified — 2026-10-18

The user created the Free Blueprint in Render Dashboard. Service ai4s-demo is **Live** at https://ai4s-demo.onrender.com, runtime commit 3ac84b1c8f4f4c8db15afa55f8c16896cc7546d9. The single-image Linux Docker build and startup therefore ran on Render; this supersedes the earlier authentication-blocked preparation status below. No paid resource was selected.

**10 actual HTTPS acceptance checks passed**: private registration/session, downloadable inputs, real invoice OCR plus human review, saved source, budget projection, cited text policy, actual reference FX, consent-bound signed automatic outcomes, separate ledger accounting, owner case export, decline/retry and logout revocation. Check groups are recorded exactly in submission/evidence/render-live-http.json. The public sign-in UI was also opened and captured; the full browser interaction suite has not been rerun against Render.

The additional original BFSU scanned table returned **HTTP 422 OCR_TIMEOUT** under the existing 75-second bound on Free hosting. Secure cookie verification passed before that upload, but page-search and byte-download assertions were not reached on this cloud attempt. Earlier native tests of the same PDF passed; that does not establish sufficient Free CPU for this document. Use clear invoice images and text-based policy PDFs for the initial cloud journey. The failure is recorded in render-public-reference.json; no paid upgrade or timeout bypass was performed.

Current deployment evidence: cloud-readiness.json, render-live-http.json, render-public-reference.json and screenshots/cloud/signin.png. All payments remain simulated. Free service sleep/quota and 30-day database expiry still apply. Historical preparation and native results follow.

---

# Cloud deployment preparation — 2026-10-18

The user selected a fixed online demo independent of the local computer, has no hosting account yet, and chose Free hosting with idle sleep/database limits. Added a Render Deploy button, root render.yaml, a single-origin multi-stage cloud Dockerfile, standalone frontend output gated by BUILD_STANDALONE, bounded cloud OCR concurrency, and a supervisor for non-resetting migrations/readiness/owned-process shutdown. DEPLOY_RENDER.md explains account setup, actual resource/URL selection, secrets, quotas, recovery and manual deployments.

## Executed checks

- Official Render JSON Schema (2020-12): valid; one Free web service, one Free PostgreSQL, no external DB IP access in the configuration.
- Full backend: **112 passed in 254.25 seconds**, one existing upstream deprecation warning; Alembic detects no new upgrade operations.
- Cloud startup configuration guards: **9 unittest cases passed**, including explicit PostgreSQL/psycopg conversion, HTTPS/origin/cookies, secret placeholders, port collisions and no-live-money enforcement.
- Frontend lint: exit 0. Webpack standalone build: exit 0, TypeScript/static generation/16 application routes completed.
- Actual isolated native cloud launcher: **11 HTTP checks passed**, including the original BFSU PDF OCR, signed sandbox success/decline, separate ledger confirmation and case export. Runtime used one OCR slot and Node heap 192 MB.
- Standalone production browser acceptance: **2 passed**, zero unexpected/skipped/flaky, **60,896.924 ms**. The prior full LAN browser suite remains 15 passed in browser-results.json.
- Direct-file launcher shutdown released isolated ports 3102/8102; the original app on port 3000 remained healthy. The initial PowerShell pipeline harness terminated its parent before cleanup; its verified owned children were stopped and the harness was corrected to direct-file invocation before this shutdown check.

## Deployment status and limits

**No public cloud deployment or paid resource has been created.** The newly available Render connection returned USER_NOT_LOGGED_IN; the user must create/sign in and connect the account (then choose the workspace), or use the reviewed Deploy button directly. This is an authentication dependency, not an unreported successful deployment. Docker is unavailable locally, so native standalone/supervisor checks do not certify Linux image execution or Free-plan capacity. Actual Render build/HTTPS acceptance remains pending.

The Free database expires after 30 days and the web service sleeps/has quotas. Slow CPU or 512 MB memory can still constrain dense OCR; no Free-tier load guarantee is claimed. No existing private database/documents are copied into the cloud. Current evidence: submission/evidence/cloud-readiness.json, cloud-native-http.json and cloud-native-browser.json. Earlier sections below are historical release records.

---

# Implementation report — A-Z acceptance and team handoff

## Current release 2026-10-18

The user requested the most realistic runnable MVP possible, including actual uploaded reference documents, a complete A-Z test journey and a team handoff grounded in the competition. Primary research is in docs/19_COMPETITION_HANDOFF_RESEARCH.md. No registration, submission, public deployment, payment-provider account or live transfer was invented.

### Delivered behavior

- /test-lab provides six guided steps, owner-derived progress, OCR/worker readiness, 15 downloadable self-authored inputs and original university-source links. Home and sidebar link to it.
- Users select SUCCESS or DECLINED before quote-bound consent. A persisted provider event becomes available after three seconds; only existing HMAC/timestamp/amount/state checks settle it. Changed method clears consent. Normal testing needs no operator code. Advanced MANUAL simulate/replay remains operator-only; a disabled worker rejects automatic methods before creating an intent.
- Documents declare USER_PROVIDED, PUBLIC_REFERENCE or TEST_FIXTURE. Public references require the original URL. These declarations do not certify the issuer or personal coverage.
- The original BFSU-published 2025 insurance PDF was downloaded and actually uploaded: 705,051 bytes, one scanned page, local OCR, page/source retrieval and byte-identical original download. Public originals retain publisher rights and are excluded from the source ZIP. team.py fetch-reference downloads from a fixed catalog.
- Owner case ZIPs contain the invoice original where present, SHA-256, server quote, consent, events/audit, eligible simulated receipt and linked plan/ledger snapshot. Authentication secrets are excluded; users are told the ZIP may contain private source data.
- scripts/team.py implements non-resetting setup, diagnostics, foreground two-service start, reference download and secret-free source packaging with checksums. Optional full-stack Dockerfiles/Compose are supplied. TEAM_HANDOFF.md, ACCEPTANCE_TESTS.md and English technical/security/demo documents reflect the release.

### Executed verification

| Check | Actual result |
|---|---|
| Backend baseline | 101 passed in 63.61 seconds |
| Final full backend suite | **111 passed in 115.58 seconds**, one existing Starlette/httpx warning |
| Targeted A-Z browser rerun | **2 passed in 33.0 seconds** |
| Final full browser suite through LAN | **15 passed**, 0 unexpected/skipped/flaky; **271,092.295 ms** |
| Frontend lint and optimized build | Exit 0; clean extracted production Webpack compilation succeeded (91s compile), TypeScript and 16 application routes plus not-found completed |
| Actual HTTP acceptance with original public PDF | **11 checks passed**; evidence/acceptance-live.json |
| API/schema | 18 ORM tables, **50 paths**; additive revisions 20261018_self_service and 20261018_document_kind |
| Current-host helper checks | doctor, setup --skip-install --database existing, fetch-reference and package exercised |
| Recordings | Passing A-Z and decline/retry browser QA clips generated; no operator code shown |

A clean installation exposed the default Next proxy timeout on a dense scanned PDF; it now allows 120 seconds around a bounded 75-second OCR process. One public-PDF attempt under concurrent test load reached the explicit OCR timeout; the separate repeat passed. This is not a load-test certification. Cold development route compilation also required longer navigation waits; production startup precompiles the UI. Initial new browser checks exposed test-harness problems: duplicate wallet heading matches, a URL wait matching /invoices/new before save completed, and an exact receipt locator including a nested warning. Selectors/waits were corrected; the final full suite passed. Synthetic inputs do not establish accuracy on all real invoices.

### Handoff verification and boundaries

A fresh source archive was extracted into an isolated directory and installed with new secrets, a new virtual environment, npm ci, downloaded OCR models, migrations and a separate empty PostgreSQL database. The extracted application compiled with Webpack, ran on ports 3101/8101, passed 10 doctor checks, both production browser acceptance journeys and 11 actual HTTP checks including the original BFSU PDF. Final runtime/config files were compared with this tested copy. Detailed evidence is in submission/evidence/handoff-validation.json and acceptance-clean-install.json. The source bundle contains lockfiles, migrations, self-authored inputs, catalog, guides and credential-free evidence. The final full LAN browser rerun again passed all 15 cases with no failures/skips/flaky results. ZIP CRC, manifest hashes and exclusion/secret scans are verified; the archive SHA-256 is saved in its adjacent sidecar. Local .env, accounts/DB, venv/node_modules, failed traces, downloaded public originals and local model caches are excluded; recipients recreate these intentionally.

No generative LLM, semantic embeddings, bank synchronization, custody, insurer activation, production FX quote or actual payment provider was added. OCR is a real model; forecasting, parsers and copilot routing remain rules/calculations. Sandbox success never automatically posts actual ledger spending. Privacy/retention, HTTPS/email recovery/MFA, load and independent security-review gaps remain documented. Docker/Unix must not be described as executed without evidence.

Older sections below are historical release records; their counts and operator-dependent normal flow are superseded by this section.

---

# Implementation report — MVP upgrade

## Financial-participant implementation — 2026-10-18

The user clarified that the supplied screenshot analyses the competition problem and asked for implementation along that analysis, using callable APIs where useful. Delivered the document → reviewed invoice → multi-currency plan → cash-flow/FX assessment → separately authorized action journey. The formal submission topic was not selected or registered by this work. Scope mapping and architecture are in `docs/17_CHALLENGE_IMPLEMENTATION.md`; user instructions are in `STUDENT_FINANCE_GUIDE.md`.

### Delivered and running

| Area | Concrete behavior |
|---|---|
| Local invoice OCR | PNG/JPG/WebP, scanned/text PDF, TXT/MD; actual Tesseract.js neural recognition, optional English/Vietnamese/Chinese language selection, labelled field suggestions with page/source-line evidence, mandatory owner review before save, retained original download; no automatic invoice/payment creation |
| Multi-currency ledger | Owner-scoped CNY/VND sổ tiền, declared opening balance/date, actual income/expense posting, idempotent retries/request conflict detection, void audit trail and CSV export |
| Scheduled cash flow | One-off/monthly plans, month-end clamping, explicit invoice-to-plan snapshots, 30/60/90-day per-currency graphs, shortfall and overdue messages; confirmed actual entries do not double-count in projection |
| FX awareness | Actual Frankfurter reference/history calls and cache, source/date/stale metadata, amount/budget scenarios at reference and ±5%, budget exceedance and calculation threshold; native projections remain available during an FX outage |
| Student copilot | Reads owned budgets/invoices/reference data and uploaded policy excerpts, returns citations and task links, handles missing evidence; payment intents return guidance without creating or confirming anything |
| Policy grounding | OCR for image/scanned policies, language selection, retained private source/text, CJK/two-character and Vietnamese/English synonym matching, page citations; original text-policy flows still work |
| UX | Three new pages `/copilot`, `/finance`, `/rates`; updated navigation/context help, source-review form, invoice budget action and data-derived next-step cards on home |

No live funds/custody, bank account integration, insurer activation, realtime market feed, statistical forecasting, semantic embedding model or generative LLM/RAG was silently substituted. The OCR is an actual model; assistant routing/field parsing/forecasting are explicit grounded rules/calculations. All financial mutations remain separate user actions. Existing signed sandbox events and consent invariants are preserved.

### Executed verification

| Command / check | Actual result |
|---|---|
| Backend baseline before changes | 76 passed in 39.83s |
| Final `pytest -q --junitxml=../submission/evidence/backend-junit.xml` | **101 passed in 66.13s**, one pre-existing Starlette/httpx deprecation warning |
| Full browser suite through `http://192.168.1.14:3000` | **13 passed in 1.7 minutes**; original flows plus OCR, ledger/forecast and copilot |
| Three new browser workflows rerun after language-selector changes, list reporter | **3 passed in 23.3s** |
| Final frontend lint and optimized build | Exit 0, no lint warnings; TypeScript and all 15 application routes plus not-found completed |
| `alembic upgrade head` / `alembic check` | Static revision `9f40f776cbf8` applied; no pending upgrade operations; 18 ORM tables; existing records preserved |
| Contract | `contracts/openapi-mvp.json` regenerated with 45 paths, including reviewed imports, finance and bounded assistant routes |
| Actual HTTP via frontend LAN proxy | **8 checks passed**: real Chinese OCR/review/original bytes; native shortfall; idempotent confirmation/no double count; void; actual FX/history; scanned-policy citations; no payment side effect; logout revocation |
| Local multilingual OCR smoke | Five exact fields matched on each of three self-authored clean printed samples: English 0.67s, Vietnamese 0.75s, Chinese 1.05s; not a production accuracy estimate |
| Dependencies | 48 installed Python distribution records / 455 npm package entries inventoried. Runtime npm audit 0 findings; full audit retains 5 existing high development-chain findings |

Fixed issues found during verification: unsupported PDFium page context management in scanned PDFs, label/selector ambiguity in forms, and OCR-inserted Chinese/date whitespace plus mixed-language extraction quality. Added explicit OCR language selection and reran the relevant tests. OCR field smoke was initially 5/5 English, 1/5 Vietnamese, 0/5 Chinese before those refinements; final measured results above use the main language and appropriate installed test fonts. Real photos/layouts still require review.

### Evidence, setup and current limits

- `submission/evidence/student-finance-live-http.json`: credential-free actual HTTP results and public reference data.
- `submission/evidence/local-ocr-smoke.json`, `ocr-model-manifest.json`: exact small smoke-set outcomes and pinned language source/hash metadata.
- `submission/evidence/browser-results.json`, `backend-junit.xml`: full-suite structured results. Failed traces remain ignored and are not handoff artifacts.
- `submission/evidence/screenshots/student-finance/`: reviewed OCR, shortfall, FX scenarios and mobile cited copilot screenshots. Original UX screenshots remain under screenshots/ux.
- `STUDENT_FINANCE_GUIDE.md`, `RUNBOOK.md`: runnable Windows/Unix setup and usage; English technical/security submissions were updated.

OCR runs locally through Node/Tesseract.js with Pillow/PDFium preprocessing. After `npm ci` and backend dependency installation, run `python scripts/setup_ocr.py` once to download three public language packs pinned to `87416418657359cb625c412a48b6e1d6d41c29bd`. Runtime processing does not transmit private input to an OCR service. The API host needs Node.js and installed frontend Node packages. Maximum OCR scans: 5 MB / 5 pages / 16-megapixel image, two workers, 75-second timeout; normal text policies retain the 50-page cap. Original invoice imports have a 100-source account limit and do not yet have a user-facing retention/deletion workflow.

Ledger data is declared, not bank verified. Plans are snapshots; projections depend on the entered schedule and show end-of-day results. No automatic invoice/sandbox deduction, cross-wallet exchange or bank reconciliation is claimed. The current free FX feed is dated reference data, with no provider execution/fees assumed. Localhost and current LAN sharing remain available; no public deployment, firewall changes, real payments or second physical-device test were performed.

## Usability redesign — 2026-10-18

The user reported difficulty understanding the interface and requested comparable-system research plus an implemented redesign. Reviewed public first-party flows/documentation for Flywire, Convera GlobalPay for Students, Wise and SafetyWing. Evidence, URLs, observed patterns and the distinction between observation and design inference are recorded in `docs/15_UX_RESEARCH_AND_REDESIGN.md`.

Delivered a task-focused home page with separate fee-conversion and insurance-document entries, preparation instructions, a first-use help modal remembered per account/browser, skip/close/Escape and a persistent contextual help trigger. Invoice/detail/quote/tracking pages now show numbered progress; form groups explain required vs optional information. Inline help explains issuer/recipient, quote-only behavior, search input, empty history and pending sandbox status. Operator navigation moved to a secondary section. Mobile navigation retains readable labels. Payment consent and provider verification remain unchanged; no live transfer or insurance claims service was added.

Final verification on the running app at **http://192.168.1.14:3000**:

| Check | Actual result |
|---|---|
| Existing browser cases before redesign | 7 passed in 1.1 minutes |
| `pytest -q` | **76 passed in 36.77s**, one existing upstream Starlette deprecation warning |
| `npm run lint` | Exit 0, max warnings 0 |
| Final `npm run build` | Exit 0; optimized compilation, TypeScript and all routes completed |
| Full browser suite after redesign and focus fix | **10 passed in 50.3s**, through the LAN origin |
| Additional 320px phone check after adding mobile navigation labels | **1 passed in 4.0s**, covering focus wrap, Escape, dismissal persistence, reopening and overflow |

The first complete UX run had 9 passes and one failure: Tab could leave the modal's DOM focus loop at the final control. Added explicit forward/backward focus wrapping; the focused case and full suite then passed. A prior LAN attempt was interrupted after the router assigned a new IP and Next development-origin configuration needed a restart; both servers were restarted with the exact new allowlisted origin. Localhost and LAN proxied health returned HTTP 200. No firewall or Internet exposure changes were needed.

New cases verify guidance is shown by default, can be dismissed without repeating on reload, opens the right topic by route, links into both working tasks, explains form inputs and does not create a payment merely by viewing a quote. Existing account, document upload/search/download/delete, consent, success/failure/cancellation, duplicate-event and receipt cases also pass. Screenshots inspected include desktop welcome/dashboard/conversion and narrow mobile dashboard, saved under `submission/evidence/screenshots/ux/`; structured full-suite results remain in `submission/evidence/browser-results.json`.

The current Wi-Fi IP is **192.168.1.14**, replacing yesterday's 192.168.1.2. Updated `MVP_GUIDE.md` and `LAN_TEST_GUIDE.md`. This is functional/browser verification, not a measured usability study or confirmation from another physical device.

## LAN sharing update — 2026-10-17

User requested testing from other devices on the same Wi-Fi. The running frontend now listens on `0.0.0.0:3000`; share **http://192.168.1.2:3000**. API and PostgreSQL remain on loopback. Frontend API calls use a same-origin Next.js rewrite, with explicit LAN origin allowlisting in the backend and Next development server. Existing localhost access remains usable. No Internet tunnel or public deployment was created; existing Node.js firewall rules were sufficient without changes.

Actual LAN-origin browser testing exposed `crypto.randomUUID` being unavailable on an HTTP IP origin. Replaced its checkout uses with UUID v4 generation using cryptographic `getRandomValues`, preserving stable retry/idempotency behavior. First LAN browser run: 3 passed, 4 failed at quote creation. After the fix: **7 passed in 47.8 seconds**, including success/failure/duplicate/cancel, cookie login/reload, invoice estimates and private document upload/download. Backend baseline: **75 passed**; after explicit LAN-origin/CSRF regression coverage: **76 passed in 24.60 seconds**, one existing Starlette warning. Frontend lint and `tsc --noEmit` both passed after final edits.

Actual HTTP smoke through `http://192.168.1.2:3000` also passed account, invoice, reference FX, quote, document search/download/delete and logout. LAN and localhost proxied health both returned HTTP 200. These checks used this host's browser/network stack; router client isolation and a second physical device have not been tested. Keep this host awake and both services running. IP may change with DHCP; rerun `scripts/configure_lan.ps1` and restart both services when it changes. Windows/Unix commands and troubleshooting are in **LAN_TEST_GUIDE.md**.

Date: 2026-10-17, Vietnam. Local UI: http://localhost:3000 . API docs: http://127.0.0.1:8000/docs . User guide: MVP_GUIDE.md. Setup/replay: RUNBOOK.md. The prior P0 report is archived as IMPLEMENTATION_REPORT_P0.md; this file describes the current product.

## Current usable features

The user requested working MVP behavior with free APIs instead of a product made entirely of sample data. The user confirmed they have no payment-provider sandbox account. This iteration implements the features that can operate with actual user input and a verified public API; actual funds transfer remains explicitly unconnected.

| Area | Delivered behavior |
|---|---|
| Accounts | Email/password registration and login, private initially-empty workspace, Argon2id password hashes, 24-hour revocable HttpOnly cookie sessions, CSRF protection and origin checks, persistent login across reload, login/signup throttling, profile edit, password change/revoke-all and sign-out |
| Invoices | Owner-scoped create, detail, edit, search, status filter and archive; optional source URL/notes; Decimal CNY validation; duplicate invoice numbers blocked per owner; active/succeeded payment locks prevent changing financial input |
| Reference FX | Actual Frankfurter v2 CNY/VND integration, no API key, PostgreSQL observation cache, source/observation date/fetch timestamp, explicit stale-cache flag and maximum age; no made-up fallback on failure; history API also implemented |
| Quote estimates | Immutable server snapshots, daily reference conversion, explicit ROUND_HALF_UP, zero default application fees and no invented provider fee, expiry, refresh with consent reset; viewing a user invoice estimate does not create an order |
| Policy documents | Private PDF/TXT/MD upload, actual text extraction, original download, extracted-text reader, owner-scoped delete, duplicate detection and keyword/synonym search returning original excerpts with filename/page citations |
| History | Status and ID filters, CSV export, per-order timeline/JSON export and printable sandbox receipt |
| Payment sandbox | Existing verified provider abstraction, persisted asynchronous outbox, actual webhook route, HMAC verification, idempotency, concurrency locks and protected terminal transitions; explicit consent required to start a trial |
| UX | Separate sign-in/private workspace and optional sample-data account, responsive desktop/mobile forms, empty/loading/error states, data invalidation after mutations so cached pages refresh correctly |

Registered accounts receive no seeded invoices or fictional policy answers. Their invoices are USER_ENTERED, not claimed to be institution-verified. Original synthetic fixtures remain in the explicitly selected sandbox workspace. Frankfurter-backed calculations are `purpose=REFERENCE_ESTIMATE, is_simulated=false`; payment orders using those values remain `is_simulated=true` because execution is still sandbox. Receipts retain conspicuous no-real-funds text.

## Free API connected and verified

Official documentation: https://frankfurter.dev/ ; endpoint: https://api.frankfurter.dev/v2/rate/CNY/VND . A direct request returned HTTP 200 and CNY/VND **3864.07**, observation date **2026-10-16**. The actual running-app HTTP smoke also retrieved this reference observation and verified Decimal conversion. An 800 CNY QA invoice converted to **3,091,256 VND**, with zero configured application fees. This is a dated reference observation, not a current executable bank quote.

The backend caches observations for six hours; eligible cached data can be used during an upstream outage with `is_stale=true`. Observations older than seven days are rejected. No fallback to 3,500 or any other invented value is used for a user-entered invoice. Private user identity, invoices and document text are not sent upstream. Research and alternatives evaluated are recorded in docs/14_MVP_APIS_AND_PROVENANCE.md.

## Executed verification

| Command / check | Actual result |
|---|---|
| Baseline `pytest -q` before refactor | 42 passed |
| `alembic upgrade head` | Applied static revision `20261017_mvp` after `4ad8203419ab` to demo and separate test PostgreSQL DBs, preserving existing records |
| `pytest -q --junitxml=../submission/evidence/backend-junit.xml` | **75 passed**, one upstream Starlette/httpx deprecation warning |
| `alembic check` | `No new upgrade operations detected.` |
| `npm run lint` | Passed with max warnings 0 |
| `npm run build` | Passed optimized Next.js build and TypeScript; all 12 application routes plus not-found emitted |
| `npm run test:e2e` | **7 passed**: 4 payment regressions and 3 registered-account/invoice/document workflows |
| `python scripts/check_mvp_live.py` using backend venv | Actual HTTP registration/session, private invoice, Frankfurter quote, no order on quote-only, policy upload/cited search/download integrity/delete, invoice archive and session revocation passed |
| `python scripts/verify_source.py` | Checks deliverable text/evidence for accidental copies of local session/webhook/operator secrets |
| `python scripts/validate_handoff.py` using backend venv | Original contract/reference/fixture structure validated separately from application tests |

Backend tests use PostgreSQL `insurance_payment_test`, with destructive reset restricted to a database name ending `_test`. They include cookie attributes, login throttling, expiry, CSRF/origin rejection, password revocation, per-account invoice numbering/ownership, live-rate parsing with Decimal, cache behavior/outage/invalid upstream data, no invented fees, immutable quote snapshots, PDF extraction, encrypted/empty/invalid/oversized file rejection, document ownership and citations, plus the complete prior payment-adversarial suite.

Unit tests stub the upstream rate response for repeatability. `mvp-live-http.json` separately records the actual running integration. QA accounts/invoice/document input in evidence are self-authored test fixtures, not claims about actual insurance terms. No credentials are exported. Current API schema is exported to contracts/openapi-mvp.json; contracts/openapi.yaml remains the original draft supplied with the kit.

Verification found and fixed stale invoice display when navigating back to a previously cached Next.js page after editing. Shared data-version invalidation now refreshes detail/list/dashboard/history, and order status changes invalidate related views. Database dependencies use function scope so commits complete before sending a successful HTTP response. An intermediate browser run was also interrupted by development hot reload; final runs occur after edits stop. Passing current outputs supersede intermediate failures.

## Evidence and implementation artifacts

- submission/evidence/backend-tests.txt and backend-junit.xml: actual current pytest output.
- submission/evidence/frontend-lint.txt and frontend-build.txt: actual current lint/build output.
- submission/evidence/browser-tests.txt and browser-results.json: actual current browser runs.
- submission/evidence/mvp-live-http.json: actual HTTP smoke with external reference FX.
- submission/evidence/screenshots/mvp/: sign-in, empty private dashboard with reference FX, reference quote and mobile document citations, captured from the running app and visually inspected.
- submission/evidence/screenshots/: existing payment regression/receipt/print screenshots.
- submission/evidence/operations.json: original signed sandbox payment scenario replay.
- backend/requirements.lock.txt and frontend/package-lock.json: tested dependency resolutions.
- submission/evidence/dependency-licenses.json: 46 installed Python distributions and 442 npm package entries, metadata inventory rather than legal certification.
- submission/TECHNICAL_DOCUMENT.md and SECURITY_SELF_ASSESSMENT.md: current English architecture and security handoff. Historical P0 copies are clearly named with `_P0`.

## Practical limits

1. **Payment execution is not connected to a real provider.** The user has no sandbox merchant account. Credentials, beneficiary onboarding and an eligible Chinese insurance corridor must be supplied/verified before a real integration can be enabled. No Vietnamese domestic bank collection is presented as Chinese insurer settlement, and no real funds were moved.
2. Policy search is extractive keyword/synonym retrieval with original citations. It is not general LLM reasoning, translation, coverage adjudication or claims submission. Image-only PDFs need OCR before upload. File processing is bounded to 5 MB/50 pages/500,000 extracted characters; no antivirus/OCR service is integrated.
3. Email/password accounts work, but email delivery/verification, forgotten-password email recovery, MFA and an external identity provider are not implemented. No buttons claim these services are configured. Local sessions should use Secure cookies and HTTPS before any shared deployment.
4. User-entered invoice/beneficiary information is stored with provenance, not institution verification. Daily FX is for planning; provider exchange spread/fees are not known. No bank account, passport or card-data feature exists.
5. No public deployment was performed. PostgreSQL Windows-native startup, migrations and the application were exercised; Docker/Unix instructions remain unexecuted on this host. Local development DB credentials/privileges are unsuitable for shared hosting without hardening, backups and independent review.
6. Runtime npm audit previously reported 0 vulnerabilities; full npm audit has 5 high development-tool package-chain findings from the unpatched braces advisory (https://github.com/advisories/GHSA-vfj7-8cjw-p6xm). npm dependency versions did not change in this upgrade. A Python vulnerability audit was not run; no exhaustive security certification is claimed.

No third-party messages, public publishing, purchases, actual insurance activation, fabricated successful payment, competition registration, presentation deck or video were produced. MVP_GUIDE.md explains how to use the actual delivered product; RUNBOOK.md contains startup and reproducible test/capture commands.

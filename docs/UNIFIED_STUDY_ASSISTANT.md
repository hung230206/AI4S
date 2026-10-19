# One study-abroad assistant

The user no longer chooses between insurance RAG and Gemini. The current local UI has one floating assistant across authenticated pages; `/copilot` and `/knowledge` open that assistant through a compatibility redirect. Source citations are folded inside each answer. Published source pages remain at `/knowledge/{id}` so existing citations still work. Admin publication, drafts, upload consent and revision checks remain at `/admin/rag`. These local interface/routing corrections have not been committed or deployed. Earlier online validation below describes the deployed release.

## Request flow

Recognised app tasks now return a local, fixed navigation proposal before retrieval or generation. The UI asks Open page / Stay here and only an explicit confirmation changes the page. Successful-transaction requests open History with its success filter. Definition, evidence and how-to questions keep the conversation routes below. Existing workflow action buttons also ask confirmation when clicked. No financial action is performed by navigation. Details and reproducible tests: [ASSISTANT_NAVIGATION_LOCAL.md](ASSISTANT_NAVIGATION_LOCAL.md).

1. The UI sends the question to `POST /api/v1/study-assistant/chat`. There is no user-facing model/retrieval mode selector.
2. The server checks action requests first. Complete educational questions about known insurance concepts (for example, “bảo hiểm là gì”, “What is a deductible?” and “什么是保险？”) use general Gemini guidance. Basic definitions do not require policy evidence. Extra qualifiers about a personal policy, named product, country rules or legal entitlements keep the source-required route. Specific insurance, policy, benefit, claims, legal and document questions go through RAG using bounded multilingual intent rules. Eligible follow-ups preserve whether their preceding question was general or source-dependent, including consecutive follow-ups. History is used only when conversation sharing is permitted. This is a local rule-based router, not a trained intent model or a second Gemini classification call; unrecognised educational phrasing can still need refinement.
3. For RAG, retrieve up to three passages from permitted owned documents and the administrator-published shared library. Generic-word-only hits cannot substantiate an otherwise unknown subject. Drafts, withdrawn/deleted shared sources and other accounts' private files are excluded.
4. Gemini receives the question, permitted history and original passages. The source-only system instruction requires synthesis from that evidence, inline source markers and server-known source IDs. No evidence means an explicit insufficient-information answer, without asking Gemini to fill the gap from memory. Unsupported source IDs cause an honest extractive fallback.
5. Other study-abroad questions use general Gemini guidance, without unrelated library passages. Account-specific finance questions remain local unless the current server policy and consent permit financial context. Payment/execution requests receive a read-only workflow response and never execute model tools.
6. After an external call, both successful and fallback responses recheck session/consent and the retrieved documents. Withdrawn or changed sources suppress the stale answer and citations.

`POST /api/v1/study-assistant/preview` uses the same context/routing functions, shows the permitted provider payload, and never calls Gemini. The existing finance/RAG APIs remain compatible for external clients and admin tools; they are not separate chat screens.

## Privacy and failure behaviour

Clicking the floating bar checks permission and opens the fixed Agree/Disagree notice with a detailed policy link when needed. Agree opens the assistant; Disagree sends nothing and leaves it closed. Access management and revocation live in Account settings. Enter submits, Shift+Enter inserts a newline, IME composition does not submit, and an in-flight guard prevents duplicates. No original files or API keys are sent in prompts. The free-provider boundary excludes personal account/policy/claim context. The model has no executable tools. A provider quota/timeout failure is visibly labelled; original RAG excerpts are never presented as generated text. General insurance education is distinguished from source-backed policy/legal answers, and missing evidence on a source-required question never falls through to model memory.

## Actual validation

- Baseline: 216 backend checks passed before the backend refactor.
- Final: 244 backend checks pass, covering routing in Vietnamese/English/Chinese, source-only generation, missing evidence, previews, free-provider exclusions, read-only actions, withdrawal during success/fallback and consent revocation on both routes.
- Development browser checks: 13 pass with deterministic provider responses, including the single entry point, pending-question consent, source links, keyboard behaviour and admin publication.
- Real local Google calls passed for both routes: RAG 3.015s; general Gemini 1.906s. A separate compiled-production browser journey used actual Google generation and real Chinese reference passages, showed citations and withdrew permission afterward (3.561s). These are individual observations, not a latency guarantee.
- Frontend lint, TypeScript and production build pass. **32 selected production browser regressions pass** (1.6m) on a fresh isolated QA database. Four legacy development-only flows are excluded from this production selection. Production regression results are recorded separately in `submission/evidence/unified-assistant-production-browser.txt` and the implementation report. The initial full browser run used a disabled mock-payment worker; that configuration was corrected before repeating the payment regressions. A real order/event snapshot race was fixed by fetching the authoritative order before its event log. The owned-document citation check was updated for multiple shared matches and the UI retains page numbers. Repeated registration tests reached the normal limiter; final runs used a fresh isolated QA database, preserving production limits.

No model training, automatic money movement, legal entitlement decision or long-term legal monitoring was added. The existing eight-source competition selection remains unchanged. Intent rules and lexical retrieval have a bounded vocabulary; unusual phrasing can be misrouted or lack evidence, and the assistant must not invent missing policy facts.

## Reproduction

PowerShell (repository root):

```powershell
cd backend
.venv/Scripts/python.exe -m pytest -q
cd ../frontend
npm run lint
npx tsc --noEmit
npm run build
$env:PLAYWRIGHT_BASE_URL='http://127.0.0.1:3105'
npx playwright test
cd ..
node scripts/check_rag_browser_real.mjs http://127.0.0.1:3105 china
```

Unix uses `.venv/bin/python` and `PLAYWRIGHT_BASE_URL=http://127.0.0.1:3105 npx playwright test`. Start the compiled frontend and backend first, configure matching proxy/origins, and enable the mock-provider worker for the full payment browser suite. Real-provider acceptance requires the locally configured server key and explicit in-app consent; it does not read a key from command arguments. The source excerpt tests use only published public references.

## Verified online release

Render deployment dep-dbb22rtg1s2s73dvo1e0 serves application commit 04aae9b4b0e9f8de0bd35045dceebf5bf153c9c4 at https://ai4s-demo.onrender.com/copilot. The server setting is gemini-3.5-flash-lite. Actual online RAG generation passed in 3.578s and general generation in 2.235s. The eight published-source hashes still match the selected competition corpus. The browser confirms one chat entry and that /knowledge navigates to /copilot. See unified-assistant-deployment-receipt.json and unified-assistant-render-real.json; screenshots/rag/unified-assistant-render.png shows the deployed interface. These checks used public questions/excerpts, revoked the test permission afterward and did not alter private records.

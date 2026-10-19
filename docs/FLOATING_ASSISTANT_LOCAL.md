# Floating assistant: local review

This change is uncommitted and has not been pushed or deployed. Use http://localhost:3000, with the existing local API on port 8000.

## Manual checks

1. Sign in or choose the sample-data account. The assistant bar is centred at the bottom of every authenticated application page.
2. Click the bar. Without current permission, read the Agree/Disagree popup and its permission-details link. Disagree must leave the chat closed and send no question. Agree opens the chat and focuses its input. Existing valid permission is reused until expiry or revocation.
3. Ask “Bảo hiểm sức khỏe ở Trung Quốc có những quy định gì?” to exercise retrieval and source-grounded generation. Open the folded source section to inspect a versioned source page. Ask “Làm sao thích nghi khi mới đi du học?” for general study guidance. There is no manual route/mode selector. Provider availability and retrieval evidence determine the actual response.
4. Enter sends; Shift+Enter adds a line. New replies scroll the message area automatically and leave the page behind it in place. Try several long replies and confirm the composer stays visible.
5. Change pages using application navigation, minimize and reopen. The same in-memory conversation remains. Reloading the browser clears the conversation.
6. Open Account settings, minimize chat and select Revoke Gemini access. Reopen the bar: permission must be requested again, and the old conversation must be gone. This also discards display of a reply that was still in flight; previously sent provider content cannot be recalled.
7. Check Vietnamese/English/Chinese, light/dark, a narrow phone and short landscape. Permission management is absent from the chat itself.

## Reproduce automated checks

The full suite requires a running API, frontend, local PostgreSQL, OCR dependencies and a server-provisioned RAG administrator. The administrator JSON remains ignored and contains `email` and `password`; never add it to source control. Using a fresh isolated local QA database is recommended for repeated full runs to avoid the normal registration/login rate limits. Do not weaken rate limits or reset user data.

Windows PowerShell, from `frontend`:

```powershell
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
$env:RAG_BROWSER_ADMIN_CREDENTIALS=(Resolve-Path ../.local/rag-admin-test.json).Path
npx.cmd playwright test tests/gemini.spec.ts tests/rag.spec.ts --reporter=list
# Full regression suite, when the test account and environment are prepared:
npx.cmd playwright test --reporter=list
```

Unix shell, from `frontend`:

```sh
npm run lint
npx tsc --noEmit
npm run build
export RAG_BROWSER_ADMIN_CREDENTIALS=/absolute/path/to/ignored/admin-test.json
npx playwright test tests/gemini.spec.ts tests/rag.spec.ts --reporter=list
# Full regression suite, when the test account and environment are prepared:
npx playwright test --reporter=list
```

The deterministic chat tests mock provider responses. The separate `floating-assistant-live.json` records an actual local browser request through RAG and Google Gemini. Screenshots in `submission/evidence/screenshots/floating-assistant/` include both test fixtures and the labelled real integration check. No real-money transactions or insurer submissions were performed.

# Assistant product copy and consent

The local product presents one **Trợ lý du học / Study-abroad assistant / 留学助手**. Model/provider names are removed from ordinary labels, permission buttons, fallback/error messages and normal assistant introductions. Internal API fields, provider adapters and legacy redirects stay compatible. Provider identity remains accurately disclosed in the detailed privacy terms as Google, with a link to its official AI-service terms.

The consent popup contains a short purpose, a readable external-processing statement, an age/terms acknowledgement, one details link, and Agree/Disagree. Technical conversation-turn counts and context-passage counts are no longer presented as user-facing conditions. Account settings provide View terms and Withdraw consent. Resource bounds still apply internally; this change does not enable unlimited prompt size or expand permissions.

The linked public notice describes account access boundaries, the shared sample account, administrator publication of knowledge sources, infrastructure access, the external processor, unpaid-service data use, retention, withdrawal and actual deletion limits. It does not promise that all content stays inside the application or that disclosure/security incidents are impossible. Personal financial records, private policies, claim files and original uploads remain excluded from the unpaid external AI path.

The consent notice version is now `assistant-privacy-2026-10-19-v3` on both client and server. Previously recorded permission remains in the audit history but cannot silently authorize the updated notice. The user must agree again. The server still fixes the sample-assistant scope to conversation context and sample/public excerpts; there are no preselected extra data permissions.

Provider processing was checked against the official terms on 19 October 2026: https://ai.google.dev/gemini-api/terms . The current terms describe use of unpaid-service input/output to improve products and possible human review, and warn against submitting sensitive, confidential or personal information. These facts are disclosed in the linked product notice. This copy change is not a legal-compliance certification or a security audit.

Validation receipts are under `submission/evidence/simple-consent-*`; desktop and mobile light/dark screenshots are under `submission/evidence/screenshots/simple-consent/`. The real local browser check covers consent before dispatch, an actual generated assistant introduction, absence of vendor names in nine application pages, and subsequent withdrawal. Deterministic tests separately cover refusal, expired/newer notices, stale permission versions, source citations, keyboard behavior, Account synchronization, file consent and administrator publication.

From `frontend`, PowerShell:

```powershell
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
$env:RAG_BROWSER_ADMIN_CREDENTIALS=(Resolve-Path ../.local/rag-admin-test.json).Path
npx.cmd playwright test --reporter=list
```

Unix shell equivalents are `npm run lint`, `npx tsc --noEmit`, `npm run build`, and `RAG_BROWSER_ADMIN_CREDENTIALS=/absolute/path/to/ignored/admin-test.json npx playwright test --reporter=list`.

From the repository root, backend verification is `backend/.venv/Scripts/python.exe -m pytest backend/tests -q` on PowerShell, or `backend/.venv/bin/python -m pytest backend/tests -q` on Unix. Tests require a dedicated PostgreSQL database with a name ending `_test`; do not reset application data. Repeated full browser runs should use an isolated QA database rather than weakening registration limits.

Delivery remains local at http://localhost:3000. No commit, push or deployment is authorized or performed.

## Executed results

Final full verification: 276 backend tests passed (one existing dependency deprecation warning), 40 browser tests passed, and lint, TypeScript and production build passed. The real local provider call took 5.218 seconds with no fallback, nine pages passed the branding check and test consent was withdrawn afterward. These are individual observations, not latency or security guarantees.

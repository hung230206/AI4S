# Executed evidence

`backend-tests.txt` and `backend-junit.xml`: final pytest invocation, against a separate PostgreSQL database. `frontend-lint.txt` and `frontend-build.txt`: actual lint/build output. `browser-results.json`: actual Playwright run; `screenshots/`: real browser captures, desktop/mobile/print. `operations.json`: API-generated success/failure/expired/cancelled histories plus duplicate provider event audit. `npm-audit.json` and `npm-audit-runtime.json`: full and runtime audit results. `dependency-licenses.json`: installed package license metadata. `source-scan.txt`: scan for accidental copies of local secret values.

The current MVP suite has 75 backend tests and 7 browser flows. `mvp-live-http.json` records a separate actual HTTP smoke of registration/cookie session, a user-entered QA invoice, the connected Frankfurter reference rate, private document extraction/citation/download/delete, archive and logout revocation. Its account/invoice/document content is explicitly self-authored QA input; the reference rate is actual upstream/cache data. No credentials are exported. `screenshots/mvp/` contains the sign-in/private dashboard/reference quote/mobile policy citation captures. Current API contract: `contracts/openapi-mvp.json`.

Reproduce with RUNBOOK.md. `scripts/demo_evidence.py` creates new fictional invoices and uses controlled quote timestamps only for the expiry scenario; it does not fabricate event histories or results. Screenshot captures do not include operator authentication input. Never publish `frontend/test-results/` or `.env`.

The exact latest run counts and unresolved caveats are recorded in the implementation report. Screenshots are evidence of the captured states, not a full accessibility or security certification.

# Consumer-facing insurance form

Local update, 20 October 2026. The insurance form no longer accepts review-fields.json uploads. JSON validation/import code and its input were removed rather than renamed. Technical fixture data remains available to automated QA and developer tools; it is not a required user document. The current default consumer pack omits JSON entirely.

The policy editor now explains three ordinary steps in Vietnamese, English and Chinese: choose/upload the policy document; check suggested details and complete missing fields; review and save. The original text remains accessible in a collapsed disclosure. The subsequent document-assist upgrade now fills supported fields automatically with source evidence; see DOCUMENT_ASSIST_UPGRADE.md. Missing values remain blank and the user reviews before saving. Benefits retain their source-page and verbatim-clause fields. Monetary inputs, file consent, human confirmation, server citation validation, revision checks and owner isolation are unchanged. Select controls and benefit amounts have human-readable accessible labels.

The sample help, downloadable pack README and current sample-pack HTML/Markdown instructions now describe the ordinary form. The same ten delivered sample documents retain their tested hashes. Reference JSON files remain developer metadata and are not loaded through the product UI.

Actual checks and evidence are recorded in IMPLEMENTATION_REPORT.md and submission/evidence/consumer-insurance-*. Tests now enter policy details through the visible controls, rather than bypassing the workflow with a JSON fixture upload. They retain the invalid-citation rejection, correction/reconfirmation, payment/claim-export and mobile/localisation checks, and assert that no JSON upload or review-fields instruction appears in the insurance workspace.

Reproduction from repository root, Windows PowerShell:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests/test_insurance.py -q
Push-Location frontend
npx.cmd playwright test tests/insurance.spec.ts --reporter=list
$env:RAG_BROWSER_ADMIN_CREDENTIALS=(Resolve-Path ../.local/rag-admin-test.json).Path
npx.cmd playwright test --reporter=list
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
Pop-Location
```

Unix shell:

```sh
backend/.venv/bin/python -m pytest backend/tests/test_insurance.py -q
cd frontend
npx playwright test tests/insurance.spec.ts --reporter=list
RAG_BROWSER_ADMIN_CREDENTIALS=../.local/rag-admin-test.json npx playwright test --reporter=list
npm run lint
npx tsc --noEmit
npm run build
```

Backend tests require the dedicated *_test database enforced by conftest.py. Browser checks use the running local application and separate QA users; never reset the user's database or relax authentication limits. No commit, push or deployment is part of this change.

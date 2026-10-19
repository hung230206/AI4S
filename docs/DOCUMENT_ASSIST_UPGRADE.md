# Document assistance and current China sample pack

Local implementation, 20 October 2026. No commit, push or deployment. This supersedes the manual-entry description in CONSUMER_INSURANCE_FORM.md. All test policy terms remain fictional, independently of how accurately the application extracts them.

## Observable behaviour

1. **Policy upload:** OCR/text extraction is followed by a read-only structured proposal. The new two-page Chinese/English PDF fills eight main fields and four benefit groups, including amounts, deductibles, percentages, waiting periods, page numbers and verbatim clauses. Each main field has original-page evidence. Selecting a different source clears the previous proposal. Opening an existing reviewed policy preserves edits and does not re-extract over them. Missing dates, currency and territory stay blank; no default date is presented as a document fact. Save still requires human confirmation and server citation checks.
2. **Invoice upload:** the extractor handles inline labels and PDF table labels whose values appear on the next line, Chinese/English/Vietnamese synonyms, OCR whitespace around decimal punctuation, and conflicting amount candidates. It suggests the fee category separately from the five required invoice fields. Choosing a new file resets the previous draft. Claim forms, medical records, discharge summaries, itemized costs, accident statements and explicitly paid hospital expenses are directed to claim preparation; the server also rejects their reuse as payable invoice sources.
3. **Claim draft:** after selecting a policy, users may upload a claim form or hospital bill to fill the incident date, amount and explicitly stated claim type. Amounts are applied only when the document currency matches the selected policy. Future/unknown incident dates remain blank. Creating a case from a proposal requires a separate human review checkbox. This file is stored as a private document; the guide explicitly says to attach it in the appropriate checklist slot after creating the case.
4. **Attachment comparison:** text PDFs and TXT attachments are compared after upload, with a repeatable comparison button for existing files. Readable amounts, currency, dates and document categories are checked against the case. Differences are warnings, because partial bills and later treatment dates can be legitimate. Comparisons do not change amounts, checklist state, eligibility, submission or payout. Existing comparisons are cleared after a case edit. Images/scanned PDFs in the attachment slot require original-document review or the OCR-enabled fill-from-document step; the comparison response states when no text is available.
5. **Document retrieval:** Vietnamese questions about outpatient/inpatient benefits, waiting periods, deductibles, renewal, limits, evacuation and reimbursement are expanded to English/Chinese terms. Existing RAG-to-LLM source-based synthesis and account permissions remain in place. A missing fact is still missing, rather than a model-generated policy term.
6. **Downloads:** /insurance/sample-pack defaults to the current ten-document China pack, installed in tracked fixtures and included by the deployment Dockerfile. The consumer archive contains no JSON import file. Insurance and test-lab screens point to it. The larger engineering test-lab archive also includes it under China_Current_Samples. The legacy dynamic regression fixture is available only through the explicit edition=regression parameter for existing automated business-flow tests; it is not the default user download.

## Method, privacy and boundaries

The new autofill layer combines actual local OCR with multilingual label/section extraction, Decimal/date validation, conflict detection and original-page provenance. It is not a newly trained model and does not call Gemini for private policy or medical files. It ignores narrative instructions as extraction labels and never invokes transaction tools. Generic extraction may leave unfamiliar layouts blank; it does not guarantee universal document recognition. Benefits are entered summaries, not insurer verification.

Gemini's structured-output documentation was reviewed as an alternative: https://ai.google.dev/gemini-api/docs/structured-output and https://ai.google.dev/gemini-api/docs/document-processing . A valid JSON schema alone cannot establish that a returned amount or benefit is supported by the document. The existing external-provider privacy boundary was therefore retained rather than sending uploaded private documents automatically. Provider terms: https://ai.google.dev/gemini-api/terms . The current upload path needs file-processing consent, enforces account ownership and preserves review before writes. Extraction/comparison responses use the existing no-store middleware. No original file is published into shared RAG by these endpoints.

Sample structure and source-access limitations remain documented in RESEARCH_BASED_UPLOAD_SAMPLES.md and the archive's NGUON_NGHIEN_CUU.md. The ten original PNG/PDF bytes are unchanged; only consumer instructions and packaging were updated.

## Reproduce

Start PostgreSQL, backend on 8000 and frontend on 3000 as documented in the main README. Use the isolated *_test database for pytest; never truncate the normal demo database. Browser tests create QA records in the running local application.

Windows PowerShell, repository root:

```powershell
Push-Location backend
.venv/Scripts/python.exe -m pytest tests/test_document_assist.py -q
.venv/Scripts/python.exe -m pytest -q
Pop-Location
Push-Location frontend
npx.cmd playwright test tests/document-assist.spec.ts --reporter=list
$env:RAG_BROWSER_ADMIN_CREDENTIALS=(Resolve-Path ../.local/rag-admin-test.json).Path
npx.cmd playwright test --reporter=list
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
Pop-Location
backend/.venv/Scripts/python.exe scripts/package_china_upload_samples.py
backend/.venv/Scripts/python.exe scripts/verify_source.py
```

Unix shell:

```sh
(cd backend && .venv/bin/python -m pytest tests/test_document_assist.py -q && .venv/bin/python -m pytest -q)
(cd frontend && npx playwright test tests/document-assist.spec.ts --reporter=list)
(cd frontend && RAG_BROWSER_ADMIN_CREDENTIALS=../.local/rag-admin-test.json npx playwright test --reporter=list)
(cd frontend && npm run lint && npx tsc --noEmit && npm run build)
backend/.venv/bin/python scripts/package_china_upload_samples.py
backend/.venv/bin/python scripts/verify_source.py
```

Actual outcomes and any repaired test failures are recorded in IMPLEMENTATION_REPORT.md and submission/evidence/document-assist-*.

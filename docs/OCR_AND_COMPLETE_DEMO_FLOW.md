# OCR recovery and complete demo journeys

Implemented locally on 20 October 2026. This change addresses an uploaded full-page bilingual claim-form image failing at invoice OCR on constrained hosting. No private image, recognised personal/medical/banking text or real credentials are included in source, test fixtures or screenshots.

## Diagnosis and processing

The previous invoice UI waited for synchronous OCR; the subprocess had a fixed 75-second limit. The supplied 1200 × 1696 image was readable locally: the baseline took 17.047 seconds. Local success does not reproduce Render's CPU/RAM conditions or prove the reported production timeout's exact cause. The old combination of one long request, three language models and a hard timeout was a plausible failure path. The supplied file is a VND claim form, not a CNY invoice for payment.

Invoice uploads now use `POST /api/v1/invoice-imports/jobs` (202) and authenticated `GET /api/v1/invoice-imports/{id}` polling. The source, processing state and extracted results persist in the existing owner-scoped `InvoiceImport` record. States are QUEUED, RUNNING, COMPLETED and FAILED. The browser stores only the source ID in account-scoped session storage and resumes polling after a reload. It does not persist recognised text in browser storage. A completed document is applied only after processing, and saving an invoice still requires human review.

There is at most one pending file per account, four admitted jobs globally, bounded OCR concurrency and at most 100 retained source records per account. PostgreSQL advisory admission locking and per-account locking serialize duplicate uploads and capacity checks. Workers use independent database sessions; OCR does not hold an open database transaction. Generation tokens prevent an older attempt overwriting a newer retry. Polling marks a job older than 15 minutes as interrupted; reuploading the same file retries the retained source. Sources are persisted, but an in-process worker does not automatically resume after a server restart. The recovery path is an explicit retry, not an automatic restart guarantee. Background failures do not log extracted text or raw database exception parameters.

The default subprocess timeout is now 180 seconds, configurable with `OCR_TIMEOUT_SECONDS` (30–300). The cloud Docker image installs native Tesseract and uses the existing pinned, local fast language models with neural mode and one OpenMP thread. Local Windows installations without the native executable retain the existing Tesseract.js fallback. No OCR document is sent to an external API. Other synchronous document upload paths retain their existing behaviour, with the default proxy allowance increased to 210 seconds; the invoice UI no longer depends on a long proxy request.

Technical references: native invocation, language selection and segmentation are documented at https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html . Thread configuration and performance considerations are documented at https://tesseract-ocr.github.io/tessdoc/FAQ.html . These references inform implementation choices, not a guaranteed hosting latency.

## Correct document handoff

Recognisable claim-form headings produce `document_type: CLAIM_FORM`. Explicit VND is labelled VND. Neither a claim form nor an identified VND source can be used to save a CNY payment invoice; the backend enforces this independently of the UI. The claim form's amount, patient, beneficiary and bank details are not auto-filled into payment fields.

The invoice page offers **Continue to a claim case**. Choose a draft case or create one from a separately reviewed policy. `?import=<source UUID>` carries only the private source identifier. A claim form does not substitute for a policy or establish insurance rights. The claim screen shows the filename and asks for separate attachment-processing consent. `POST /api/v1/insurance/claims/{id}/attach-import` reuses the original bytes only after checking source ownership, case ownership, completed extraction, document type, revision, file type, size and attachment limits. No second upload or OCR is required. Repeated attachment is deduplicated by hash. The source is not placed in shared RAG or external AI evidence. Case amount/currency are not changed to match the form; users must review actual applicability.

## Completing the demo

For ordinary invoices and premium estimates, the default sandbox method is now automatic SUCCESS rather than the advanced operator-only method. The user still reviews a server quote and explicitly consents. Only a signed mock-provider event produces success and a simulated receipt. The operator simulation endpoint remains restricted; real payments remain disabled.

If the reference-rate service is unavailable, **Continue with a demo rate** requests `demo_rate: true`. This is available only in demo mode, uses the server's configured Decimal rate/fees and shows DEMO_RATE. There is no silent substitution of a reference FX rate. The explicit demo option does not call the external FX service. The normal reference-rate path is unchanged.

After success, the payment page provides links back to budgeting and claim preparation. A policy-linked premium passes its policy ID to the claim form, which selects only a matching active policy owned by the account. Sandbox success does not activate cover or automatically deduct a financial ledger balance. Actual-expense recording remains a separate human action. Existing claim steps remain draft → checklist-ready → user-reported external submission → closed, with original-file ZIP export; they do not send a claim to an insurer.

## Local reproduction

With the API on port 8000, frontend on port 3000 and the existing test-only database configured, PowerShell commands from the repository root are:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests/test_ocr_jobs.py -q
cd frontend
npx.cmd playwright test tests/ocr-jobs.spec.ts --reporter=list
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
```

Unix uses `backend/.venv/bin/python`, `npx` and `npm`. Runtime OCR models must already be installed with `python scripts/setup_ocr.py`; that setup downloads public model files only. Browser payment tests need `PROVIDER_WORKER_ENABLED=true` and `DEMO_MODE=true`. Full-suite RAG tests additionally need the ignored local administrator credential file configured through `RAG_BROWSER_ADMIN_CREDENTIALS`.

Dedicated evidence is prefixed `ocr-flow-`; screenshots under `screenshots/ocr-jobs/` contain only self-authored fictional documents. Exact executed validation totals and remaining deployment limitations are recorded in the latest implementation report section.

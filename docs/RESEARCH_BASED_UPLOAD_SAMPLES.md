# Research-shaped Chinese upload samples

Created locally on 20 October 2026. The subsequent document-assist upgrade installs these ten documents as the default website download and adds grounded automatic form filling; see DOCUMENT_ASSIST_UPGRADE.md. No commit, push or deployment was performed.

The delivery contains ten upload files: three PNG fee notices (tuition CNY 20000.00, accommodation CNY 6000.00, insurance CNY 800.00); one two-page insurance schedule; and six PDF claim documents (hospital bill, medical record, claim form, discharge summary, itemized expenses and accident statement). The medical case uses consistent fictional identity/case references, dates and a reconciled CNY 980.00 total. Identity and bank documents remain outside the app's upload workflow.

These are newly authored, clearly marked test documents. They are not real fiscal invoices, issued policies, medical records or authority certificates. Test coverage limits, waiting periods, percentages, institutions and clinical narrative are invented. Sources support document categories and field/layout structure; they do not establish validity of the invented terms. No genuine logo, official seal, payment QR, passport or bank account was reproduced.

## Research and access limits

- Shanghai Jiao Tong University's 2025 insurance purchase notice was read as a PDF. Used for premium/period/receipt structure, not as a source for invented benefit limits: https://isc.sjtu.edu.cn/kindeditor/Upload/file/20250826/20250826031349_9371.pdf
- Hohai University's medical-service page was read. Its linked claim/accident PDFs blocked off-campus access; their contents were not claimed as reviewed: https://cie.hhu.edu.cn/16190/listm.htm
- The lxbx.net claims checklist was read as a PDF and used to select attachment categories: https://www.lxbx.net/storage/website/20240402/Q420240402144639403992859232.pdf
- Fee-category, medical-bill and medical-record headings also use indexed primary-source content. Direct fetches were blocked or failed; these limitations are disclosed in the bundle's NGUON_NGHIEN_CUU.md. Historical publication dates are retained and no claim of present legal force is made: https://admission.just.edu.cn/10238/list.htm ; https://czt.gd.gov.cn/czpw/content/post_2644253.html ; https://www.nhc.gov.cn/wjw/gfxwj/201002/79d42b9c8b3f47ee91000d31de116784.shtml . These references were not added to shared RAG.

## Actual validation

All seven PDFs rendered with readable embedded Chinese text and passed the application's own PDF text extraction. A contact sheet of all eleven document pages and full-size representative pages were visually reviewed. Policy source quotations match extracted page 2 exactly. The claim PDF is classified as CLAIM_FORM by the invoice reader.

All three images passed actual queued OCR on the local API, in 3.05, 3.05 and 3.03 seconds in the final run. Invoice number, amount and due date matched exactly; issuer and recipient were recognised. A private QA run successfully saved four policy benefits with server-verified citations, uploaded all six attachment types across two claims and verified byte-identical export. The final repeat used the existing STUDENT sandbox with fictional files only and repeated those checks against deterministic final PDF bytes (nine attachment uploads across inpatient/accident cases). Offline identity/bank readiness was deliberately left unconfirmed. No AI consent, external LLM request, payment, insurer submission or corpus publication was performed. Initial validation harness errors were an incorrect consent-purpose header and an absent demo CSRF value; both were repaired without changing the application or bypassing its checks.

Final delivery hashes match all ten files actually tested; ZIP integrity and its ten PDF/PNG entries were checked. The consumer ZIP includes a Vietnamese clickable HTML guide and provenance notes. REVIEW_FIELDS.json, UPLOAD_MAP.json and VALIDATION.json remain local developer reference artifacts and are excluded from the default website archive. Result copies are under submission/evidence/research-samples-*. The archive is also copied to the user's Downloads folder. Timings are local observations, not Render measurements.

## Reproduce

Requires reportlab, pypdf, Pillow, Poppler/pdftoppm and a CJK TrueType font. The generator uses the Windows SimSun collection by default; DEMO_CJK_FONT can point to a compatible font on another system. The validation script uses the existing backend environment and local API on port 8000. --demo uses only fictional samples in the shared sandbox; omitting it creates an isolated QA account. Registration limits remain unchanged.

Windows PowerShell, repository root:

```powershell
& 'C:/Users/hungt/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' scripts/create_research_upload_samples.py
backend/.venv/Scripts/python.exe scripts/validate_research_upload_samples.py --demo
```

Unix shell, with the stated dependencies and compatible CJK font installed:

```sh
DEMO_CJK_FONT=/path/to/CJK-TrueType-font.ttf python3 scripts/create_research_upload_samples.py
backend/.venv/bin/python scripts/validate_research_upload_samples.py --demo
```

The initial sample-only task used the API validations above. The later application upgrade runs the full backend/browser regressions; exact current results are in IMPLEMENTATION_REPORT.md.

# Financial-participant implementation, 2026-10-18

The user clarified that their screenshot analyses the competition problem and requested that the application be developed along that interpretation, using callable APIs where useful. This is the implemented scope, not a claim that every technology named in the screenshot is an official mandatory requirement. The formal topic/registration choice remains with the team.

Official problem reference: https://www.pol.cmu.ac.th/public/blog/attachment/download/7a51866a-4cee-42b5-9187-fa4e1f4df411 . Topic C covers international-student/cross-border financial needs, including tuition and multi-currency management. The current implementation focuses that journey while retaining private insurance-document assistance and the verified payment sandbox.

| Analysis dimension | Delivered implementation | Boundary |
|---|---|---|
| Multi-currency ledger | Owner-scoped CNY/VND wallets with user-declared opening balances/dates; actual income/expense posting; void audit trail; CSV; server Decimal precision | No custody, bank synchronization or real exchange; original currencies remain separate |
| Adaptive interaction | Contextual help and progress, route-specific instructions, data-derived next-step cards, shortfall/overdue warnings, grounded assistant routing and links into working workflows | UI decisions and assistant intents are explainable rules; no free-form LLM-generated interface |
| OCR | Local neural Tesseract.js/WASM recognition for images and scanned PDFs; text extraction for text PDFs; labelled field parser; page/source-line evidence; required user review and retained original | Not guaranteed on every photo/layout/handwriting; ambiguous fields remain for review; invoice currency is CNY |
| Document grounding | Local OCR for scanned policies, private text storage, multilingual keyword/synonym/CJK retrieval, original page excerpts and cited assistant responses | No LLM generation, semantic embedding model, insurer coverage decision or claims filing |
| Cash-flow forecast | 30/60/90-day native-currency projections from declared balances and scheduled income/expense; monthly calendar-day clamping; overdue handling; explicit actual-entry confirmation | Schedule-based calculation, not a learned prediction; does not infer undeclared costs or automatically import sandbox payments |
| FX risk awareness | Connected Frankfurter daily observations/history, cached provenance, amount/budget scenarios at reference and ±5%, deficit display and budget threshold | Not intraday market data, execution quotes, timing advice, hedging or a provider-fee estimate |
| Bounded autonomy | Extraction and read/compute assistance; finance writes require authenticated, CSRF-protected user actions; explicit source review, actual-entry confirmation and separate payment consent | Assistant endpoint returns `executed_actions: []`; it cannot invoke a payment or rewrite an order outcome |

## Architecture and data

FastAPI/SQLAlchemy/PostgreSQL adds four tables via static Alembic revision `9f40f776cbf8`: `finance_wallets`, `finance_plans`, `finance_entries`, `invoice_imports`. Existing records and payment state-machine constraints are preserved. Total: 18 ORM tables, 45 OpenAPI paths. The current contract is `contracts/openapi-mvp.json`.

Invoices continue to be user-entered/unverified. An imported document is not an invoice until the authenticated owner reviews and saves it. Its exact bytes, pages and proposed fields are retained privately; a repeated save of the same source is rejected. Original bytes can be downloaded by the owner. Extraction does not create a quote, ledger entry or payment.

The cash-flow engine keeps original currency amounts as Decimal. The graph converts values to browser numbers only for drawing coordinates. Amounts displayed/exported remain server-derived strings. Amount precision, ownership, supported currencies and date bounds are enforced server-side. Entries use owner-scoped idempotency keys plus request hashes and a per-user lock. A posted plan occurrence has a unique partial database index; confirmation changes current balance exactly once and removes that occurrence from forecast. Voiding it restores its effect and makes the occurrence planned again. Monthly recurrences preserve the original day and clamp to month end.

Invoice-derived plans copy the server invoice amount/date; they are explicit snapshots and are labelled as such. No automatic invoice/sandbox-payment deduction occurs. Native projections remain available when the reference FX service is unavailable; the combined VND valuation is withheld rather than fabricated.

## OCR runtime and verified public integration

Tesseract.js 6.0.1 runs in a separate bounded Node worker called by the API. Language packs `eng`, `vie`, `chi_sim` are downloaded at setup from https://github.com/tesseract-ocr/tessdata_fast at commit `87416418657359cb625c412a48b6e1d6d41c29bd`; sizes/hashes are exported in `submission/evidence/ocr-model-manifest.json`. Runtime OCR uses local models, without sending private input to a third-party OCR service. Pillow normalizes images; pypdfium2 renders scanned pages. The API supports at most two concurrent local OCR subprocesses with 75-second timeouts, 5 MB uploads, 16-megapixel images and a five-page scan limit. Text-policy documents retain the existing 50-page limit.

Reference docs: https://github.com/naptha/tesseract.js/blob/master/docs/api.md ; https://github.com/naptha/tesseract.js/blob/master/docs/local-installation.md ; https://pypdfium2.readthedocs.io/en/stable/ . Model licenses and native-runtime notices must be retained. Host Node.js and `frontend/node_modules` are required by this local OCR deployment; run `npm ci` and `python scripts/setup_ocr.py` before OCR tests.

Frankfurter remains the actual no-key public integration: https://frankfurter.dev/ and https://api.frankfurter.dev/v2/ . The app calls pair/history routes with public currency codes and dates only. No external payment provider was connected; no sandbox account, merchant registration or production eligibility was invented.

## Measurement and limitations

`scripts/benchmark_local_ocr.py` generates three clean self-authored printed images and runs actual local OCR with the appropriate language. An initial mixed-language/spacing attempt exposed weak Vietnamese extraction and spaces between Chinese glyphs. Added an explicit language selector and CJK/date whitespace normalization. The measured rerun matched all five expected fields in each clean English, Vietnamese and Chinese sample (0.67s, 0.75s and 1.05s on this host). This is a smoke set, not a production accuracy estimate. It does not cover real photos, handwriting or varied institution layouts. Original source and required review remain essential.

`scripts/check_student_finance_live.py` verifies actual HTTP through the frontend proxy, real local Chinese OCR, the review gate and original-file byte integrity, native-currency shortfall projection, entry retry/void accounting, actual reference FX/history, scanned policy citation, read-only payment intent and cookie revocation. It exports no credentials. Final exact test counts/timings are in IMPLEMENTATION_REPORT.md.

No public deployment, live financial transfer, insurance activation, generative LLM service, statistical spending model, realtime FX feed, email notification service or provider connection was introduced. These are concrete current product boundaries, not hidden replacements for working features.

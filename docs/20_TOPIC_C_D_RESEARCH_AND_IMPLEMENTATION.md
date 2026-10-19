# Topic C + D: research and working implementation

Research checked 19 October 2026 (Asia/Bangkok). This is a product-development decision, not registration or an insurer's advice.

## What the competition actually asks

The International Track asks teams to choose **one** of six topics. Topic C concerns international students and cross-border financial needs, including remittances, tuition and multi-currency management. Topic D concerns policy questions, coverage-gap analysis and claims guidance. The shared scoring weights are task completion 40%, security/compliance 30%, innovation/interaction 30%. Non-on-chain execution evidence can use simulated accounts or sandbox logs.

Primary sources:

- Organizer material hosted by Chiang Mai University, pages 1–2: https://www.pol.cmu.ac.th/public/blog/attachment/download/7a51866a-4cee-42b5-9187-fa4e1f4df411
- Technical-guidance institution IEEE CIS Singapore: https://www.ieee-cis-singapore.org/2026-fintechathon
- Organizer website and controlling rules: https://fintechathon.g-ican.com/

The implementation combines C and D **within one student journey**. It does not claim dual-topic registration, submit an entry, or guarantee a judging score. The team still chooses its official registration topic. The screenshot analysis of an “Interactive AI Framework” is a user-supplied interpretation, not an additional official requirement.

## Research method and its limits

1. Read the primary competition brief and compare its tasks with the running application's capabilities.
2. Review a published international-student insurance claims guide to identify the documents commonly involved in a China student scenario.
3. Separate insurance concepts from insurer-specific rules. Use a general insurance explanation only for vocabulary and the distinction between a policy, premium, deductible and claim.
4. Turn the missing tasks into explicit state transitions, account-scoped records and falsifiable acceptance scenarios.
5. Validate with self-authored fixtures, negative/security tests, browser journeys, original-byte hashes and deployment checks.

This is document research and prototype evaluation. No student interviews, clinical evaluation, actuarial study or usability study with recruited participants has been conducted. No empirical claim about conversion, savings or claim-success rates is made.

Sources used for the design:

- Insurance for Overseas Students in China, claims preparation guide, one page: https://www.lxbx.net/storage/website/20240402/Q420240402144639403992859232.pdf . It describes upfront outpatient expenses and a document matrix covering identity, hospital invoices, medical records, itemized costs, accident/discharge evidence, bank details and application forms. It is a general reference, not this user's contract. Its hotline is not installed as a universal emergency contact.
- NAIC, How Does Insurance Work?: https://content.naic.org/consumer/how-does-insurance-work . Used for general concepts only; United States material is not presented as Chinese or Vietnamese law.
- Existing daily FX integration: https://frankfurter.dev/ . Reference rates are dated and are not executable FX quotes or intraday market monitoring.
- Optional Gemini API: https://ai.google.dev/api/generate-content and https://ai.google.dev/gemini-api/terms . No new mandatory AI subscription or payment account was introduced.
- Render automatic deploy behavior: https://render.com/docs/deploys . The Blueprint now preserves the user's requested `commit` auto-deploy trigger.

## Resulting product flow

| Stage | Problem addressed | Working behavior | Scope |
|---|---|---|---|
| Policy source and review | A PDF does not give a student a usable portfolio | Upload through existing local OCR/text extraction; select a private source; review dates, territory, premium and benefits; keep exact page excerpts | D |
| Coverage comparison | A student cannot see missing limits or periods | Compare entered needs against each active policy; show missing limits, exclusions, period/territory/waiting gaps and unknown data | D |
| Premium budgeting | Insurance costs are disconnected from student cash flow | Add one native-currency planned expense; preserve current balance; forecast alongside tuition/living costs | C + D |
| Premium sandbox estimate | A student needs to understand VND cost and consent | Explicitly create an internal CNY fee estimate; reuse the existing dated FX, quote review, consent, signed sandbox outcome and receipt | C + D |
| Claim preparation | Students lose track of documents and evidence | Create an owner-scoped case, attach sample documents, check external items, review readiness, export originals and journal | D |
| Guided assistant | Data and next steps were scattered | Read-only direct guidance and optional Gemini see bounded reviewed policy facts and case status; server constructs navigation and citations | C + D |

## Method implemented in code

`backend/app/insurance.py` implements the workflow. Alembic adds portfolio, claim-case and private-attachment tables, plus a stable premium-estimate relation. Existing accounts, CSRF protection, user-row transaction locks and audit records are reused.

Each included/excluded benefit needs an excerpt of at least 12 characters present on the declared page. Whitespace is normalized, but the server does **not** prove that the human-entered interpretation follows from the excerpt. The UI makes the reviewer responsible for dates, amounts, territory, conditions and exclusions. Unknown numbers remain null; they are never replaced with zero.

Coverage comparison is deterministic and explainable. It requires matching currency and territory, a sufficient single-policy limit, the full requested period and a known elapsed waiting period. A matching result says only that the **entered criteria** match. Limits across policies are never added. Possible overlap is highlighted for insurer review. Deductibles, reimbursement percentages and excerpts are retained for review; they are not used to manufacture a claim payout prediction. Annual benefit consumption, sublimits, exclusions outside the entered summary, coordination and insurer verification are outside the comparison.

Premium plans and estimates are user-confirmed snapshots. Repeated creation is serialized; a policy has one linked plan and one linked estimate. Linking the same estimate through the invoice planning screen reuses the expense. A policy edit does not silently rewrite an existing financial plan. Sandbox success does not activate a policy, prove premium payment or produce an insurer-issued invoice.

Claims use `DRAFT → READY → SUBMITTED_EXTERNALLY → CLOSED`, with `READY → DRAFT` for corrections. The app checks checklist completeness before READY. Changing case details, attachments or checklist invalidates the readiness review. External submission requires a user-entered reference and explicit confirmation; it is a **self-reported record**, not a network submission or insurer outcome. Policy data is snapshotted at case creation, and the old source is retained even if the portfolio summary later changes.

## Security and privacy

- Owner checks on every portfolio, case, source, attachment and export path; no client-selected role or cross-account ID grants access.
- Cookie authentication retains origin and CSRF checks. Repeated creations use request hashes; updates and state transitions use revisions to reject stale writes.
- Claim files are stored separately from searchable policy documents and are never placed in Gemini evidence. Case descriptions and medical details are omitted from assistant context. Only bounded case status/deadline and reviewed portfolio facts are included.
- Passport/identity and bank-document categories cannot receive uploads. The user records their readiness outside Demo. This is not a classifier capable of detecting personal information hidden in a wrongly categorized file; use synthetic/anonymized data for public demo testing.
- Attachments accept bounded PDF/PNG/JPG/TXT types, with signature/UTF-8 checks, maximum 5 MB each, 8 files / 20 MB per case. Downloads force attachment disposition. There is no malware scanner or general-purpose authenticity check.
- Exports are private downloads containing original documents. Removing a draft attachment removes its stored bytes and retains the hash in the journal. Submitted cases lock further attachment changes.
- No medical diagnosis, underwriting, automatic eligibility decision, live bank transfer, live currency exchange or insurer approval API is implemented.

## Demonstration and handoff

Open `/insurance` or use “Start the C + D journey” on the dashboard, Test Lab or copilot. Download the dated test pack; it is generated from self-authored text and contains no actual medical, banking or identifying information. The editable JSON field loader is a test convenience, not automatic extraction or verified insurer data.

See `TOPIC_C_D_GUIDE.md` for a short Vietnamese walkthrough. See `IMPLEMENTATION_REPORT.md` and `submission/evidence/` for actual validation results. An online deployment is only considered verified after its health/release marker and an authenticated C+D journey succeed.

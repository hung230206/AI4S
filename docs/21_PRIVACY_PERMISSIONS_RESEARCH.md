# Privacy permissions and competition security design

Verified and implemented 19 October 2026 (Asia/Bangkok). This is an engineering assessment of the demo, not legal certification or an independent penetration test.

## Research and interpretation

The official International Track leaflet, retrieved and read in this review, allocates **30% to security/compliance**, and explicitly requests a security self-assessment describing permission tiers and known risks. It does not prescribe a universal cookie popup or require unnecessary device permissions. The team should demonstrate enforceable boundaries and disclose remaining limitations.

- Competition leaflet: https://www.pol.cmu.ac.th/public/blog/attachment/download/7a51866a-4cee-42b5-9187-fa4e1f4df411
- Technical-guidance partner, topics and track overview: https://www.ieee-cis-singapore.org/2026-fintechathon

Google's current Gemini terms distinguish unpaid and paid processing. Unpaid prompts/responses may support product improvement and human review; personal, sensitive or confidential information should not be submitted. Accordingly, consent alone does not make private-data use of the unpaid demo appropriate. `GEMINI_DATA_MODE=DEMO_ONLY` is the default: account finance and personal policy summaries are blocked, and optional retrieval only considers documents labelled `TEST_FIXTURE` or `PUBLIC_REFERENCE`. The application cannot independently prove the truth of these labels or that text is anonymous.

- Google provider terms and data-use conditions: https://ai.google.dev/gemini-api/terms

The EDPB's practical guidance describes consent as freely given, specific, informed and unambiguous, with an accessible withdrawal mechanism. We use those principles as design guidance, without asserting that a checkbox establishes GDPR compliance. Optional AI permission is separate from using the underlying service. Refusal does not disable uploads, internal OCR, local retrieval, budgets or payment review.

- Consent design guidance: https://www.edpb.europa.eu/sme/be-compliant/process-personal-data-lawfully_en

OWASP recommends separating untrusted input from instructions and constraining model authority. Document excerpts and conversation are untrusted. Gemini has no tools; source identifiers are allow-listed against server-created evidence, and financial actions remain separate authenticated workflows.

- Prompt-injection guidance: https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html

For a Vietnam-facing deployment, the official register identifies the Personal Data Protection Law **91/2025/QH15**, effective 1 January 2026, and implementing Decree **356/2025/ND-CP**. These are a legal-review starting point, not a claim that the project has satisfied every requirement. Cross-border processing, sensitive data, controller responsibilities and operational procedures require review of the actual operator and deployment.

- Government law record: https://vanban.chinhphu.vn/?pageid=27160&docid=214590
- Government decree record: https://vanban.chinhphu.vn/?pageid=27160&docid=216387

## Method

1. Read the published contest material and primary provider/security guidance.
2. Trace actual outbound calls, authentication, retrieval, uploads, logs and UI defaults.
3. Model bypasses: forged UI state, missing consent, stale revisions, changed scopes, another login, shared-demo users, expired permission, private retrieval winning top-k, and sensitive content.
4. Enforce boundaries in the API and verify them with mocked-provider adversarial tests plus actual HTTP acceptance; use self-authored fictional data for any real model request.
5. Test the full existing payment/insurance journey to detect regressions. Capture the final evidence and record limits explicitly.

## Implemented permission tiers

| Tier | Authority and data | Enforcement |
|---|---|---|
| Internal service | Owner-scoped data, local server OCR/retrieval and deterministic comparison | Authentication, CSRF for cookie writes, ownership queries; no cloud-model call |
| Optional external AI | Question + general app guide; optional history/documents; finance/policy summaries only in operator-configured paid-private mode | Versioned session consent, expiry, exact revision on each request, server-built evidence and data-mode checks |
| User financial review | Exact quote, amounts and explicit sandbox consent | Existing server-calculated Decimal amounts, idempotency, owner checks and signed asynchronous provider events; AI cannot approve |
| Development operator | Mock outcome/replay only | Separate server-validated operator code, demo-mode restriction and verified mock webhook; no real money authority |

AI permission is a persisted record bound to the authenticated **session fingerprint**, not the shared demo user. Each new demo token now has a random identifier; legacy shared tokens cannot grant AI access. Accounts logging in on another device start without AI permission. Permission expires after at most one hour and also requires valid authentication. Grant/update/revoke uses an optimistic revision under an owner lock. Notice/data-mode changes invalidate existing grants. Revocation and logout block future sends; another tab cannot continue with a stale revision.

All supplementary scopes and acknowledgement checkboxes start unchecked. Explicit confirmations cover notice comprehension, adult use and non-personal/non-sensitive test content. The Gemini control stays inactive until permission is granted; page load always selects internal direct lookup. Grant does not execute a chat request. Revocation is available in chat and account settings without another consent dialog.

### Data minimisation and disclosure

- History is optional, at most three earlier Gemini turns from the same permission revision. Earlier local replies are never silently forwarded. The backend discards ungranted history even if a modified client includes it.
- Document retrieval is optional, owner-scoped, at most three excerpts. In demo mode the provenance filter applies **before** top-k retrieval. User-provided private documents are excluded, even when they rank higher than samples.
- Budget/invoice and reviewed-policy contexts are separate optional scopes, disabled in demo mode. `PAID_PRIVATE` is an operator configuration requiring verified paid billing, provider terms/DPA and legal review; changing the flag is not itself proof of compliance. It does not enable claim-record sharing.
- Claim cases, attachments, medical descriptions, original file bytes, passwords, authentication cookies and operator/API keys are excluded from model evidence. A conservative text tripwire rejects recognisable emails, long phone/identity-like numbers and credential/medical labels before external dispatch. This is not a complete DLP or anonymisation system.
- An authenticated preview endpoint shows the context eligible at preview time without calling Google. The server checks current permission again on send. The preview is not a promise that subsequently edited account facts are frozen.
- Audit records contain notice version, revision, scopes, mode, model and evidence count, never the chat text or attachments. AI permission metadata persists; automatic retention cleanup is not implemented.
- `/privacy` is accessible before sign-in, and linked from sign-in, account and footer. Upload notices identify application-server processing and selected-file scope. No camera, microphone, geolocation, payment or USB device permission is needed; the frontend denies those unused browser capabilities through `Permissions-Policy`.
- Personal accounts can sign out all devices without changing the password. Existing password change also revokes sessions.

### Keyboard behaviour

The composer submits on Enter, keeps a newline on Shift+Enter, and ignores IME composition Enter/key-code 229. Native form validation still applies. A synchronous in-flight guard plus disabled input prevents repeated Enter/clicks from creating duplicate model requests.

## Known risks and unfinished operational work

1. Consent cannot recall a request already dispatched or erase Google's prior copies. Clearing a conversation removes this tab's memory only. Withdrawal controls future application calls; the in-flight request may finish.
2. Provenance labels and anonymity attestations are user declarations. The detector may miss names, medical details, unusual identifiers or obfuscated secrets, or reject an innocent long number. Do not use the unpaid demo for real confidential records.
3. Shared sandbox data is visible to other sandbox users. Upload only fictional data there. A personal account provides application-level owner isolation, not end-to-end encryption from the hosting operator.
4. There is no full self-service account erasure, automatic retention schedule, backup-erasure workflow, independently verified DPA/billing check, formal impact/transfer assessment, dedicated privacy-officer/contact process, MFA, email verification or independent audit. Referenced policy sources remain retained to preserve claim evidence; this must be reconciled with real deletion requests before production.
5. Hosting and provider terms, applicable regions, legal identity/contact details, incident handling, retention periods and sensitive/cross-border processing need the team's operational/legal review before a real-data launch. Public issue reports must not contain private content or keys.

Exact commands/results are in the latest section of `IMPLEMENTATION_REPORT.md` and `submission/evidence/privacy-*`. Earlier C+D/Gemini reports describe their historical releases; this permission design supersedes their outbound-data defaults.

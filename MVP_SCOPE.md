# Current acceptance and handoff extension

The normal owner path now supports explicitly consented SUCCESS/DECLINED sandbox methods, delayed signed provider outcomes, a guided `/test-lab`, fixed downloadable fixtures, source-declared public/test/private documents and owner case ZIPs. Operator simulate/replay remain privileged. No real transfer or generative LLM was added. See TEAM_HANDOFF.md and docs/19_COMPETITION_HANDOFF_RESEARCH.md.

# Current extension — financial participant, 2026-10-18

The user clarified that the supplied screenshot analyses the competition problem and asked for implementation along that analysis. The current app now includes reviewed local OCR, private source retention, CNY/VND ledgers, scheduled cash-flow projections, daily FX history/budget scenarios and grounded, read-only assistance. See docs/17_CHALLENGE_IMPLEMENTATION.md for the implementation matrix, measured evidence and concrete boundaries. STUDENT_FINANCE_GUIDE.md is the current usage guide. The earlier foundation scope below is retained as history.

# MVP upgrade — authorized scope

The user requested a usable MVP with working features and free API integrations. They confirmed no payment-provider sandbox account is available. Existing payment/receipt records must retain their accurate provenance; cosmetic relabelling cannot make them real settlements.

Delivered target for this iteration:

- Real email/password accounts, Argon2 password hashes, revocable HttpOnly cookie sessions, CSRF protection, login throttling, profile/password management and sign-out.
- User-owned invoice creation/edit/void, search/filter and no seeded data in new accounts. User-entered invoices are labelled as user-entered and unverified, not fictional school bills.
- Frankfurter v2 daily CNY/VND reference rates, cached in PostgreSQL with source/date/fetch time; persisted quote snapshots. Failure must not silently substitute a made-up rate. Reference rates are planning data, not an executable bank FX offer.
- User-uploaded policy PDF/text, private storage, text extraction, searchable excerpts with page/source citation. No canned insurance answers are presented as document-derived answers. Empty/unsupported evidence is explicit.
- Dashboard, invoice and history management, current account, usable empty/error/loading states; actual data for signed-in accounts.
- Preserve the verified mock payment engine as an explicitly selected sandbox flow. Without a merchant account/keys, beneficiary onboarding and a supported insurance corridor, no real payment integration can truthfully be enabled. No payOS local collection is substituted for cross-border insurer settlement.
- Execute regression/new tests, real upstream API smoke, browser flows, migration consistency, frontend lint/build, and update the report with measured results.

No account purchase, third-party message, public deployment or production funds transfer is authorized by this upgrade. Existing research/brief files are retained as historical context; this document and the latest user request describe the upgraded product scope.

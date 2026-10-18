# Agent policy and working agreements

## Source hierarchy

1. Safety and no-live-money rules in this file.
2. `docs/01_PRODUCT_SCOPE.md` and `docs/08_ACCEPTANCE.md` for product intent.
3. `contracts/openapi.yaml`, `database/schema.sql`, `fixtures/` for interfaces and sample data.
4. Others are advisory. When source proposal conflicts with hackathon timeline, ship core P0 and document the gap.

## Mandatory coding practices

- Implement, run, test, and fix. Do not leave placeholders or `TODO` in P0 paths.
- Before risky refactors run current tests; after changes rerun targeted and full tests.
- Keep provider integration behind `PaymentProvider` interface with `MockPaymentProvider` default.
- No LLM API or external payment account should be necessary to demo.
- UTC timestamps in DB/API with timezone; localize presentation for Vietnam.
- Currency precision: CNY 2 decimals, VND 0 decimals; no money floats; server calculates totals and ensures invariants.
- Use parameterized DB queries/ORM, migrations and transactional writes; do not trust client status, FX or amount.
- Idempotency for POST creation/confirmation; uniqueness of provider event IDs; concurrency-safe terminal transitions.
- Verify signature + bounded timestamp on mock-provider webhooks. Reject invalid signatures; never process unverified payloads.
- Restrict privileged demo simulate endpoint to a development-only operator session authenticated by server-validated `DEMO_OPERATOR_CODE`; do not grant operator role from client role alone; disable outside `DEMO_MODE`.
- Receipt must carry conspicuous text: `SIMULATED TRANSACTION — NO REAL FUNDS MOVED`.
- UI must distinguish source-grounded policy excerpts from synthetic data and guesses.
- Put fake-but-runnable credentials only in `.env.example` as documented *development placeholders*, never real keys. `.env` ignored.

## How to finish

- Provide commands for Windows PowerShell (user's local OS) and Unix shells.
- Report exact test runs and any failing tests; never assert unrun tests passed.
- Populate English submission artifacts for international track.
- Cite authoritative documentation with full URLs in the research docs, and label speculation.

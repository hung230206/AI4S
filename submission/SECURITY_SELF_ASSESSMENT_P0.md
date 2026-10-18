# Security self-assessment — local mock prototype

## Permission tiers

| Actor | Read own invoice/order/receipt | Confirm | Emit outcome | Read other students |
|---|---|---|---|---|
| Demo student | Yes | Own order, manual exact quote consent | No | No |
| Demo operator | No student API access | No | Request signed mock event in DEMO_MODE | No student API access |
| Mock provider worker | Outbox only | No | Signed events through webhook | No student session |
| Webhook | Matched payment intent only | Cannot override human consent | Applies verified transitions | No read API |

## Implemented controls and evidence

- Signed sessions expire after one hour; server loads the user and validates persisted role. Operator code uses constant-time comparison and is never sent to a student. Memory-only bearer tokens avoid cookie CSRF; CORS permits the local frontend origin.
- Invoice/order/receipt/event queries enforce ownership. Public DTOs remove internal student IDs, payload hashes and outbox fields. Client amount/currency/status injection is rejected by strict request DTOs.
- Decimal calculations, quote snapshots, database checks, explicit consent, idempotency hashes/snapshots and row locks protect amounts and repeated requests. Unique constraints add database enforcement.
- Raw-body HMAC, bounded delivery timestamp, event uniqueness, provider ID/amount/currency checks and irreversible terminal states protect receipt issuance.
- Durable mock outbox uses the actual webhook path, and worker retry safely deduplicates. API restarts do not lose queued outcomes. No live payment adapter is present; unsafe configuration fails startup.
- Sanitized audit/events contain action, actor tier, quote/total identifiers and simulation metadata. Signature headers, raw payloads, credentials, card data and passport data are not exported. Logs are not cryptographically tamper-evident against a privileged DB administrator.
- `.env`, database cluster, caches and browser traces are ignored. Source/evidence scan checks that generated local session/webhook/operator secrets were not copied into deliverables. Only synthetic fixtures are seeded.
- Receipt text: `SIMULATED TRANSACTION — NO REAL FUNDS MOVED` and `DEMO - NOT AN ACTUAL PAYMENT`, including print layout.

Final measured runs and counts are in `../IMPLEMENTATION_REPORT.md`; machine-readable backend/browser results and operation traces are in `evidence/`. These are executed tests, not certification or penetration testing.

## Dependency findings (2026-10-17)

`npm audit --omit=dev --json` reported **0 runtime vulnerabilities**. Full `npm audit` reported **5 high-severity package-chain findings** stemming from one unpatched `braces` stack-exhaustion advisory in the ESLint/Next lint toolchain. They are not payment endpoint dependencies. `npm view braces version` returned 3.0.3; the advisory lists no patched release. Do not run tooling against untrusted glob patterns/repositories; recheck before distribution. No forced downgrade to an incompatible Next lint major was applied. Source: https://github.com/advisories/GHSA-vfj7-8cjw-p6xm . Saved audit JSON records the actual findings. Backend dependency versions are recorded in `backend/requirements.lock.txt`; a Python vulnerability audit was not performed. License metadata is exported with dependencies; no claim of exhaustive legal review is made.

## Known risks and unfinished production requirements

1. Demo student sign-in is a local identity selector. No production identity provider, MFA, rate limiting, revocation service or real tenant onboarding exists. Operator code is local development access, not production access control. Keep servers loopback-only; no public hosting has been configured.
2. The native fallback database role is a local development superuser and its password is an explicit fake placeholder. Production would require a limited application role, secured secrets, TLS, backups, retention policy, recovery validation, monitoring and independent security review.
3. Outbox is an in-process mock dispatcher using durable PostgreSQL records and local ASGI transport. It demonstrates asynchronous provider semantics, not independent provider infrastructure, internet delivery reliability or financial reconciliation.
4. No licensed Chinese insurance payment corridor, beneficiary onboarding, KYC/AML, payment acceptance or legal settlement has been verified. No funds move. Fictional receipts prove neither payment nor coverage.
5. FX, fees, institution and policy are synthetic. Guidance is a small read-only deterministic FAQ with explicit source; no clinical/legal/coverage advice or general AI capability is claimed.
6. Desktop/mobile browser smoke checks are not a full accessibility audit. No production-scale performance or failover test was performed. Docker/Unix setup was not executed on this Windows host.
7. TestClient emits an upstream Starlette/httpx deprecation warning; tests still pass. Development tool advisory remains as described above. Existing fixture due date expires after 2026-11-01; generate a fresh synthetic fixture for later demonstrations.

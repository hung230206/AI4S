# CODEx TASK — build the application from this kit

You are the lead full-stack engineer. Work **inside this directory**, read `AGENTS.md`, `README.md`, all P0 docs, and `contracts/openapi.yaml` before coding. Execute the plan; don't stop after writing more plans. Create working, tested code.

## Deliverables

1. Backend: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PostgreSQL, pytest.
2. Frontend: Next.js App Router, TypeScript, Tailwind (simple polished responsive UI); complete P0 screens.
3. Mock Payment Provider, backend-controlled transitions, signed asynchronous webhook events, idempotent processing and event log.
4. Docker Compose Postgres plus documented local setup; `.env.example` only, no secrets committed.
5. Seed scenario in CNY / VND, deterministic FX with an unambiguous `DEMO_RATE` badge.
6. Tests including double-click, duplicate/out-of-order webhook, expired quote, tampered amount, ownership and invalid signature.
7. `submission/` outputs filled with actual architecture, security self-assessment and real test output; optional scripts for generating evidence.
8. A final `IMPLEMENTATION_REPORT.md`: what is completed, actual commands and pass counts, unresolved limitations, screenshots/video instructions, chosen demo access method.

## Engineering order

- **Step 0:** Inspect contract/docs; note ambiguities in `IMPLEMENTATION_NOTES.md` and choose the smallest safe interpretation; don't ask clarifications except absolute blockers.
- **Step 1:** Create workspace skeleton, compose DB, dependencies, startup docs.
- **Step 2:** DB + migrations + synthetic fixtures/seed; satisfy schema invariants.
- **Step 3:** FastAPI with typed DTOs, consistent errors, auth/session, quote and order endpoints.
- **Step 4:** Mock provider and secure events (signature, timestamp, replay, duplicate event ID), state machine with transactions/row locks.
- **Step 5:** End-to-end responsive UI with all P0 pages, clear simulation badges, loading/errors and confirmation.
- **Step 6:** Unit/integration tests and browser smoke test; resolve all failures.
- **Step 7:** Optional insurance guidance and Airwallex adapter interface only if time permits and core is verified.
- **Step 8:** Update docs/submission artifacts; provide demo guide and concise final handoff.

## Hard requirements

- `PAYMENT_PROVIDER=mock`, `DEMO_MODE=true`, `ALLOW_REAL_PAYMENTS=false` as default. Never implement production money transfer behind this brief.
- The only authority for invoice amounts is backend DB; UI cannot submit an amount to pay.
- All money calculations use decimal arithmetic with explicit rounding. No floats for currency.
- Confirmation must be an explicit human action, tied to the exact quote and amount viewed; AI is read-only/advisory.
- A redirect, browser callback or frontend value must never by itself mark an order as succeeded.
- A fake result must never be presented as settled, legally valid or paid to a university/insurer.
- Mock provider must be the **source of payment events**; even the demo operator action cannot arbitrarily rewrite order status.
- Do not silently replace the underlying Chinese insurance payment problem with a working local-Vietnam real-cash checkout.
- All dependencies used must have appropriate licenses; don't embed copied copyrighted insurance texts.

## Definition of success

Run the documented stack locally, demonstrate one successful payment, one failed payment, one expired quote and one duplicate webhook, and show passing tests and an exportable operation log. If an optional API requires external credentials, the P0 app still works without them.

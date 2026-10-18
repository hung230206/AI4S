# 06 — Test cases and evidence requirements

## Automated test categories (must implement)

### Money / quote

- 800 CNY * synthetic 3,500 VND/CNY = 2,800,000 VND.
- 1.5% + 5,000 VND produces 47,000 VND fee and 2,847,000 VND total.
- All math with `Decimal`, no rounding drift, zero/negative request rejected.
- Expired quote, invoice mismatch, quote belonging to another user are rejected.

### State machine

- Without explicit consent, payment remains `AWAITING_CONFIRMATION`.
- Good consent -> `PROCESSING`; verified good event -> `SUCCEEDED`; simulated receipt exists.
- Verified failure event -> `FAILED`; no paid receipt; new order required for retry.
- User cancel before confirming -> `CANCELLED`.
- Terminal state cannot return to earlier state.

### Security / adversarial

- Client cannot change amount/currency to underpay.
- Repeated create/confirm idempotency requests don't create additional charges.
- Concurrent confirms -> one provider attempt.
- Duplicate webhook ID -> only one payment state transition.
- Bad signature -> 401; old timestamp -> 401; mismatch currency or amount -> rejected.
- Out-of-order event after terminal state -> ignored/audited; no rollback.
- Student A cannot read B's orders/receipt (404 or 403 consistently).
- Non-operator cannot run simulator; simulator disabled unless `DEMO_MODE`.
- Secrets, sensitive info and full webhook payload absent from logs.
- Explicit request cancellation cannot fake provider cancellation after processing.

### UI

- All flows work by keyboard, readable errors, responsive mobile and desktop.
- Synthetic/FX/receipt labels are conspicuous and cannot be confused with real payment.
- Loading/retry/polling and empty histories handled.

## Evidence capture for submission

Codex should create `submission/evidence/` with safely redacted JSON logs, test outputs and screenshot capture instructions, NOT invented screenshots or fabricated passing counts. Give a reproducible command (e.g. `make demo-evidence` or documented Python script) for judge replay.

## Fixture-driven scenarios

`fixtures/payment_scenarios.json` is an acceptance checklist, not automatically executed; Codex should turn each item into pytest/integration tests and record the outcome.

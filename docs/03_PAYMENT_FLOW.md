# 03 — Payment workflow and state machine

## End-to-end steps

1. Student signs in to local demo account.
2. `GET /invoices` => seeded synthetic bill, explicitly no real beneficiary.
3. `POST /quotes` => server calculates fixed FX demo quote. **No payment** yet.
4. `POST /orders` with invoice/quote IDs and `Idempotency-Key` => `AWAITING_CONFIRMATION`.
5. Review screen displays immutable breakdown; user clicks **Confirm simulated payment**.
6. `POST /orders/{id}/confirm` with matching quote + explicit consent and idempotency header. Server records consent, creates mock provider intent and moves `PROCESSING`.
7. Mock provider operator scenario sends signed event to `/webhooks/mock`. Backend checks signature, timestamp, event ID, status transition, ownership and amount equality.
8. `SUCCEEDED` produces a simulated receipt; `FAILED` produces a retry-new-order guidance; `CANCELLED` is possible only before provider processing.
9. Event trace and history are available; export judge-safe log.

## Allowed transitions

```text
AWAITING_CONFIRMATION --> PROCESSING
AWAITING_CONFIRMATION --> CANCELLED
AWAITING_CONFIRMATION --> EXPIRED  [quote expired before confirm]
PROCESSING --> SUCCEEDED
PROCESSING --> FAILED
```

No other transition is valid. For retries after failure create a **new** order/quote rather than resurrecting a terminal order. `DRAFT/QUOTED` are concepts for invoice/quote, not persisted order statuses in MVP.

## FX and fee example (ALL SYNTHETIC)

```
invoice_amount         = 800.00 CNY
DEMO VND per 1 CNY     = 3,500 VND
converted_subtotal     = 2,800,000 VND
variable_fee_rate      = 1.50%
variable_fee           = 42,000 VND
fixed_fee              = 5,000 VND
amount_due             = 2,847,000 VND
quote_validity         = 10 minutes
```

Round VND fee to nearest integer using `ROUND_HALF_UP`. Quote expires at UTC timestamp. Rate is static synthetic educational input and **not** a live exchange rate.

## Error codes required

- `QUOTE_EXPIRED` (409)
- `INVOICE_NOT_PAYABLE` (409)
- `CONSENT_REQUIRED` (422)
- `QUOTE_MISMATCH` (409)
- `ORDER_STATE_INVALID` (409)
- `EVENT_BAD_SIGNATURE` (401)
- `EVENT_STALE_TIMESTAMP` (401)
- `EVENT_DATA_MISMATCH` (409)
- `ORDER_NOT_FOUND` (404)
- `FORBIDDEN` (403)
- `PROVIDER_TEMPORARILY_UNAVAILABLE` (503)

**Idempotency contract:** identical request with identical `Idempotency-Key` returns same resource; conflicting payload with same key yields 409. Expired quote cannot be confirmed even after prior successful `GET`.

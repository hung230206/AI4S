# 04 — API implementation guide

The authoritative machine-readable draft: `contracts/openapi.yaml`. Codex may expand responses/schemas but must preserve endpoint semantics.

## Routes

| Verb | Route | Purpose | Access |
|---|---|---|---|
| POST | `/api/v1/demo/session` | Local-only demo sign-in / operator requires DEMO_OPERATOR_CODE | Local only |
| GET | `/api/v1/health` | Health | Public |
| GET | `/api/v1/invoices` | List own synthetic invoices | Student |
| GET | `/api/v1/invoices/{invoice_id}` | Invoice detail | Student |
| POST | `/api/v1/quotes` | Create immutable time-limited FX quote | Student |
| POST | `/api/v1/orders` | Create order from invoice/quote | Student + Idempotency-Key |
| GET | `/api/v1/orders` | History | Student |
| GET | `/api/v1/orders/{order_id}` | Current status & breakdown | Owner |
| POST | `/api/v1/orders/{order_id}/confirm` | Explicit user consent | Owner + Idempotency-Key |
| POST | `/api/v1/orders/{order_id}/cancel` | Cancel only if awaiting confirmation | Owner |
| GET | `/api/v1/orders/{order_id}/events` | Sanitized timeline | Owner |
| GET | `/api/v1/orders/{order_id}/receipt` | Simulated receipt if success | Owner |
| POST | `/api/v1/demo/orders/{order_id}/simulate` | Trigger mock-provider signed event | Operator, demo only |
| POST | `/api/v1/webhooks/mock` | Mock-provider event inbound | HMAC verified |

## General conventions

- JSON body, UTC ISO8601 `Z` timestamps, stable UUID identifiers.
- API errors: `{ "error": {"code": "QUOTE_EXPIRED", "message": "...", "request_id": "..."} }`.
- CNY: decimal string `"800.00"`; VND: decimal string `"2847000"`. Avoid JSON numeric floats for money.
- `Idempotency-Key` 8–128 chars; persist `(user_id, endpoint, key, body_digest, response/reference)`.
- The webhook endpoint validates HMAC over **raw bytes**, timestamp and shared secret; it must never authorize an arbitrary browser-provided status change.
- Demo operator session separate from student's session and visibly labeled privileged. Never expose simulation controls in production build.

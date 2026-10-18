# 05 — Database notes

Start from `database/schema.sql` for logical structure. Write an Alembic initial migration matching it; don't call the raw schema and a mismatched ORM both authoritative.

## Key invariants

- `insurance_invoices` holds amount and payee verified at the server. In seeded data they are **fictional** and `source_type=SYNTHETIC`.
- `fx_quotes` carries a snapshot of demo rate and fees and expiry. Old quote must not be edited.
- `payment_orders` holds user, invoice, quote, status, snapshot of amount, consent time and idempotency key.
- `payment_transactions` maps mock provider payment ID to order. One provider attempt per order for P0; failed order retry requires new order.
- `payment_events.external_event_id` globally unique to avoid duplicate state changes.
- `payment_receipts` only for successful, verified processing; receipt `is_simulated=true` required.
- `audit_logs` logs actor, action and safe metadata without passport/card content.

## Money

Use `Numeric(20,2)` for CNY invoices; `Numeric(20,0)` for VND quote/order total, never floating point. Store FX rate as `Numeric(20,6)`. Fee rounding is `ROUND_HALF_UP`. Consider integer minor units at the provider adapter boundary; internal API uses decimal strings. Confirm currency exponent before minor-unit conversion.

## Schema deployment

Use a local Docker Postgres database by default. Cloud Supabase is optional and should never be a blocker. Provide seed script that is repeatable (upsert). No RLS reliance with privileged DB connections; authorization in app service is mandatory.

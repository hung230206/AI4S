# Implementation decisions

## Current MVP revision

The latest user request expanded the product beyond a seeded demo. Registered accounts now use Argon2id passwords, revocable HttpOnly cookie sessions and CSRF; they work independently of DEMO_MODE. New accounts start empty. USER_ENTERED invoices use the connected Frankfurter reference service and zero default application fees. The old identity selector/fixed rates remain only for explicitly selected sandbox fixtures. Private PDF/text upload and extractive policy search replace the canned FAQ in the main UI. Mutating database dependencies finish their transaction before an HTTP response is sent (`scope="function"`). Signup throttling permits 20 attempts per IP per 15-minute window; login throttles remain 10 per account/IP and 10 per IP per window. See MVP_SCOPE.md, docs/14_MVP_APIS_AND_PROVENANCE.md and the latest report for current behavior. The original decisions below describe the initial P0 stage.

- Work stays in this extracted kit directory. The supplied files are implementation requirements, not authorization to publish, transfer money, or contact external parties.
- PostgreSQL is authoritative. Tests use a separate PostgreSQL database, including real row locks and concurrent requests; no SQLite substitute.
- Local sign-in is deliberately a demo identity selector. Operator requires the environment code; tokens stay in browser memory. Sessions and simulation are disabled outside demo mode. Bind services to loopback.
- The exact quote ID binds consent to its immutable server total. Confirmation additionally accepts `expected_total_vnd` to reject stale/mismatched review screens. No client amount can set an order total.
- Cancellation is a student action only before a provider intent exists. The contract limits provider outcomes to success/failure; provider cancellation is therefore unnecessary before processing.
- A persistent mock-provider outbox is delivered asynchronously to the actual webhook ASGI route. Delivery uses signed raw bytes and retries; restarting the API resumes pending events. A separate operator panel controls outcomes, never order fields.
- Idempotency stores the original response snapshot. A replay returns that snapshot even after later order transitions; GET returns current state.
- At most one awaiting, processing, or succeeded order per invoice. Expired awaiting orders are closed when accessed or before a new quote/order. Seed is repeatable and preserves fixture due dates.
- `database/schema.sql` remains the supplied logical reference; the versioned Alembic migration is the deployment authority, extending the logical schema with response snapshots and the mock-provider outbox.
- P1 provider sandbox remains disabled; do not invent an Airwallex API. Topic selection remains a team decision.

# 13 — Threat model and mitigation

| Threat | Impact | Mandatory mitigation | Test |
|---|---|---|---|
| Browser modifies invoice or amount | underpayment/fraud | DB-authoritative amount, quote snapshot | `client_tamper_amount` |
| Double-click confirm | duplicate charge | idempotency key + DB unique constraint + lock | `confirm_twice` |
| Forged provider success | false paid status | HMAC verification + timestamp + event ID + amount match | `invalid_hmac` |
| Replayed provider event | double receipt | unique event ID and terminal lock | `duplicate_event` |
| Late failure after success | state corruption | irreversible terminal state | `out_of_order_after_success` |
| Unauthorized student reads data | privacy leak | scoped ORM queries / ownership check | `cross_user_access` |
| Quoted price expired | wrong FX | expiry validation at confirm | `expired_quote` |
| Demo secrets in code | compromised accounts | `.env` exclusion and static scan | `secrets_scan` |
| Privileged simulator public | payment spoof | DEMO_MODE + operator role + no deployment by default | `simulate_forbidden` |
| Misleading UX | false insurance claim | labels and simulated receipt watermark | UI verification |

## Known regulatory gap

No verification of lawful payment corridor for a real Chinese insurer. This MVP is technical research and payment simulation only; compliance self-assessment must explicitly list this as unresolved.

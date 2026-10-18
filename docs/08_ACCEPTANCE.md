# 08 — Acceptance criteria / Definition of done

## Must pass to consider P0 complete

- [ ] Fresh clone + README steps launch Postgres, backend and frontend on Windows.
- [ ] Seed makes one synthetic CNY insurance invoice and two distinct demo roles.
- [ ] Student can view invoice and demo quote and see correct 2,847,000 VND total.
- [ ] Student must explicitly confirm; no automatic payment by AI or page load.
- [ ] Backend changes order to PROCESSING, operator triggers signed simulated provider event.
- [ ] Success -> SUCCEEDED + uniquely identified simulated receipt.
- [ ] Failure -> FAILED, no successful receipt and safe retry instructions.
- [ ] Cancellation prior to confirmation works; expired quote cannot be confirmed.
- [ ] Duplicate idempotency key and webhook ID do not create duplicate charges/receipts.
- [ ] Bad signatures, mismatched webhook amount and ownership attacks are rejected.
- [ ] All money calculations are server-side Decimal, amounts not trusted from client.
- [ ] Test command exits 0, frontend build exits 0, no secret or real personal data in repository.
- [ ] Operation evidence script or instructions reproduce safe logs and demo sequence.
- [ ] English architecture/security/demo/submission documents filled with actual implemented behavior.

## Optional — only if core is stable

- [ ] Source-grounded insurance policy guidance.
- [ ] Airwallex Sandbox adapter implemented and tested with user-provided sandbox account ONLY, no production.
- [ ] English UI switch.

## Not acceptable

- Hardcoded frontend status `SUCCESS` after arbitrary button press.
- Sending money or attempting card charging in production.
- Claiming demo receipt is insurance coverage or legal payment confirmation.
- Describing an Airwallex cross-border insurance remittance as compliant/supported without provider verification.
- Tests/documentation that only report success without actual execution.

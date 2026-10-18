# 01 — Product requirements / PRD

## Context

The original uploaded proposal selected Topic D and described an AI assistant for Vietnamese students learning host-country health insurance policies, and a feature to help pay annual insurance premiums and mandatory medical service fees. Team is now investigating **both Topic C and D** before choosing a single registration topic. Current engineering ownership: payment and FX module.

Official topics:
- **C: Cross-border & Student Finance Assistant** — financial pain points of international students, including remittance, tuition, multi-currency management.
- **D: Insurance Assistant** — policy Q&A, coverage gaps, claims guidance.

## User story

As a Vietnamese student preparing to study in China, I want to see a transparent insurance payment request in CNY, its simulated VND equivalent and fee, choose to confirm or cancel, and track evidence of a simulated transaction without being misled that actual insurance was paid.

## Required P0 capabilities

**US01 — View invoices**: Show at least one seeded synthetic insurance invoice with country, institution label, receiver, amount, currency, due date and provenance badge `SYNTHETIC DEMO DATA`.

**US02 — Obtain quote**: Generate a persisted, short-lived server quote, showing CNY principal, demo VND/CNY rate, converted subtotal, percentage fee, fixed fee, total VND and expiry. A quote from an expired invoice is rejected.

**US03 — Create payment order**: User creates an order from an active invoice + unexpired quote; server checks ownership and computes all amounts. Reuse the same idempotency key to return the same order.

**US04 — Consent**: User explicitly confirms an exact quote ID and total; backend logs consent actor/time and triggers mock provider asynchronously. No auto-consent by AI.

**US05 — Mock provider**: A test-only operator can choose provider outcome `SUCCEEDED`, `FAILED` or, before processing, `CANCELLED`; simulation creates a signed event that is processed through the same webhook pathway as normal status updates.

**US06 — Trace & receipt**: UI displays pending/processing/terminal states, history, timestamps, sanitized events. Receipt appears ONLY after verified success and is watermarked `SIMULATED`.

**US07 — Failure/safety**: Handle timeout, expired quote, bad input, insufficient demo funds (optional), duplicate click, forged event, duplicate event, reversed event order, stale update, unauthorized access and provider outage gracefully.

**US08 — Responsive UX**: Mobile and desktop layouts. No QR code implying real payment. Clear status + demo badges on every payment view.

## P1 if time remains

- Read-only insurance help: answer only from packaged source-labelled synthetic policy; show policy citation. Use deterministic templates by default; LLM optional.
- Airwallex Sandbox adapter scaffold; only functional where account/permissions support it and API endpoint definitions are verified from provider docs.
- Export CSV/JSON of sanitized events for judges.

## Explicitly out of scope

Live cross-border remittances, bank onboarding/KYC, real premium billing by Chinese schools, direct AliPay/WeChat integration, refunds, chargebacks, official insurance claims adjudication, storing card PAN/CVV/passport data, real FX quotations, legal/compliance certification, claims of guaranteed bank/regulator support.

## Non-functional requirements

- Repeatable startup on Windows with local Postgres; no paid API dependency.
- Server-to-server verification and audit logs; deterministic reproducible tests.
- P95 local response <1s for non-provider endpoints is a stretch goal, not a guarantee.
- All screens accessible via keyboard; clear empty/error states and no color-only status cues.

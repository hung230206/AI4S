# 12 — AI boundaries and policy guidance

Core demo must work **without any LLM**. If a financial agent is added:

- Agent can call **read-only** tools `list_demo_invoices`, `explain_quote`, `explain_payment_status`, `search_demo_policy`.
- Agent may suggest `create_quote` but must not call `confirm_payment`, provider transition, payout API or update invoice totals.
- Only authorized human consent through API can progress payment.
- For Topic D, answer insurance questions only from a cited, available policy snippet. If evidence insufficient, say so.
- Label `fixtures/demo_policy.md` as fictional to avoid misleading medical/insurance advice.
- AI output is advisory, never an account balance, FX source or binding legal interpretation.

Possible separate LLM via OpenAI or local model after P0; do not create mandatory network dependency or commit API keys.

# 09 — Sources, provenance and research caveats

## A. Information directly from original team's `.docx`

Attached: `reference/NC_Tham_Quyen_Shenzhen_2026_original.docx`.

Original proposal says:
- Declared Topic D `Insurance Assistant`.
- Vietnamese international students learning host-country insurance; example markets include China, Japan, Korea and Taiwan.
- System should retrieve and explain policy clauses, limits and claims procedures using NLP/LLM.
- Proposed assistance with **annual insurance premiums and mandatory healthcare-related fees**.
- Suggested account/card/wallet links and payment request routing in diagram.

**Not specified in the proposal:** exact payee, account origin, fee schedule, valid merchant acquirer, licensed cross-border payment rail, actual payment API, operational credentials, supplier contracts, acceptance criteria, or settlement legal eligibility.

## B. Official competition (checked 2026-10-17)

Competition rules PDF: https://www.pol.cmu.ac.th/public/blog/attachment/download/7a51866a-4cee-42b5-9187-fa4e1f4df411
- Topic C: Cross-border & Student Finance Assistant; Topic D: Insurance Assistant.
- Registration asks each team to **choose one** topic; the team has not yet decided whether C or D will be the official submission topic.
- Non-on-chain topics may submit simulated-account/sandbox operation logs + demo video as execution evidence.
- Evaluation: completion 40%, security/compliance 30%, innovation/interaction 30%.
- English is the official submission/presentation language.
- Deadline: 2026-10-20 23:59 China Standard Time = 2026-10-20 22:59 Vietnam time.

## C. Official provider documentation (checked 2026-10-17)

Airwallex sandbox: https://www.airwallex.com/docs/developer-tools/sandbox-environment
Sandbox payouts: https://www.airwallex.com/docs/developer-tools/sandbox-environment/payouts
Transfer simulations: https://www.airwallex.com/docs/api/2024-09-27/simulation/transfers
Airwallex China payout requirements: https://www.airwallex.com/docs/payouts/payout-network/china
- Sandbox supports test activity without real money, including transfer-status simulations.
- **CRITICAL:** local CNY payouts to mainland China have specific declared-trade/e-commerce goods use cases; insurance premiums are NOT shown as a supported use case in these documents. A working payout sandbox does NOT establish permission to pay Chinese student insurance premiums in production.
- Payment acceptance, FX conversion and payout are different product capabilities requiring separate verification.

## D. Explicit design assumptions created for hackathon demo

- Synthetic institution label: `Demo International University` (NOT a real entity).
- Synthetic invoice number: `DEMO-CN-INS-2026-001` and fee 800.00 CNY (demo amount; **not a claim about any university's current rate**).
- Deterministic demonstration FX rate 1 CNY = 3,500 VND (**not live**); 1.5% variable fee and 5,000 VND flat fee (**not a provider price quote**).
- Payment provider is an in-process/mock HMAC event simulator, NOT a licensed remittance provider.
- Insurance policy file is wholly fictional and intended for UI/logic testing, NOT medical/financial advice.

Codex must maintain a visible boundary between A/B/C (documented evidence) and D (synthetic demo assumptions). Do not silently convert the mock into a live payments integration.

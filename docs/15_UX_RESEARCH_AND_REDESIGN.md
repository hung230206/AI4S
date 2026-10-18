# UX research and implemented redesign

Research and implementation date: 2026-10-18 (Asia/Bangkok).

The user reported that the existing interface did not explain how to use the product and requested research into comparable systems plus an implementation. This review examined publicly available first-party flows and documentation, without accounts, private dashboards or transactions. It does not claim equivalence to a licensed payment or insurance service.

## Comparable systems

| Source inspected | Observed pattern | Applied in Bảo An |
|---|---|---|
| Flywire, https://pay.flywire.com/ and https://pay.flywire.com/how-it-works | A clear initial action and a numbered journey covering selection, details, payment and tracking; help is accessible beside the payment journey | Task-focused home page, persistent numbered invoice → conversion → optional trial → tracking steps, a help button on every authenticated page |
| Convera GlobalPay for Students, https://students.convera.com/ | Student payment entry, payment details, delivery and tracking are explained as a sequence; tracking is a distinct destination | A continue-tracking action for an existing trial, explanatory history empty state, and a distinct optional trial section after conversion |
| Wise Help Centre, https://wise.com/help/articles/2596987/how-can-i-send-money-from-my-wise-account | Select a send action, enter recipient and amount, then review details before confirming; visible fees and rate are reviewed before sending | Keep server-calculated quote breakdown visible before optional consent; clearly explain what viewing a quote does and what creates an order |
| SafetyWing member guide, https://intercom.help/safetywing/en/articles/9916732-member-guide-to-remote-health-global | Member tasks are separated into coverage, documents/claims and tracking; instructions say what to prepare and what happens next | Insurance-document workflow has its own entry, upload → keyword → citation instructions, file preparation help, and an explicit explanation that extraction does not decide coverage |

These observations informed our design choices. The conclusion that two task choices and contextual guidance will improve this particular product is a design inference, not a measured usability result. We did not conduct interviews or a controlled usability study. No source logos, code, illustrations, policy text or exact screen layouts were copied.

## Problems addressed

1. The previous home screen devoted substantial space to generic promotional content; new users could not see a clear starting task.
2. “Invoice”, conversion, payment and policy lookup appeared as peer features without explaining how they relate.
3. Technical operator controls competed with student navigation.
4. Viewing a reference conversion could be mistaken for starting a payment; an empty history was unexplained.
5. A processing state did not clearly tell a tester whether to wait or click again.

## Delivered interaction

- The home screen starts with two concrete tasks: prepare a VND budget from a CNY invoice, or read insurance terms from an uploaded document. Each says what input is needed and links into the existing working workflow.
- A native modal introduces these choices on the first authenticated visit in each browser, per account. It has Skip/Close/Escape, native focus containment, focus restoration, and a persistent help trigger. Dismissal is a browser preference only; it does not change the account or payment state. Browser storage being unavailable does not prevent closing it.
- The help trigger opens the topic relevant to invoices, documents or payment history. Users can switch topics or open a working page directly.
- Invoice forms are grouped into required fee details and optional provenance. Inline expandable help explains issuer, recipient and source documents.
- Invoice detail, conversion and tracking show numbered progress. Conversion explicitly says a user-entered estimate can be viewed without creating a payment. Optional sandbox consent remains unchecked and server-validated.
- Document pages explain accepted files, the independent upload/search/citation workflow and how to choose search terms.
- Empty history explains why a quote is absent. Pending trials have a continue action and a statement that processing updates automatically when the operator sends a result.
- Operator access remains authenticated by its existing server-side mechanism; only its navigation location moved to a secondary operator section.
- Existing account, document, monetary precision, consent, provenance and signed-event controls remain in place. No new payment provider, live transaction, OCR, AI-generated insurance answer or public hosting was introduced.

## Reproduction and evidence

Windows PowerShell, from `frontend/`:

```powershell
npm run lint
npm run build
$env:PLAYWRIGHT_BASE_URL = 'http://192.168.1.14:3000'
npm run test:e2e
```

Unix, replacing the host IP:

```sh
npm run lint
npm run build
PLAYWRIGHT_BASE_URL=http://192.168.1.14:3000 npm run test:e2e
```

New browser cases cover initial help, narrow-screen overflow, focus containment, Escape/skip, remembered dismissal, reopening, task links, contextual topics, quote-only behavior and existing invoice/document functionality. Screenshots are saved to `submission/evidence/screenshots/ux/`. Exact final outcomes are recorded in IMPLEMENTATION_REPORT.md.

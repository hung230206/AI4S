# Task-based navigation and page introductions

Local UX update, 20 October 2026. No commit, push or deployment is part of this change.

## User journey

The homepage starts with three independent needs: pay a fee, understand insurance, or manage living money. Unfinished invoices and pending sandbox payments appear below. The sidebar keeps the main tasks; exchange-rate analysis remains available from the budget page, and insurance documents from the insurance page. The global assistant and manual header guide remain available.

An invoice detail page combines its saved information, optional planned expense and server-reported sandbox payment status. Viewing a quote does not create a payment. Payment completion offers a demo receipt and a return home; a linked policy is optional. Medical claim preparation belongs to the insurance workflow and is not a mandatory step after paying a fee. Sandbox payments do not transfer money, activate a policy, submit a claim or automatically post an actual expense.

Budget labels use available money, upcoming income/expenses and estimated remaining money. Business calculations, consent, authentication, signatures, ownership and idempotency are unchanged.

## Brief page introductions

A native modal explains each supported screen in one or two sentences when its pathname changes. Changing a tab, filter, language or polled business status does not reopen it. Unknown/public routes do not display an invented introduction. It waits if another native modal is already open.

- **Got it / Escape:** close the current introduction. It will appear on the next visit unless hidden.
- **Don't show this introduction again:** saves dismissal for this introduction only when closed. Other page introductions remain enabled. Dynamic invoice/payment/claim pages share their respective introduction type, rather than saving record IDs.
- **Account → Help while using the app:** restore hidden introductions, or disable/enable automatic introductions globally. The header guide remains available even when introductions are disabled.

Preferences are local to the current browser and account; another device is independent. No permission is granted by dismissing help. Local storage failure falls back to in-tab preferences. Vietnamese, English and Chinese copy, keyboard cycling, Escape, focus return, narrow-screen layout and dark theme are supported.

## Reproduce checks

Windows PowerShell (from repository root):

```powershell
Push-Location frontend
npx.cmd playwright test tests/task-ux.spec.ts --reporter=list
$env:RAG_BROWSER_ADMIN_CREDENTIALS=(Resolve-Path ../.local/rag-admin-test.json).Path
npx.cmd playwright test --reporter=list
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
Pop-Location
```

Unix shell:

```sh
cd frontend
npx playwright test tests/task-ux.spec.ts --reporter=list
RAG_BROWSER_ADMIN_CREDENTIALS=../.local/rag-admin-test.json npx playwright test --reporter=list
npm run lint
npx tsc --noEmit
npm run build
```

The existing frontend/API must be running on ports 3000/8000 against the local database using QA accounts, with the existing ignored test-admin credential file. Never reset the user's database to run these checks. Dedicated UX tests use the sandbox session and fictional read-only response fixtures; the full regression includes real local API flows and the signed mock-provider workflow. Validation results are recorded in IMPLEMENTATION_REPORT.md and submission/evidence/task-ux-*.txt. Screenshots are under submission/evidence/screenshots/task-ux/.

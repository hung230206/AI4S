# Bảo An — Vietnamese demo frontend

Current routes also include `/copilot` (grounded assistance), `/finance` (CNY/VND ledger and scheduled cash flow) and `/rates` (reference history and budget sensitivity). Invoice/source review and scanned-policy OCR are integrated into the existing forms. The frontend Tesseract.js package also supplies the API's local Node OCR worker; install Node packages before running OCR on the API host. Usage: root STUDENT_FINANCE_GUIDE.md. Latest verification: 13 full browser flows, with three targeted reruns after language selection changes.

Next.js App Router + TypeScript + Tailwind/CSS. Run `npm ci` then `npm run dev`, with the API on port 8000. Open http://localhost:3000. Run `npm run lint`, `npm run build` and `npm run test:e2e` (Chrome, backend/frontend running). Full instructions and evidence are linked from root RUNBOOK.md and IMPLEMENTATION_REPORT.md.

Registered accounts use a revocable HttpOnly cookie and a CSRF token held in memory. Only the optional sandbox/operator bearer sessions use the original in-memory mechanism. All outcomes come from the API. User-entered invoices and uploaded policies retain their actual user-supplied provenance; Frankfurter reference rates retain source/date. Payment execution and its receipts remain explicitly sandbox because no provider account is connected. Operator controls are hidden in production builds.

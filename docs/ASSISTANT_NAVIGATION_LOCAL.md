# Assistant navigation confirmation (local implementation)

The assistant now proposes an application page when it recognises a user's app task. A modal asks **Open page / Stay here**. Receiving a reply never changes the URL automatically. Stay here and Escape dismiss the proposal, preserve the chat and return focus to its composer. Open page minimises the assistant and performs client-side navigation; reopening the assistant preserves the conversation.

| Example request | Destination after confirmation |
| --- | --- |
| hiện tại có những giao dịch nào đã thành công | `/history?status=SUCCEEDED` |
| Tôi muốn xem giao dịch thất bại | `/history?status=FAILED` |
| Tôi muốn thêm hóa đơn | `/invoices/new` |
| Cho tôi xem hóa đơn | `/invoices` |
| Tôi muốn thanh toán học phí | `/invoices` (review first) |
| Tôi cần quản lý ngân sách | `/finance` |
| Mở tỷ giá | `/rates` |
| Tôi muốn tải tài liệu | `/assistant` |
| Tôi cần quản lý bảo hiểm | `/insurance` |
| Mở cài đặt tài khoản | `/account` |

Vietnamese, English and Chinese task phrases are supported by bounded local rules. Concept definitions, policy/legal evidence questions, how-to questions and negative requests retain the existing chat routes. Unrecognised tasks do not gain navigation privileges. This change does not implement chat-based transaction listing, train a classifier, invoke an extra model, create invoices or execute payments. Existing execution guards remain enforced.

`backend/app/assistant_navigation.py` maps recognised intents to fixed routes. Chat navigation responses contain `navigation: {href, title, reason}`, `provider: RULES`, `method: NAVIGATION_SUGGESTION`, empty citations and empty executed actions. Navigation requires the existing authenticated student dependency, but sends no question, conversation or account context to an external service. The preview endpoint marks this path as local, with no recipient or external evidence. Existing assistant-opening consent remains required by the UI.

The client validates navigation proposals and action buttons against an exact page allowlist. Only a single recognised `status` query on History is allowed; external URLs, protocol URLs, arbitrary queries and admin pages are rejected. Legacy workflow action buttons also ask confirmation when clicked. Only explicit `navigation` replies open the popup automatically. Permission withdrawal clears outstanding confirmation. The modal initially focuses Stay here, preventing the Enter used to send a question from approving navigation. It uses native dialog focus containment and accessible labels in all three languages.

History's status filter now uses validated URL state. Confirming a second status while already on History updates the filter correctly. Changing the select updates the URL, and browser navigation restores the corresponding filter. Normal owner-scoped order loading and CSV export remain unchanged. Search-parameter usage is wrapped in Suspense for the production build.

## Reproduction

Start the existing local API on port 8000 and frontend on port 3000. No external model key is needed for these navigation tests. Use the existing safe test database configuration (database name ending `_test`). The full browser suite additionally needs the existing mock-provider worker, OCR runtime and local RAG test-admin credentials.

PowerShell, from the repository root:

```powershell
cd backend
.venv/Scripts/python.exe -m pytest tests/test_assistant_navigation.py tests/test_study_assistant.py -q
cd ../frontend
npx.cmd playwright test tests/assistant-navigation.spec.ts --reporter=list
npm.cmd run lint
npx.cmd tsc --noEmit
npm.cmd run build
```

Unix, from the repository root:

```sh
cd backend
.venv/bin/python -m pytest tests/test_assistant_navigation.py tests/test_study_assistant.py -q
cd ../frontend
npx playwright test tests/assistant-navigation.spec.ts --reporter=list
npm run lint
npx tsc --noEmit
npm run build
```

Evidence is under `submission/evidence/navigation-*` and `submission/evidence/screenshots/assistant-navigation/`. Actual run totals are recorded in the latest section of `IMPLEMENTATION_REPORT.md`. This implementation is local only; no commit, push or deployment is part of this change.

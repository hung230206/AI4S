import {test, expect, type Page} from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import {randomUUID} from "node:crypto";
import {dismissWelcome} from "./guide-helper";
const root = path.resolve(__dirname, "../..");
const credentialPath = process.env.RAG_BROWSER_ADMIN_CREDENTIALS || path.join(root, ".local/rag-browser-admin.json");
const creds = () => JSON.parse(fs.readFileSync(credentialPath, "utf8")) as {email: string; password: string};
const text = "Self-authored fictional outpatient specialist benefit has an annual limit of CNY 7,654. Hospital invoices and signed claim forms are required. This is software test data, not actual insurance cover.";

async function loginAdmin(page: Page) {
  const admin = creds();
  await page.addInitScript(() => localStorage.setItem("baoan.mode", ""));
  await page.goto("/admin/rag");
  await page.getByLabel("Email", {exact: true}).fill(admin.email);
  await page.getByLabel("Mật khẩu", {exact: true}).fill(admin.password);
  await page.locator("form").getByRole("button", {name: "Đăng nhập", exact: true}).click();
  // The account is intentionally provisioned server-side, never by an elevation API.
  await expect(page.getByRole("button", {name: "Thêm tài liệu", exact: true})).toBeVisible();
  await dismissWelcome(page);
}
async function publish(page: Page, title: string) {
  const card = page.locator(".rag-admin-list article").filter({has: page.getByRole("heading", {name: title, exact: true})});
  await card.getByRole("button", {name: "Xuất bản", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Đồng ý công bố tài liệu RAG?"});
  await expect(dialog.getByRole("checkbox")).toHaveCount(0);
  await expect(dialog.getByRole("button")).toHaveCount(2);
  await expect(dialog.getByRole("link")).toHaveAttribute("href", "/privacy#rag-publish");
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(card).toContainText("Đã xuất bản");
}

test("admin account manages publication, edits invalidate old sources, trash and restore", async ({page}) => {
  test.setTimeout(100000);
  const title = "Browser RAG source " + randomUUID().slice(0, 8);
  await loginAdmin(page);
  await page.getByRole("button", {name: "Thêm tài liệu", exact: true}).click();
  await page.getByLabel("Tên tài liệu", {exact: true}).fill(title);
  await page.getByLabel("Đơn vị / tác giả", {exact: true}).fill("QA self-authored");
  await page.getByLabel("Giấy phép / căn cứ được phép sử dụng", {exact: true}).fill("CC0 team-authored fictional browser test");
  await page.getByLabel("Nội dung tự soạn", {exact: true}).fill(text);
  await page.getByRole("button", {name: "Lưu bản nháp", exact: true}).click();
  const card = page.locator(".rag-admin-list article").filter({has: page.getByRole("heading", {name: title, exact: true})});
  await expect(card).toContainText("Bản nháp");
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).fill("Outpatient specialist benefit");
  await page.getByRole("button", {name: "Thử truy xuất bản nháp", exact: true}).click();
  await expect(page.locator(".rag-source blockquote")).toContainText("7,654");
  await card.getByRole("button", {name: "Xuất bản", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Không đồng ý", exact: true}).click();
  await expect(card).toContainText("Bản nháp");
  await publish(page, title);
  await page.screenshot({path: "../submission/evidence/screenshots/rag/admin-published.png", fullPage: true});
  await page.getByRole("link", {name: "Hỏi đáp bảo hiểm từ tài liệu →", exact: true}).click();
  await page.getByLabel("Nguồn để tra cứu", {exact: true}).selectOption({label: title});
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).fill("outpatient specialist benefit");
  await page.getByRole("button", {name: "Tìm câu trả lời", exact: true}).click();
  await expect(page.locator(".rag-answer")).toContainText("7,654");
  const sourceHref = await page.getByRole("link", {name: "Đọc trang nguồn ↗", exact: true}).first().getAttribute("href");
  expect(sourceHref).toContain("revision=2");
  await page.goto("/admin/rag");
  await card.getByRole("button", {name: "Sửa", exact: true}).click();
  await page.getByLabel("Nội dung tự soạn", {exact: true}).fill(text.replace("7,654", "8,765"));
  await page.getByRole("button", {name: "Lưu bản nháp", exact: true}).click();
  await expect(card).toContainText("Bản nháp"); await publish(page, title);
  await page.goto(sourceHref!);
  await expect(page.getByRole("alert", {name: "Lỗi thao tác"})).toContainText("RAG_SOURCE_RETIRED");
  await page.goto("/knowledge"); await page.getByLabel("Nguồn để tra cứu", {exact: true}).selectOption({label: title});
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).fill("outpatient specialist benefit");
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).press("Enter");
  await expect(page.locator(".rag-answer")).toContainText("8,765");
  await page.screenshot({path: "../submission/evidence/screenshots/rag/student-citations.png", fullPage: true});
  await page.goto("/admin/rag"); await card.getByRole("button", {name: "Chuyển vào thùng rác", exact: true}).click();
  await card.getByRole("button", {name: "Xác nhận", exact: true}).click(); await expect(card).toHaveCount(0);
  await page.getByRole("button", {name: "Thùng rác", exact: true}).click(); await expect(card).toContainText(title);
  await card.getByRole("button", {name: "Khôi phục bản nháp", exact: true}).click();
  await page.getByRole("button", {name: "Tài liệu đang quản lý", exact: true}).click(); await expect(card).toContainText("Bản nháp");
});

test("admin file upload requires per-file agreement and original file can be replaced", async ({page}) => {
  await loginAdmin(page); await page.setViewportSize({width: 390, height: 844});
  const title = "Uploaded RAG " + randomUUID().slice(0, 8);
  await page.getByRole("button", {name: "Thêm tài liệu", exact: true}).click();
  await page.getByLabel("Tên tài liệu", {exact: true}).fill(title);
  await page.getByLabel("Đơn vị / tác giả", {exact: true}).fill("Fictional QA");
  await page.getByLabel("Giấy phép / căn cứ được phép sử dụng", {exact: true}).fill("CC0 fictional upload test");
  await page.getByRole("button", {name: "Tải PDF / ảnh / TXT", exact: true}).click();
  await page.getByLabel("Tệp tài liệu RAG", {exact: true}).setInputFiles({name: "source.txt", mimeType: "text/plain", buffer: Buffer.from(text)});
  await page.getByRole("button", {name: "Lưu bản nháp", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Cho phép xử lý tài liệu RAG?"});
  await dialog.getByRole("button", {name: "Không đồng ý", exact: true}).click();
  await expect(page.locator(".rag-admin-list article").filter({hasText: title})).toHaveCount(0);
  await page.getByRole("button", {name: "Lưu bản nháp", exact: true}).click();
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.locator(".rag-source")).toContainText("source.txt");
  await page.getByLabel("Thay tệp gốc", {exact: true}).setInputFiles({name: "replacement.txt", mimeType: "text/plain", buffer: Buffer.from(text.replace("7,654", "9,876"))});
  await page.locator("button").filter({hasText: /^Thay tệp gốc$/}).click();
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.locator(".rag-source")).toContainText("9,876");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path: "../submission/evidence/screenshots/rag/admin-mobile.png", fullPage: true});
});

test("regular users cannot administer and missing evidence abstains without a model call", async ({page}) => {
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo")); await page.goto("/admin/rag");
  await expect(page.getByText("Bạn cần đăng nhập bằng tài khoản quản trị kho RAG.", {exact: true})).toBeVisible();
  await dismissWelcome(page);
  expect((await page.request.get("/api/v1/admin/rag/documents")).status()).toBe(401); // Demo bearer is kept only in app memory.
  await page.goto("/knowledge");
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).fill("Bảo hiểm thai sản được trả bao nhiêu?");
  await page.getByRole("button", {name: "Tìm câu trả lời", exact: true}).click();
  await expect(page.locator(".rag-answer")).toContainText("Chưa có đủ thông tin");
  await expect(page.locator(".rag-answer .citation-card")).toHaveCount(0);
});

test("RAG Gemini mode asks binary consent, preview stays local and answer links its cited source", async ({page}) => {
  let sends = 0;
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.route("**/api/v1/rag/documents", async route => {const response = await route.fetch(); await route.fulfill({json: {...await response.json(), gemini_configured: true}});});
  await page.route("**/api/v1/rag/ask", async route => {
    sends++; expect(route.request().postDataJSON().use_gemini).toBe(true);
    await route.fulfill({json: {status: "EVIDENCE_FOUND", provider: "GEMINI", method: "BM25_RAG_GEMINI", answer: "Fictional policy answer from cited evidence.", missing_concepts: [], notice: "Test only", citations: [{source_id: "R1", document_id: "114ae7bd-ee08-5092-ab9f-d3830ff2b330", revision: 1, title: "Fictional policy source", publisher: "Demo team", filename: "sample.txt", page: 1, excerpt: "Original sample excerpt", document_kind: "TEST_FIXTURE", href: "/knowledge/114ae7bd-ee08-5092-ab9f-d3830ff2b330?revision=1#page-1"}]}});
  });
  await page.goto("/knowledge"); await dismissWelcome(page);
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).fill("Outpatient benefit limit");
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).press("Enter");
  const dialog = page.getByRole("dialog", {name: "Cho phép dùng Gemini?"});
  await expect(dialog).toContainText("Đồng ý sẽ tiếp tục câu hỏi đang chờ");
  await dialog.getByRole("button", {name: "Không đồng ý", exact: true}).click(); expect(sends).toBe(0);
  await page.getByRole("button", {name: "Bật trả lời RAG + Gemini", exact: true}).click();
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(dialog).not.toBeVisible();
  expect(sends).toBe(0); // Enabling alone must not replay the declined question.
  await page.getByRole("button", {name: "Xem dữ liệu sẽ gửi", exact: true}).click();
  await expect(page.locator(".privacy-preview")).toContainText('"sent": false'); expect(sends).toBe(0);
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).press("Enter");
  await expect(page.locator(".rag-answer")).toContainText("Fictional policy answer"); expect(sends).toBe(1);
  await expect(page.getByRole("link", {name: "Đọc trang nguồn ↗", exact: true})).toHaveAttribute("href", /revision=1#page-1$/);
  await page.getByRole("button", {name: "Thu hồi quyền Gemini", exact: true}).click();
  await expect(page.getByRole("button", {name: "Bật trả lời RAG + Gemini", exact: true})).toBeVisible();
});

test("a pending RAG question continues through Gemini only after agreement; Shift Enter never sends", async ({page}) => {
  let sends = 0;
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.route("**/api/v1/rag/documents", async route => {const response = await route.fetch(); await route.fulfill({json: {...await response.json(), gemini_configured: true}});});
  await page.route("**/api/v1/rag/ask", async route => {
    sends++; const payload = route.request().postDataJSON();
    expect(payload.use_gemini).toBe(true); expect(payload.privacy_revision).toBeGreaterThan(0);
    await route.fulfill({json: {status: "EVIDENCE_FOUND", provider: "GEMINI", model: "gemini-3.5-flash-lite", method: "BM25_RAG_GEMINI", answer: "Theo điều khoản mẫu, hạn mức ngoại trú là 2.000 CNY/năm [R1].", missing_concepts: [], notice: "Test only", citations: [{source_id: "R1", document_id: "114ae7bd-ee08-5092-ab9f-d3830ff2b330", revision: 1, title: "Demo student health policy — fictional terms", publisher: "Demo team", filename: "sample.txt", page: 1, excerpt: "Fictional annual outpatient limit: CNY 2,000.", document_kind: "TEST_FIXTURE", href: "/knowledge/114ae7bd-ee08-5092-ab9f-d3830ff2b330?revision=1#page-1"}]}});
  });
  await page.goto("/knowledge"); await dismissWelcome(page);
  const question = page.getByLabel("Câu hỏi bảo hiểm", {exact: true});
  await question.fill("Quyền lợi ngoại trú có hạn mức bao nhiêu?"); await question.press("Shift+Enter");
  await expect(question).toHaveValue(/\n$/); expect(sends).toBe(0);
  await question.press("Enter");
  const dialog = page.getByRole("dialog", {name: "Cho phép dùng Gemini?"});
  await expect(dialog).toBeVisible(); expect(sends).toBe(0);
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(dialog).not.toBeVisible(); await expect(page.locator(".rag-answer")).toContainText("2.000 CNY");
  expect(sends).toBe(1); await expect(page.locator(".rag-answer")).toContainText("gemini-3.5-flash-lite");
  await expect(page.getByRole("link", {name: "Đọc trang nguồn ↗", exact: true})).toBeVisible();
  await page.locator(".rag-answer").scrollIntoViewIfNeeded();
  await page.screenshot({path: "../submission/evidence/screenshots/rag/rag-llm-unified.png"});
  await question.press("Enter"); await expect.poll(() => sends).toBe(2);
  await expect(dialog).not.toBeVisible(); // Current session grant is reused, never silently renewed.
});

import {test, expect, Page} from "@playwright/test";
import {dismissWelcome} from "./guide-helper";

async function openChat(page: Page, configured = true) {
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.route("**/api/v1/finance/assistant/status", route => route.fulfill({json: {gemini_configured: configured, model: configured ? "gemini-test" : null, read_only: true, history_stored: false}}));
  await page.goto("/copilot");
  await dismissWelcome(page);
  await expect(page.getByRole("heading", {name: "Trợ lý du học", exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toHaveCount(0);
}

async function allowGemini(page: Page) {
  await page.getByRole("button", {name: "Xem quyền Gemini", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Cho phép dùng Gemini?"});
  await expect(dialog.getByRole("checkbox")).toHaveCount(0);
  await expect(dialog.getByRole("button")).toHaveCount(2);
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(dialog).not.toBeVisible();
}

test("Gemini chat sends bounded conversation context, displays sources and clears locally", async ({page}) => {
  const bodies: {message: string; use_gemini: boolean; language: string; history: {role: string; content: string}[]}[] = [];
  await page.route("**/api/v1/study-assistant/chat", async route => {
    bodies.push(route.request().postDataJSON());
    await route.fulfill({json: {provider: "GEMINI", model: "gemini-test", method: "GEMINI_GROUNDED", intent: "BUDGET_NEXT_STEP", answer: "Test reply from owned budget data.", executed_actions: [], actions: [{title: "Check budget", href: "/finance"}], citations: [{source_id: "B1", title: "Test budget source", href: "/finance"}, {source_id: "D1", title: "Self-authored test policy", document_kind: "TEST_FIXTURE", page: 1, excerpt: "Self-authored test excerpt."}], notice: "Test response"}});
  });
  await openChat(page);
  await allowGemini(page);
  await expect(page.locator(".copilot-privacy")).toContainText("Google Gemini");
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Giải thích ngân sách của tôi");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".copilot-answer")).toContainText("Test reply");
  await expect(page.getByRole("link", {name: "Test budget source ↗"})).toHaveAttribute("href", "/finance");
  await expect(page.locator(".copilot-source .badge.demo")).toHaveText("Dữ liệu mẫu tự soạn");
  expect(bodies[0].use_gemini).toBe(true); expect(bodies[0].history).toEqual([]);
  await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByLabel("Question for the assistant", {exact: true}).fill("Explain that again");
  await page.getByRole("button", {name: "Send question", exact: true}).click();
  await expect(page.locator(".copilot-turn")).toHaveCount(2);
  expect(bodies[1].language).toBe("en"); expect(bodies[1].history.map(turn => turn.role)).toEqual(["user", "assistant"]);
  await page.getByRole("button", {name: "Clear conversation", exact: true}).click();
  await expect(page.locator(".copilot-turn")).toHaveCount(0);
});

test("provider quota fallback is explicit without a mode picker", async ({page}) => {
  await page.route("**/api/v1/study-assistant/chat", route => route.fulfill({json: {route: "RAG", provider: "EXTRACTIVE", method: "AUTOMATIC_RAG", answer: "Original excerpt", fallback_reason: "PROVIDER_RATE_LIMIT", actions: [], citations: [], executed_actions: []}}));
  await openChat(page); await allowGemini(page);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Hỏi về bảo hiểm");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".copilot-fallback")).toContainText("giới hạn lượt gọi");
  await expect(page.getByRole("button", {name: "Tra cứu trực tiếp", exact: true})).toHaveCount(0);
});

test("no key keeps local assistant available without a mode picker", async ({page}) => {
  let cloud = true;
  await page.route("**/api/v1/study-assistant/chat", async route => {cloud = route.request().postDataJSON().use_gemini; await route.fulfill({json: {provider: "RULES", answer: "Local answer", actions: [], citations: [], executed_actions: []}});});
  await openChat(page, false);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Hóa đơn của tôi");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".copilot-answer")).toContainText("Local answer"); expect(cloud).toBe(false);
});

test("Enter sends once, Shift Enter adds a newline and IME Enter never submits", async ({page}) => {
  const sent: {message: string; history: unknown[]}[] = [];
  await page.route("**/api/v1/study-assistant/chat", async route => {
    sent.push(route.request().postDataJSON());
    await route.fulfill({json: {provider: "GEMINI", answer: "Keyboard accepted", actions: [], citations: [], executed_actions: []}});
  });
  await openChat(page); await allowGemini(page);
  const box = page.getByLabel("Câu hỏi cho trợ lý", {exact: true});
  await box.fill("Dòng đầu"); await box.press("Shift+Enter"); await box.pressSequentially("Dòng sau");
  await expect(box).toHaveValue("Dòng đầu\nDòng sau"); expect(sent).toHaveLength(0);
  await box.dispatchEvent("keydown", {key: "Enter", code: "Enter", keyCode: 229, isComposing: true, bubbles: true});
  expect(sent).toHaveLength(0);
  await box.press("Enter");
  await expect(page.locator(".copilot-turn")).toHaveCount(1); expect(sent).toHaveLength(1);
  expect(sent[0].message).toBe("Dòng đầu\nDòng sau"); expect(sent[0].history).toEqual([]);
  await box.fill(" "); await box.press("Enter"); expect(sent).toHaveLength(1);
});

test("feature click opens fixed binary consent, decline does not grant and details are public", async ({page}) => {
  let grants = 0;
  await page.route("**/api/v1/privacy/ai-permission", async route => {if (route.request().method() === "POST") grants++; await route.continue();});
  await openChat(page);
  await page.getByRole("button", {name: "Xem quyền Gemini", exact: true}).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("checkbox")).toHaveCount(0);
  await expect(dialog.getByRole("button")).toHaveCount(2);
  await expect(dialog.getByRole("link")).toHaveAttribute("href", "/privacy#gemini");
  await expect(dialog).toContainText("tối đa 3 lượt Gemini");
  await dialog.getByRole("button", {name: "Không đồng ý", exact: true}).click();
  await expect(dialog).not.toBeVisible(); expect(grants).toBe(0);
  await expect(page.getByRole("button", {name: "Thu hồi quyền Gemini", exact: true})).toHaveCount(0);
  await page.getByRole("button", {name: "Xem quyền Gemini", exact: true}).click();
  await page.keyboard.press("Escape"); await expect(dialog).not.toBeVisible(); expect(grants).toBe(0);
  await page.context().clearCookies(); await page.evaluate(() => localStorage.clear());
  await page.goto("/privacy#gemini"); await expect(page.getByRole("heading", {name: "Thông báo quyền riêng tư", exact: true})).toBeVisible();
});

test("preview stays local, revoking disables Gemini and account page exposes controls", async ({page}) => {
  let sent = 0;
  await page.route("**/api/v1/study-assistant/chat", async route => {sent++; await route.fulfill({json: {provider: "GEMINI", answer: "Answer", actions: [], citations: [], executed_actions: []}});});
  await openChat(page); await allowGemini(page);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Explain budgeting");
  await page.getByRole("button", {name: "Xem dữ liệu sẽ gửi", exact: true}).click();
  await expect(page.locator(".privacy-preview")).toContainText("Explain budgeting");
  await expect(page.locator(".privacy-preview")).toContainText("APP_GUIDE"); expect(sent).toBe(0);
  await page.getByRole("button", {name: "Thu hồi quyền Gemini", exact: true}).click();
  await expect(page.getByRole("button", {name: "Thu hồi quyền Gemini", exact: true})).toHaveCount(0);
  await expect(page.locator(".privacy-preview")).toHaveCount(0);
  await page.goto("/account"); await expect(page.getByRole("heading", {name: "Cho phép dùng Gemini?", exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Xem quyền Gemini", exact: true})).toBeEnabled();
});

test("an in-flight Enter request cannot be sent twice and permission dialog fits mobile locales", async ({page}) => {
  let calls = 0; let release!: () => void;
  const gate = new Promise<void>(resolve => {release = resolve;});
  await page.route("**/api/v1/study-assistant/chat", async route => {calls++; await gate; await route.fulfill({json: {provider: "GEMINI", answer: "One answer", actions: [], citations: [], executed_actions: []}});});
  await openChat(page); await allowGemini(page);
  const box = page.getByLabel("Câu hỏi cho trợ lý", {exact: true});
  await box.fill("Explain the sample policy"); await box.press("Enter");
  await expect(box).toBeDisabled(); await page.keyboard.press("Enter"); expect(calls).toBe(1);
  release(); await expect(page.locator(".copilot-turn")).toHaveCount(1);
  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByRole("button", {name: "View Gemini access", exact: true}).click();
  const mobileDialog = page.getByRole("dialog", {name: "Allow Gemini?", exact: true});
  await expect(mobileDialog).toBeVisible();
  await expect(mobileDialog.getByRole("heading", {name: "Allow Gemini?", exact: true})).toBeInViewport();
  expect(await mobileDialog.evaluate(element => element.scrollTop)).toBe(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path: "../submission/evidence/screenshots/privacy/permission-mobile-en.png", fullPage: true});
  await page.keyboard.press("Escape");
  await page.getByRole("button", {name: "中文", exact: true}).click();
  await page.getByRole("button", {name: "查看 Gemini 权限", exact: true}).click();
  await expect(page.getByRole("dialog", {name: "允许使用 Gemini？", exact: true})).toBeVisible();
  await page.screenshot({path: "../submission/evidence/screenshots/privacy/permission-mobile-zh.png", fullPage: true});
});

test("an older UI cannot consent to a newer unseen notice version", async ({page}) => {
  await page.route("**/api/v1/privacy/ai-permission", route => route.fulfill({json: {enabled: false, revision: 0, notice_version: "future-unseen-notice", scopes: [], data_mode: "DEMO_ONLY", allowed_scopes: ["history", "documents"]}}));
  await openChat(page);
  await page.getByRole("button", {name: "Xem quyền Gemini", exact: true}).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("alert")).toContainText("Thông báo quyền đã thay đổi");
  await expect(dialog.getByRole("button", {name: "Đồng ý", exact: true})).toBeDisabled();
});

test("OCR asks per file, declining sends no bytes and agreeing continues the original operation", async ({page}) => {
  let uploads = 0;
  await page.route("**/api/v1/invoice-imports", async route => {
    uploads++;
    expect(route.request().headers()["x-processing-consent"]).toBe("invoice-ocr:files-2026-10-19-v1");
    await route.fulfill({json: {id: "qa-import", filename: "fictional.txt", method: "TEXT", invoice_id: null, pages: [{page: 1, text: "Fictional invoice"}], suggestions: {fields: {}, currency: "CNY", warnings: []}}});
  });
  await openChat(page);
  await page.goto("/invoices/new");
  await page.getByLabel("Tệp hóa đơn", {exact: true}).setInputFiles({name: "fictional.txt", mimeType: "text/plain", buffer: Buffer.from("Fictional invoice CNY 800")});
  const read = page.getByRole("button", {name: "Đọc và điền thông tin", exact: true});
  await read.click();
  const dialog = page.getByRole("dialog", {name: "Cho phép đọc hóa đơn?"});
  await expect(dialog).toBeVisible(); expect(uploads).toBe(0);
  await expect(dialog.getByRole("checkbox")).toHaveCount(0); await expect(dialog.getByRole("button")).toHaveCount(2);
  await expect(dialog.getByRole("link")).toHaveAttribute("href", "/privacy#invoice-ocr");
  await dialog.getByRole("button", {name: "Không đồng ý", exact: true}).click();
  await expect(read).toBeEnabled(); expect(uploads).toBe(0);
  await read.click(); await expect(dialog).toBeVisible();
  await page.screenshot({path: "../submission/evidence/screenshots/privacy/binary-ocr-vi.png"});
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await page.getByText("Xem toàn văn đã đọc", {exact: true}).click();
  await expect(page.getByText("Fictional invoice", {exact: true})).toBeVisible(); expect(uploads).toBe(1);
});

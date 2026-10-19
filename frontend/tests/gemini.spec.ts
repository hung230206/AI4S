import {test, expect, Page} from "@playwright/test";
import {dismissWelcome} from "./guide-helper";

async function openChat(page: Page, configured = true) {
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.route("**/api/v1/finance/assistant/status", route => route.fulfill({json: {gemini_configured: configured, model: configured ? "gemini-test" : null, read_only: true, history_stored: false}}));
  await page.goto("/copilot");
  await dismissWelcome(page);
  await expect(page.getByRole("button", {name: "Tra cứu trực tiếp", exact: true})).toBeEnabled();
}

async function allowGemini(page: Page, history = false) {
  await page.getByRole("button", {name: "Cài đặt quyền Gemini", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Quyền riêng tư AI"});
  if (history) await dialog.getByLabel("Gửi tối đa 3 lượt Gemini gần nhất trong tab này", {exact: true}).check();
  await dialog.getByLabel("Tôi xác nhận từ 18 tuổi trở lên.", {exact: true}).check();
  await dialog.getByLabel(/Tôi sẽ chỉ gửi dữ liệu/).check();
  await dialog.getByLabel(/Tôi đã đọc thông báo/).check();
  await dialog.getByRole("button", {name: "Cho phép và bật Gemini", exact: true}).click();
  await expect(dialog).not.toBeVisible();
}

test("Gemini chat sends bounded conversation context, displays sources and clears locally", async ({page}) => {
  const bodies: {message: string; use_gemini: boolean; language: string; history: {role: string; content: string}[]}[] = [];
  await page.route("**/api/v1/finance/assistant", async route => {
    bodies.push(route.request().postDataJSON());
    await route.fulfill({json: {provider: "GEMINI", model: "gemini-test", method: "GEMINI_GROUNDED", intent: "BUDGET_NEXT_STEP", answer: "Test reply from owned budget data.", executed_actions: [], actions: [{title: "Check budget", href: "/finance"}], citations: [{source_id: "B1", title: "Test budget source", href: "/finance"}, {source_id: "D1", title: "Self-authored test policy", document_kind: "TEST_FIXTURE", page: 1, excerpt: "Self-authored test excerpt."}], notice: "Test response"}});
  });
  await openChat(page);
  await allowGemini(page, true);
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toHaveAttribute("aria-pressed", "true");
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

test("provider quota fallback is explicit and direct lookup sends no chat history", async ({page}) => {
  let mode = true;
  await page.route("**/api/v1/finance/assistant", async route => {
    const body = route.request().postDataJSON(); mode = body.use_gemini;
    if (!mode) expect(body.history).toEqual([]);
    await route.fulfill({json: {provider: "RULES", method: "GROUNDED_WORKFLOW", answer: "Local account data", fallback_reason: mode ? "PROVIDER_RATE_LIMIT" : undefined, actions: [], citations: [], executed_actions: [], notice: "Local"}});
  });
  await openChat(page);
  await allowGemini(page, true);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Hỏi về ngân sách");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".copilot-fallback")).toContainText("giới hạn lượt gọi");
  await page.getByRole("button", {name: "Tra cứu trực tiếp", exact: true}).click();
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Kiểm tra tiếp ngân sách");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".copilot-turn")).toHaveCount(2);
  expect(mode).toBe(false);
});

test("no key keeps direct lookup available without offering an active Gemini mode", async ({page}) => {
  await openChat(page, false);
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toBeDisabled();
  await expect(page.getByRole("button", {name: "Tra cứu trực tiếp", exact: true})).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".copilot-privacy")).toContainText("chưa được cấu hình");
});

test("Enter sends once, Shift Enter adds a newline and IME Enter never submits", async ({page}) => {
  const sent: {message: string; history: unknown[]}[] = [];
  await page.route("**/api/v1/finance/assistant", async route => {
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

test("permission choices default off, cancel does not grant and privacy notice is public", async ({page}) => {
  await openChat(page);
  await expect(page.getByRole("button", {name: "Tra cứu trực tiếp", exact: true})).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toBeDisabled();
  await page.getByRole("button", {name: "Cài đặt quyền Gemini", exact: true}).click();
  const dialog = page.getByRole("dialog");
  for (const checkbox of await dialog.getByRole("checkbox").all()) await expect(checkbox).not.toBeChecked();
  await expect(dialog.getByRole("button", {name: "Cho phép và bật Gemini", exact: true})).toBeDisabled();
  await expect(dialog.getByLabel("Gửi tóm tắt ngân sách và hóa đơn", {exact: true})).toBeDisabled();
  await page.keyboard.press("Escape"); await expect(dialog).not.toBeVisible();
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toBeDisabled();
  await page.context().clearCookies(); await page.evaluate(() => localStorage.clear());
  await page.goto("/privacy"); await expect(page.getByRole("heading", {name: "Thông báo quyền riêng tư", exact: true})).toBeVisible();
});

test("preview stays local, revoking disables Gemini and account page exposes controls", async ({page}) => {
  let sent = 0;
  await page.route("**/api/v1/finance/assistant", async route => {sent++; await route.fulfill({json: {provider: "GEMINI", answer: "Answer", actions: [], citations: [], executed_actions: []}});});
  await openChat(page); await allowGemini(page);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Explain policy coverage");
  await page.getByRole("button", {name: "Xem dữ liệu sẽ gửi", exact: true}).click();
  await expect(page.locator(".privacy-preview")).toContainText("Explain policy coverage");
  await expect(page.locator(".privacy-preview")).toContainText("APP_GUIDE"); expect(sent).toBe(0);
  await page.getByRole("button", {name: "Thu hồi quyền Gemini", exact: true}).click();
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toBeDisabled();
  await expect(page.locator(".privacy-preview")).toHaveCount(0);
  await page.goto("/account"); await expect(page.getByRole("heading", {name: "Quyền riêng tư AI", exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Cài đặt quyền Gemini", exact: true})).toBeEnabled();
});

test("an in-flight Enter request cannot be sent twice and permission dialog fits mobile locales", async ({page}) => {
  let calls = 0; let release!: () => void;
  const gate = new Promise<void>(resolve => {release = resolve;});
  await page.route("**/api/v1/finance/assistant", async route => {calls++; await gate; await route.fulfill({json: {provider: "GEMINI", answer: "One answer", actions: [], citations: [], executed_actions: []}});});
  await openChat(page); await allowGemini(page);
  const box = page.getByLabel("Câu hỏi cho trợ lý", {exact: true});
  await box.fill("Explain the sample policy"); await box.press("Enter");
  await expect(box).toBeDisabled(); await page.keyboard.press("Enter"); expect(calls).toBe(1);
  release(); await expect(page.locator(".copilot-turn")).toHaveCount(1);
  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByRole("button", {name: "Gemini permissions", exact: true}).click();
  const mobileDialog = page.getByRole("dialog", {name: "AI privacy", exact: true});
  await expect(mobileDialog).toBeVisible();
  await expect(mobileDialog.getByRole("heading", {name: "AI privacy", exact: true})).toBeInViewport();
  expect(await mobileDialog.evaluate(element => element.scrollTop)).toBe(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path: "../submission/evidence/screenshots/privacy/permission-mobile-en.png", fullPage: true});
  await page.keyboard.press("Escape");
  await page.getByRole("button", {name: "中文", exact: true}).click();
  await page.getByRole("button", {name: "Gemini 权限设置", exact: true}).click();
  await expect(page.getByRole("dialog", {name: "AI 隐私", exact: true})).toBeVisible();
  await page.screenshot({path: "../submission/evidence/screenshots/privacy/permission-mobile-zh.png", fullPage: true});
});

test("an older UI cannot consent to a newer unseen notice version", async ({page}) => {
  await page.route("**/api/v1/privacy/ai-permission", route => route.fulfill({json: {enabled: false, revision: 0, notice_version: "future-unseen-notice", scopes: [], data_mode: "DEMO_ONLY", allowed_scopes: ["history", "documents"]}}));
  await openChat(page);
  await page.getByRole("button", {name: "Cài đặt quyền Gemini", exact: true}).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Tôi xác nhận từ 18 tuổi trở lên.", {exact: true}).check();
  await dialog.getByLabel(/Tôi sẽ chỉ gửi dữ liệu/).check(); await dialog.getByLabel(/Tôi đã đọc thông báo/).check();
  await expect(dialog.getByRole("alert")).toContainText("Thông báo quyền đã thay đổi");
  await expect(dialog.getByRole("button", {name: "Cho phép và bật Gemini", exact: true})).toBeDisabled();
});

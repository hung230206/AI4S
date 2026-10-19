import {test, expect, type Page} from "@playwright/test";
import {dismissWelcome, openAssistant} from "./guide-helper";
import {safeNavigation} from "../src/lib/assistant-navigation";

async function start(page: Page) {
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.route("**/api/v1/finance/assistant/status", route => route.fulfill({json: {gemini_configured: false}}));
  await page.goto("/"); await dismissWelcome(page); await openAssistant(page);
}
async function ask(page: Page, text: string, label = "Câu hỏi cho trợ lý") {
  await page.getByLabel(label, {exact: true}).fill(text); await page.getByLabel(label, {exact: true}).press("Enter");
}

test("real navigation asks first, cancel and Escape stay put, confirm filters history and preserves the conversation", async ({page}) => {
  await start(page);
  const writes: string[] = [];
  page.on("request", request => {if (request.method() === "POST" && /\/api\/v1\/(orders|invoices|finance\/wallets)/.test(request.url())) writes.push(request.url());});
  await ask(page, "hiện tại có những giao dịch nào đã thành công");
  const modal = page.getByRole("dialog", {name: "Chuyển trang?", exact: true});
  await expect(modal).toBeVisible(); await expect(modal).toContainText("Lịch sử giao dịch");
  await expect(page).toHaveURL("http://localhost:3000/");
  await expect(modal.getByRole("button", {name: "Ở lại", exact: true})).toBeFocused();
  await page.screenshot({path: "../submission/evidence/screenshots/assistant-navigation/desktop-confirm.png", animations: "disabled"});
  await modal.getByRole("button", {name: "Ở lại", exact: true}).click();
  await expect(modal).not.toBeVisible(); await expect(page).toHaveURL("http://localhost:3000/");
  await expect(page.getByLabel("Câu hỏi cho trợ lý", {exact: true})).toBeFocused();
  const action = page.locator(".assistant-actions").getByRole("button", {name: "Lịch sử giao dịch →", exact: true});
  await action.click(); await expect(modal).toBeVisible(); await page.keyboard.press("Escape");
  await expect(modal).not.toBeVisible(); await expect(page.locator(".floating-chat")).toBeVisible();
  await action.click(); await modal.getByRole("button", {name: "Mở trang", exact: true}).click();
  await expect(page).toHaveURL(/\/history\?status=SUCCEEDED$/);
  await expect(page.getByLabel("Trạng thái giao dịch", {exact: true})).toHaveValue("SUCCEEDED");
  await expect(page.locator(".floating-chat")).toHaveCount(0);
  await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
  await expect(page.locator(".assistant-question")).toContainText("hiện tại có những giao dịch nào đã thành công");
  await ask(page, "Tôi muốn xem giao dịch thất bại"); await expect(modal).toBeVisible();
  await expect(page).toHaveURL(/status=SUCCEEDED$/);
  await modal.getByRole("button", {name: "Mở trang", exact: true}).click();
  await expect(page).toHaveURL(/\/history\?status=FAILED$/);
  await expect(page.getByLabel("Trạng thái giao dịch", {exact: true})).toHaveValue("FAILED");
  await page.getByLabel("Trạng thái giao dịch", {exact: true}).selectOption("");
  await expect(page).toHaveURL(/\/history$/); expect(writes).toEqual([]);
});

test("real add-invoice and budget requests open the correct page only after confirmation", async ({page}) => {
  await start(page);
  for (const [question, title, href] of [["Tôi muốn thêm hóa đơn", "Thêm hóa đơn", "/invoices/new"], ["Tôi cần quản lý ngân sách", "Ngân sách", "/finance"]]) {
    await ask(page, question);
    const modal = page.getByRole("dialog", {name: "Chuyển trang?", exact: true});
    await expect(modal).toContainText(title);
    await modal.getByRole("button", {name: "Mở trang", exact: true}).click(); await expect(page).toHaveURL(new RegExp(href + "$"));
    await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
    await expect(page.locator(".assistant-question").last()).toHaveText(question);
  }
});

test("mobile English and Chinese navigation proposals stay accessible", async ({page}) => {
  await page.setViewportSize({width: 390, height: 844}); await start(page);
  await page.getByRole("button", {name: "English", exact: true}).click();
  await ask(page, "Show my successful transactions", "Question for the assistant");
  const modal = page.getByRole("dialog", {name: "Open this page?", exact: true});
  await expect(modal).toContainText("Transaction history");
  await expect(modal.getByRole("button", {name: "Open page", exact: true})).toBeInViewport();
  await page.screenshot({path: "../submission/evidence/screenshots/assistant-navigation/mobile-confirm.png", animations: "disabled"});
  await modal.getByRole("button", {name: "Stay here", exact: true}).click();
  await page.getByRole("button", {name: "中文", exact: true}).click();
  await ask(page, "我需要管理预算", "向助手提问");
  const zh = page.getByRole("dialog", {name: "打开此页面？", exact: true});
  await expect(zh).toContainText("预算"); await zh.getByRole("button", {name: "打开页面", exact: true}).click();
  await expect(page).toHaveURL(/\/finance$/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("untrusted navigation targets cannot create a popup or an action", async ({page}) => {
  let href = "";
  await page.route("**/api/v1/study-assistant/chat", route => route.fulfill({json: {provider: "RULES", answer: "Invalid destination ignored", citations: [], navigation: {href, title: "Unsafe", reason: "Invalid"}, actions: [{title: "Unsafe", href}]}}));
  await start(page);
  for (href of ["javascript:alert(1)", "https://example.com", "//example.com", "/admin/rag", "/history?status=SUCCEEDED&next=https://example.com", "/history?status=__proto__"]) {
    expect(safeNavigation({href, title: "Unsafe", reason: "Invalid"})).toBeNull();
    await ask(page, "Test destination " + href);
    await expect(page.locator(".assistant-answer").last()).toContainText("Invalid destination ignored");
    await expect(page.getByRole("dialog", {name: "Chuyển trang?", exact: true})).not.toBeVisible();
    await expect(page.locator(".assistant-actions button")).toHaveCount(0);
    await expect(page).toHaveURL("http://localhost:3000/");
  }
});

test("withdrawing permission dismisses an outstanding navigation confirmation", async ({page}) => {
  await start(page); await ask(page, "Tôi cần quản lý ngân sách");
  const modal = page.getByRole("dialog", {name: "Chuyển trang?", exact: true}); await expect(modal).toBeVisible();
  await page.route("**/api/v1/privacy/ai-permission", async route => {
    const response = await route.fetch(); const current = await response.json();
    await route.fulfill({json: {...current, enabled: false, revision: current.revision + 1, scopes: []}});
  });
  await page.evaluate(() => window.dispatchEvent(new Event("demo:ai-permission-changed")));
  await expect(modal).not.toBeVisible(); await expect(page.locator(".floating-chat")).toHaveCount(0);
  await expect(page).toHaveURL("http://localhost:3000/");
});

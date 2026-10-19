import {test, expect, Page} from "@playwright/test";
import path from "node:path";
import fs from "node:fs";
const evidence = path.resolve(__dirname, "../../submission/evidence/screenshots/task-ux");
fs.mkdirSync(evidence, {recursive: true});
async function demo(page: Page, route = "/") {
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.goto(route);
  await expect(page.locator("dialog.page-intro-dialog")).toBeVisible();
}
async function acknowledge(page: Page) {await page.locator("dialog.page-intro-dialog").getByRole("button", {name: "Đã hiểu", exact: true}).click();}

test("three needs lead to the right pages; short intros repeat until the user hides them", async ({page}) => {
  await demo(page);
  const intro = page.locator("dialog.page-intro-dialog");
  await expect(intro.getByRole("heading")).toHaveText("Bạn muốn làm gì hôm nay?");
  await expect(intro.getByRole("checkbox")).not.toBeChecked();
  await expect(intro.getByRole("button")).toHaveCount(1);
  const position = await intro.boundingBox(); const viewport = page.viewportSize()!;
  expect(Math.abs(position!.x + position!.width / 2 - viewport.width / 2)).toBeLessThan(2);
  expect(Math.abs(position!.y + position!.height / 2 - viewport.height / 2)).toBeLessThan(2);
  await page.screenshot({path: path.join(evidence, "home-intro.png"), animations: "disabled"});
  await acknowledge(page); await expect(page.locator("main h1")).toBeFocused();
  await expect(page.locator(".goal-card")).toHaveCount(3);
  await expect(page.getByRole("link", {name: "Xem bảo hiểm", exact: true})).toHaveAttribute("href", "/insurance");
  await expect(page.getByRole("link", {name: "Quản lý tiền sinh hoạt", exact: true})).toHaveAttribute("href", "/finance");
  await page.screenshot({path: path.join(evidence, "three-needs.png"), animations: "disabled", fullPage: true});
  await page.getByRole("link", {name: "Quản lý tiền sinh hoạt", exact: true}).click();
  await expect(intro).toBeVisible(); await expect(intro.getByRole("heading")).toHaveText("Quản lý tiền sinh hoạt");
  await page.keyboard.press("Escape"); await expect(intro).not.toBeVisible();
  await page.getByRole("button", {name: "Sắp thu / chi", exact: true}).click();
  await expect(page.getByRole("button", {name: "Sắp thu / chi", exact: true})).toHaveAttribute("aria-pressed", "true");
  await expect(intro).not.toBeVisible();
  await page.getByRole("link", {name: "Tổng quan", exact: true}).first().click();
  await expect(intro).toBeVisible(); await expect(intro.getByRole("heading")).toHaveText("Bạn muốn làm gì hôm nay?");
  await acknowledge(page);
  await page.getByRole("link", {name: "Quản lý tiền sinh hoạt", exact: true}).click(); await expect(intro).toBeVisible();
});

test("hide checkbox applies only to that page, survives reload and can be restored in settings", async ({page}) => {
  await demo(page, "/finance"); const intro = page.locator("dialog.page-intro-dialog");
  await intro.getByRole("checkbox", {name: "Không hiện lại hướng dẫn này", exact: true}).check();
  await acknowledge(page); await page.reload();
  await expect(page.locator("main h1")).toHaveText("Quản lý tiền sinh hoạt"); await expect(intro).not.toBeVisible();
  await page.goto("/insurance"); await expect(intro).toBeVisible(); await expect(intro.getByRole("heading")).toHaveText("Hiểu và quản lý bảo hiểm");
  await expect(intro.getByRole("checkbox")).not.toBeChecked(); await acknowledge(page);
  await page.goto("/finance"); await expect(page.locator("main h1")).toBeVisible(); await expect(intro).not.toBeVisible();
  await page.getByRole("button", {name: "Mở hướng dẫn sử dụng", exact: true}).click();
  await expect(page.getByRole("dialog", {name: "Bắt đầu cùng Demo", exact: true})).toBeVisible();
  await page.keyboard.press("Escape");
  await page.goto("/account"); await acknowledge(page);
  await page.getByRole("button", {name: "Hiện lại các hướng dẫn đã ẩn", exact: true}).click();
  await expect(page.getByRole("status")).toHaveText("Đã bật lại các hướng dẫn đã ẩn.");
  await page.goto("/finance"); await expect(intro).toBeVisible(); await acknowledge(page);
  await page.goto("/account"); await acknowledge(page);
  await page.getByRole("checkbox", {name: "Tự hiện hướng dẫn khi chuyển trang", exact: true}).uncheck();
  await page.goto("/history"); await expect(page.locator("main h1")).toBeVisible(); await expect(intro).not.toBeVisible();
});

test("mobile introductions fit, trap keyboard focus and translate with the page", async ({page}) => {
  await page.setViewportSize({width: 320, height: 740}); await demo(page);
  const intro = page.locator("dialog.page-intro-dialog");
  for (let i = 0; i < 8; i++) {await page.keyboard.press("Tab"); expect(await intro.evaluate(el => el.contains(document.activeElement))).toBe(true);}
  for (let i = 0; i < 8; i++) {await page.keyboard.press("Shift+Tab"); expect(await intro.evaluate(el => el.contains(document.activeElement))).toBe(true);}
  await intro.getByRole("checkbox").check(); await acknowledge(page);
  await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByRole("button", {name: "Appearance", exact: true}).click();
  await page.getByRole("link", {name: "Manage my budget", exact: true}).click();
  await expect(intro.getByRole("heading")).toHaveText("Manage your living budget");
  await expect(intro.getByRole("checkbox")).toHaveAccessibleName("Don't show this introduction again");
  expect(await intro.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  await page.screenshot({path: path.join(evidence, "finance-mobile-en-dark.png"), animations: "disabled"});
  await intro.getByRole("button", {name: "Got it", exact: true}).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("button", {name: "中文", exact: true}).click();
  await page.goto("/insurance"); await expect(intro.getByRole("heading")).toHaveText("了解和管理保险");
  await expect(intro.getByRole("checkbox")).toHaveAccessibleName("不再显示此页面简介");
  await page.screenshot({path: path.join(evidence, "insurance-mobile-zh-dark.png"), animations: "disabled"});
});

test("invoice progress reflects API state and completed payment offers receipt and home, without a claim step", async ({page}) => {
  const invoice = {id: "fe17e283-8d02-4b93-89de-989ea29d0c01", invoice_number: "UX-FICTIONAL-001", institution_name: "Fictional QA School", beneficiary_name: "Fictional QA School", amount_cny: "800.00", due_date: "2026-12-20", country_code: "CN", source_type: "USER_ENTERED", status: "OPEN", notes: "Self-authored UI fixture", source_url: null, fee_type: "TUITION"};
  let succeeded = false;
  const order = {id: "99e31394-98e8-46f0-8378-a7c7ef574444", invoice_id: invoice.id, quote_id: "fictional-ui-quote", amount_cny: "800.00", total_vnd: "2847000", status: "SUCCEEDED", created_at: "2026-10-20T00:00:00Z", consent_at: "2026-10-20T00:00:00Z", sandbox_scenario: "SUCCESS"};
  await page.route(`**/api/v1/invoices/${invoice.id}`, route => route.fulfill({json: invoice}));
  await page.route(`**/api/v1/invoice-imports/by-invoice/${invoice.id}`, route => route.fulfill({json: {source: null}}));
  await page.route("**/api/v1/finance/plans", route => route.fulfill({json: {items: [{id: "fictional-plan", invoice_id: invoice.id, active: true, amount: "800.00", due_date: invoice.due_date}]}}));
  await page.route("**/api/v1/orders", route => route.fulfill({json: {items: succeeded ? [order] : []}}));
  await page.route(`**/api/v1/orders/${order.id}`, route => route.fulfill({json: order}));
  await page.route(`**/api/v1/orders/${order.id}/events`, route => route.fulfill({json: {items: [], audit: []}}));
  await page.route("**/api/v1/insurance/policies", route => route.fulfill({json: {items: [{id: "fictional-policy", active: true, premium_invoice_id: invoice.id}]}}));
  await demo(page, `/invoices/${invoice.id}`); await acknowledge(page);
  const journey = page.getByRole("region", {name: "Khoản phí này đang ở bước nào?", exact: true});
  await expect(journey).toContainText("Đã thêm vào khoản sắp chi");
  await expect(journey).toContainText("Chưa thử thanh toán");
  await expect(journey.getByRole("link", {name: "Xem giá trị VND", exact: true})).toHaveAttribute("href", `/checkout/${invoice.id}`);
  succeeded = true; await page.reload(); await acknowledge(page);
  await expect(journey).toContainText("Mô phỏng thành công");
  await expect(journey.getByRole("link", {name: "Xem giá trị VND", exact: true})).toHaveCount(0);
  await page.screenshot({path: path.join(evidence, "fee-progress.png"), animations: "disabled", fullPage: true});
  await journey.getByRole("link", {name: "Xem kết quả giao dịch", exact: true}).click(); await acknowledge(page);
  const completion = page.locator(".payment-complete-next");
  await expect(completion.getByRole("link", {name: "Xem biên nhận mô phỏng", exact: true})).toHaveAttribute("href", `/receipts/${order.id}`);
  await expect(completion.getByRole("link", {name: "Về tổng quan", exact: true})).toHaveAttribute("href", "/");
  await expect(completion.getByRole("link", {name: "Xem hợp đồng liên quan", exact: true})).toHaveAttribute("href", "/insurance#policy-fictional-policy");
  await expect(completion.locator('a[href*="claim"]')).toHaveCount(0);
  await expect(completion).toContainText("Không có tiền thật được chuyển");
  await page.screenshot({path: path.join(evidence, "payment-finish.png"), animations: "disabled", fullPage: true});
  await page.route("**/api/v1/orders", route => route.fulfill({status: 503, json: {error: {code: "QA_UNAVAILABLE", message: "Fictional QA outage"}}}));
  await page.goto(`/invoices/${invoice.id}`); await acknowledge(page);
  await expect(journey.getByText("Chưa tải được trạng thái", {exact: true})).toHaveCount(2);
  await expect(journey.getByText("Chưa thử thanh toán", {exact: true})).toHaveCount(0);
  await expect(journey.locator("a.button.primary")).toHaveCount(0);
});

import {test, expect, Page} from "@playwright/test";
import {execFileSync} from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import {dismissWelcome} from "./guide-helper";
const root = path.resolve(__dirname, "../..");
const python = process.platform === "win32" ? path.join(root, "backend/.venv/Scripts/python.exe") : path.join(root, "backend/.venv/bin/python");
const env = fs.readFileSync(path.join(root, ".env"), "utf8");
const code = process.env.DEMO_OPERATOR_CODE || env.match(/^DEMO_OPERATOR_CODE=(.+)$/m)?.[1].trim() || "";
const screenshots = path.join(root, "submission/evidence/screenshots");
fs.mkdirSync(screenshots, {recursive: true});
test.beforeEach(async ({context}) => {await context.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));});
function fixture() {return execFileSync(python, [path.join(root, "scripts/browser_fixture.py")], {encoding: "utf8"}).trim();}
async function checkout(page: Page) {
  const id = fixture();
  await page.goto(`/invoices/${id}`);
  await dismissWelcome(page);
  await expect(page.getByRole("heading", {name: "Hiểu rõ khoản phí của bạn"})).toBeVisible();
  await page.getByRole("link", {name: "Xem báo giá mô phỏng"}).click();
  await page.getByRole("button", {name: "Tạo báo giá mô phỏng"}).click();
  await expect(page.getByText("2.847.000 ₫", {exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Xác nhận thanh toán mô phỏng", exact: true})).toBeDisabled();
  return id;
}

test("desktop dashboard and mobile keyboard navigation", async ({page}) => {
  await page.setViewportSize({width: 1440, height: 1100});
  await page.goto("/");
  await dismissWelcome(page);
  await expect(page.getByRole("heading", {name: "Tài chính rõ ràng. Du học an tâm."})).toBeVisible();
  await expect(page.getByText("800.00").first()).toBeVisible();
  await page.screenshot({path: path.join(screenshots, "dashboard-desktop.png"), fullPage: true});
  await page.setViewportSize({width: 390, height: 844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("link", {name: "Lịch sử giao dịch", exact: true}).press("Enter");
  await expect(page).toHaveURL(/\/history$/, {timeout: 15000});
  await page.screenshot({path: path.join(screenshots, "history-mobile.png"), fullPage: true});
});

test("human consent, asynchronous signed success, duplicate, receipt", async ({page, context}) => {
  const consoleErrors: string[] = [];
  page.on("pageerror", e => consoleErrors.push(e.message));
  await checkout(page);
  await page.screenshot({path: path.join(screenshots, "checkout-desktop.png"), fullPage: true});
  await page.getByRole("checkbox").check();
  await page.getByRole("button", {name: "Xác nhận thanh toán mô phỏng", exact: true}).click();
  await expect(page).toHaveURL(/\/payments\//);
  await expect(page.getByText("Đang xử lý", {exact: true})).toBeVisible();
  const id = page.url().split("/").pop();
  const op = await context.newPage();
  await op.goto(`/operator?order=${id}`);
  await op.getByLabel("Mã DEMO_OPERATOR_CODE từ .env cục bộ").fill(code);
  await op.getByRole("button", {name: "Mở phiên vận hành"}).click();
  await op.getByRole("button", {name: "Phát sự kiện thành công", exact: true}).click();
  await expect(op.getByText(/Đã xếp hàng sự kiện/)).toBeVisible();
  await expect(page.getByText("Mô phỏng thành công", {exact: true})).toBeVisible({timeout: 15000});
  await op.getByRole("button", {name: "Phát lại sự kiện", exact: true}).click();
  await page.reload();
  await expect(page.getByText("Đã nhận trùng · không xử lý lại")).toBeVisible({timeout: 15000});
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", {name: "Xuất nhật ký JSON"}).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toContain("simulated-operation");
  await page.getByRole("link", {name: "Xem biên nhận mô phỏng"}).click();
  await expect(page.getByText("SIMULATED TRANSACTION — NO REAL FUNDS MOVED")).toBeVisible();
  await expect(page.getByText("DEMO - NOT AN ACTUAL PAYMENT")).toBeVisible();
  await page.screenshot({path: path.join(screenshots, "receipt-desktop.png"), fullPage: true});
  await page.emulateMedia({media: "print"});
  await page.screenshot({path: path.join(screenshots, "receipt-print.png"), fullPage: true});
  expect(consoleErrors).toEqual([]);
  await op.close();
});

test("mobile cancellation and safe retry", async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await checkout(page);
  await page.screenshot({path: path.join(screenshots, "checkout-mobile.png"), fullPage: true});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("button", {name: "Hủy trước khi xử lý"}).click();
  await expect(page.getByText("Đã hủy", {exact: true})).toBeVisible();
  await expect(page.getByRole("link", {name: "Xem biên nhận mô phỏng"})).toHaveCount(0);
  await page.getByRole("link", {name: "Tạo báo giá mới", exact: true}).click();
  await page.getByRole("button", {name: "Tạo báo giá mô phỏng"}).click();
  await expect(page.getByText("2.847.000 ₫", {exact: true})).toBeVisible();
});

test("failure has no receipt and operator code is verified", async ({page, context}) => {
  await checkout(page);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", {name: "Xác nhận thanh toán mô phỏng", exact: true}).click();
  await expect(page).toHaveURL(/\/payments\//);
  const id = page.url().split("/").pop();
  const op = await context.newPage();
  await op.goto(`/operator?order=${id}`);
  await op.getByLabel("Mã DEMO_OPERATOR_CODE từ .env cục bộ").fill("wrong-code");
  await op.getByRole("button", {name: "Mở phiên vận hành"}).click();
  await expect(op.getByRole("alert", {name: "Lỗi thao tác"})).toContainText("FORBIDDEN");
  await op.getByLabel("Mã DEMO_OPERATOR_CODE từ .env cục bộ").fill(code);
  await op.getByRole("button", {name: "Mở phiên vận hành"}).click();
  await op.getByRole("button", {name: "Phát sự kiện thất bại"}).click();
  await expect(page.getByText("Mô phỏng thất bại", {exact: true})).toBeVisible({timeout: 15000});
  await expect(page.getByRole("link", {name: "Xem biên nhận mô phỏng"})).toHaveCount(0);
  await page.screenshot({path: path.join(screenshots, "failure-desktop.png"), fullPage: true});
  await op.close();
});

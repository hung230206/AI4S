import {test, expect, Page} from "@playwright/test";
import {dismissWelcome} from "./guide-helper";
import {randomUUID} from "node:crypto";
import fs from "node:fs";
import path from "node:path";
const evidence = path.resolve(__dirname, "../../submission/evidence/screenshots/ux");
fs.mkdirSync(evidence, {recursive: true});

async function firstVisit(page: Page) {
  await page.goto("/");
  await page.getByRole("button", {name: "Tạo tài khoản", exact: true}).click();
  await page.getByLabel("Họ và tên", {exact: true}).fill("UX Test User");
  await page.getByLabel("Email", {exact: true}).fill(`ux-${randomUUID()}@example.com`);
  await page.getByLabel("Mật khẩu", {exact: true}).fill("ux-browser-test-password-2026");
  await page.getByRole("button", {name: "Đăng ký tài khoản", exact: true}).click();
  await dismissWelcome(page);
  await page.getByRole("button", {name: "Mở hướng dẫn sử dụng"}).click();
  const guide = page.getByRole("dialog", {name: "Bắt đầu cùng Demo"});
  await expect(guide).toBeVisible();
  return guide;
}

test("first-use guide traps focus, skips, stays dismissed and reopens on a narrow phone", async ({page}) => {
  await page.setViewportSize({width: 320, height: 740});
  const guide = await firstVisit(page);
  await expect(guide.getByRole("heading", {name: "Bạn muốn làm gì trước?"})).toBeVisible();
  expect(await guide.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.screenshot({path: path.join(evidence, "welcome-mobile.png")});
  for (let i = 0; i < 30; i++) {
    await page.keyboard.press("Tab");
    expect(await guide.evaluate(element => element.contains(document.activeElement))).toBe(true);
  }
  for (let i = 0; i < 30; i++) {await page.keyboard.press("Shift+Tab"); expect(await guide.evaluate(element => element.contains(document.activeElement))).toBe(true);}
  await page.keyboard.press("Escape");
  await expect(guide).not.toBeVisible();
  const help = page.getByRole("button", {name: "Mở hướng dẫn sử dụng"});
  await expect(help).toBeFocused();
  await page.reload();
  await expect(page.getByRole("heading", {name: "Bạn muốn làm gì hôm nay?"})).toBeVisible();
  await expect(guide).not.toBeVisible();
  await help.click();
  await guide.getByRole("button", {name: "Hóa đơn & tỷ giá", exact: true}).click();
  await expect(guide.getByRole("heading", {name: "Biết cần chuẩn bị bao nhiêu VND"})).toBeVisible();
  await guide.getByRole("button", {name: "Để sau", exact: true}).click();
  await expect(help).toBeFocused();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path: path.join(evidence, "dashboard-mobile.png"), fullPage: true});
});

test("guided invoice journey explains inputs and calculates a quote without a payment", async ({page}) => {
  await page.setViewportSize({width: 1440, height: 1000});
  const guide = await firstVisit(page);
  await page.screenshot({path: path.join(evidence, "welcome-desktop.png")});
  await guide.getByRole("button", {name: "Để sau", exact: true}).click();
  await page.screenshot({path: path.join(evidence, "dashboard-desktop.png"), fullPage: true});
  await page.getByRole("button", {name: "Mở hướng dẫn sử dụng"}).click();
  await guide.getByRole("link", {name: /Tính chi phí bằng VND/}).click();
  await expect(page).toHaveURL(/\/invoices\/new$/);
  await page.getByText("Tôi lấy thông tin hóa đơn ở đâu?", {exact: true}).click();
  await expect(page.getByText(/Đơn vị phát hành là nơi gửi thông báo/)).toBeVisible();
  await page.getByLabel("Mã hóa đơn", {exact: true}).fill(`UX-${randomUUID().slice(0, 8)}`);
  await page.getByLabel("Đơn vị phát hành", {exact: true}).fill("UX test issuer");
  await page.getByLabel("Bên nhận theo hóa đơn", {exact: true}).fill("UX test beneficiary");
  await page.getByLabel("Số tiền (CNY)", {exact: true}).fill("800.00");
  const due = new Date(); due.setDate(due.getDate() + 30);
  await page.getByLabel("Hạn thanh toán", {exact: true}).fill(due.toISOString().slice(0, 10));
  await page.screenshot({path: path.join(evidence, "invoice-help-desktop.png"), fullPage: true});
  await page.getByRole("button", {name: "Lưu hóa đơn", exact: true}).click();
  await page.getByRole("link", {name: "Xem giá trị VND", exact: true}).click();
  await page.getByRole("button", {name: "Lấy tỷ giá và tính VND", exact: true}).click();
  await expect(page.getByText("FRANKFURTER", {exact: true})).toBeVisible();
  await expect(page.getByText("Đã có giá trị VND để tham khảo", {exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Chạy thử thanh toán sandbox", exact: true})).toBeDisabled();
  const response = await page.request.get("/api/v1/orders");
  expect(response.ok()).toBe(true);
  expect((await response.json()).items).toEqual([]);
  await page.screenshot({path: path.join(evidence, "quote-next-step.png"), fullPage: true});
  await page.getByRole("link", {name: "Lịch sử giao dịch", exact: true}).click();
  await page.getByText("Vì sao tính VND rồi mà lịch sử vẫn trống?", {exact: true}).click();
  await expect(page.getByText(/Lịch sử chỉ lưu giao dịch khi bạn chọn thử/)).toBeVisible();
});

test("insurance entry opens its own workflow and route-specific help without an invoice", async ({page}) => {
  const guide = await firstVisit(page);
  await guide.getByRole("link", {name: /Hiểu tài liệu bảo hiểm/}).click();
  await expect(page).toHaveURL(/\/assistant$/);
  await expect(page.getByRole("heading", {name: "1. Tải tài liệu lên"})).toBeVisible();
  await expect(page.getByRole("button", {name: "Tìm trong tài liệu", exact: true})).toBeDisabled();
  await page.getByRole("button", {name: "Mở hướng dẫn sử dụng"}).click();
  await expect(guide.getByRole("heading", {name: "Tìm điều khoản trong tài liệu của bạn"})).toBeVisible();
  await guide.getByRole("button", {name: "Đóng hướng dẫn"}).click();
  await expect(page.getByRole("button", {name: "Mở hướng dẫn sử dụng"})).toBeFocused();
  await page.getByText("Tôi nên tải tệp nào và tìm thế nào?", {exact: true}).click();
  await expect(page.getByText(/Dùng hợp đồng hoặc chính sách bảo hiểm trường/)).toBeVisible();
  await page.screenshot({path: path.join(evidence, "documents-help.png"), fullPage: true});
});

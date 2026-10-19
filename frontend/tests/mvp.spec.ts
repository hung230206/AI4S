import {test, expect, Page} from "@playwright/test";
import path from "node:path";
import fs from "node:fs";
import {randomUUID} from "node:crypto";
import {dismissWelcome} from "./guide-helper";
const screenshotDir = path.resolve(__dirname, "../../submission/evidence/screenshots/mvp");
fs.mkdirSync(screenshotDir, {recursive: true});
const password = "browser-test-password-2026";

async function register(page: Page) {
  const email = `browser-${randomUUID()}@example.com`;
  await page.goto("/");
  await page.getByRole("button", {name: "Tạo tài khoản", exact: true}).click();
  await page.getByLabel("Họ và tên").fill("MVP Browser User");
  await page.getByLabel("Email", {exact: true}).fill(email);
  await page.getByLabel("Mật khẩu", {exact: true}).fill(password);
  await page.getByRole("button", {name: "Đăng ký tài khoản", exact: true}).click();
  await dismissWelcome(page);
  await expect(page.getByRole("heading", {name: "Bạn muốn làm gì hôm nay?"})).toBeVisible();
  return email;
}

async function newInvoice(page: Page) {
  await page.getByRole("link", {name: "Xem các khoản phí", exact: true}).first().click();
  await page.getByLabel("Mã hóa đơn", {exact: true}).fill(`BROWSER-${randomUUID().slice(0, 8)}`);
  await page.getByLabel("Đơn vị phát hành", {exact: true}).fill("Institution from uploaded notice");
  await page.getByLabel("Bên nhận theo hóa đơn", {exact: true}).fill("Recipient from uploaded notice");
  await page.getByLabel("Số tiền (CNY)", {exact: true}).fill("800.00");
  const due = new Date(); due.setDate(due.getDate() + 30);
  await page.getByLabel("Hạn thanh toán", {exact: true}).fill(due.toISOString().slice(0, 10));
  await page.getByLabel("Ghi chú", {exact: true}).fill("QA data for validating the invoice input workflow.");
  await page.getByRole("button", {name: "Lưu hóa đơn", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Hiểu rõ khoản phí của bạn"})).toBeVisible();
}

test("account registration, persistent session, profile and sign-out", async ({page}) => {
  await page.goto("/");
  await page.screenshot({path: path.join(screenshotDir, "sign-in.png"), fullPage: true});
  const email = await register(page);
  await expect(page.getByText("Chưa có việc đang làm dở. Chọn một nhu cầu phía trên để bắt đầu.", {exact: true})).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", {name: "Bạn muốn làm gì hôm nay?"})).toBeVisible();
  await expect(page.locator(".goal-card")).toHaveCount(3);
  await page.screenshot({path: path.join(screenshotDir, "private-dashboard.png"), fullPage: true});
  await page.getByRole("link", {name: "Tài khoản", exact: true}).click();
  await page.getByLabel("Tên hiển thị", {exact: true}).fill("Updated Browser User");
  await page.getByRole("button", {name: "Lưu thông tin", exact: true}).click();
  await expect(page.getByText("Đã cập nhật tên hiển thị.", {exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Đăng xuất", exact: true}).first().click();
  await page.getByLabel("Email", {exact: true}).fill(email);
  await page.getByLabel("Mật khẩu", {exact: true}).fill(password);
  await page.getByRole("button", {name: "Đăng nhập", exact: true}).last().click();
  await expect(page.getByRole("heading", {name: "Tài khoản của bạn"})).toBeVisible();
  await expect(page.getByLabel("Tên hiển thị", {exact: true})).toHaveValue("Updated Browser User");
});

test("invoice CRUD, real reference quote, sandbox consent and archive", async ({page}) => {
  await register(page);
  await newInvoice(page);
  await page.getByRole("link", {name: "Chỉnh sửa", exact: true}).click();
  await page.getByLabel("Số tiền (CNY)", {exact: true}).fill("850.50");
  await page.getByRole("button", {name: "Lưu hóa đơn", exact: true}).click();
  await expect(page.locator(".invoice-amount").filter({hasText: "850.50"})).toBeVisible();
  const detail = page.url();
  await page.getByRole("link", {name: "Xem giá trị VND", exact: true}).click();
  await page.getByRole("button", {name: "Lấy tỷ giá và tính VND", exact: true}).click();
  await expect(page.getByText("FRANKFURTER", {exact: true})).toBeVisible({timeout: 20000});
  await expect(page.getByRole("button", {name: "Chạy thử thanh toán sandbox", exact: true})).toBeDisabled();
  await expect(page.getByText(/Ngày dữ liệu:/)).toBeVisible();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", {name: "Cập nhật báo giá", exact: true}).click();
  await expect(page.getByRole("checkbox")).not.toBeChecked();
  await page.screenshot({path: path.join(screenshotDir, "reference-quote.png"), fullPage: true});
  await page.getByRole("link", {name: "Lịch sử giao dịch", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Chưa có giao dịch phù hợp"})).toBeVisible();
  await page.goto(detail);
  await page.getByRole("button", {name: "Lưu trữ", exact: true}).click();
  await page.getByRole("button", {name: "Xác nhận lưu trữ", exact: true}).click();
  await expect(page.getByText("Hóa đơn đã được lưu trữ, không tạo thêm báo giá.", {exact: true})).toBeVisible();
  await page.getByRole("link", {name: "Danh sách hóa đơn", exact: true}).click();
  await page.getByLabel("Trạng thái hóa đơn", {exact: true}).selectOption("VOID");
  await expect(page.locator(".invoice-amount").filter({hasText: "850.50"})).toBeVisible();
});

test("private policy upload, cited search, download and delete on mobile", async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await register(page);
  await page.goto("/insurance");
  await page.getByRole("link", {name: "Tài liệu bảo hiểm", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Chưa có tài liệu", exact: true})).toBeVisible();
  await page.getByLabel("Tệp chính sách (PDF, ảnh, TXT hoặc MD)", {exact: true}).setInputFiles({name: "browser-policy.txt", mimeType: "text/plain", buffer: Buffer.from("QA policy document. Annual premium CNY 800.\n\nClaims require hospital invoices and a completed claim form.\n\nExclusions: elective cosmetic treatment.")});
  await page.getByLabel("Tên tài liệu", {exact: true}).fill("Browser uploaded policy");
  await page.getByRole("button", {name: "Tải lên và trích xuất", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Browser uploaded policy", exact: true})).toBeVisible();
  await page.getByLabel("Câu hỏi hoặc từ khóa", {exact: true}).fill("hồ sơ bồi thường");
  await page.getByRole("button", {name: "Tìm trong tài liệu", exact: true}).click();
  await expect(page.getByText("NGUỒN TÀI LIỆU · TRANG 1", {exact: true})).toBeVisible();
  await expect(page.getByRole("blockquote")).toContainText("hospital invoices");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path: path.join(screenshotDir, "policy-citations-mobile.png"), fullPage: true});
  const download = page.waitForEvent("download");
  await page.getByRole("button", {name: "Tải xuống Browser uploaded policy", exact: true}).click();
  expect((await download).suggestedFilename()).toBe("browser-policy.txt");
  await page.getByRole("button", {name: "Xóa Browser uploaded policy", exact: true}).click();
  await page.getByRole("button", {name: "Xác nhận xóa", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Chưa có tài liệu", exact: true})).toBeVisible();
});

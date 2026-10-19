import {test, expect, Page} from "@playwright/test";
import {randomUUID} from "node:crypto";
import {execFileSync} from "node:child_process";
import path from "node:path";
import fs from "node:fs";
import {dismissWelcome, openAssistant} from "./guide-helper";
const root = path.resolve(__dirname, "../..");
const python = path.join(root, process.platform === "win32" ? "backend/.venv/Scripts/python.exe" : "backend/.venv/bin/python");
const screenshots = path.join(root, "submission/evidence/screenshots/student-finance");
fs.mkdirSync(screenshots, {recursive: true});
execFileSync(python, [path.join(root, "scripts/create_student_finance_fixtures.py")]);

async function register(page: Page) {
  await page.route("**/api/v1/finance/assistant/status", route => route.fulfill({json: {gemini_configured: false, model: null}}));
  await page.goto("/");
  await page.getByRole("button", {name: "Tạo tài khoản", exact: true}).click();
  await page.getByLabel("Họ và tên", {exact: true}).fill("Student Finance QA");
  await page.getByLabel("Email", {exact: true}).fill(`student-${randomUUID()}@example.com`);
  await page.getByLabel("Mật khẩu", {exact: true}).fill("student-finance-browser-2026");
  await page.getByRole("button", {name: "Đăng ký tài khoản", exact: true}).click();
  await dismissWelcome(page);
}

async function newWallet(page: Page, name: string, balance: string) {
  await page.goto("/finance");
  await page.getByLabel("Tên nhóm tiền", {exact: true}).fill(name);
  await page.getByLabel("Tiền bạn đang có", {exact: true}).fill(balance);
  await page.getByRole("button", {name: "Lưu số tiền ban đầu", exact: true}).click();
  await expect(page.getByRole("heading", {name, exact: true, level: 2})).toBeVisible();
}

test("native ledger, planned shortfall, actual confirmation and bounded assistant", async ({page}) => {
  await register(page);
  await newWallet(page, "Sinh hoạt CNY", "1000.00");
  await page.getByRole("button", {name: "Sắp thu / chi", exact: true}).click();
  await page.getByLabel("Nội dung thu / chi", {exact: true}).fill("Tiền nhà tháng tới");
  await page.getByLabel("Số tiền thu / chi", {exact: true}).fill("1200.00");
  const due = new Date(); due.setDate(due.getDate() + 5);
  await page.getByLabel("Ngày dự kiến", {exact: true}).fill(due.toISOString().slice(0, 10));
  await page.getByLabel("Nhóm khoản tiền", {exact: true}).selectOption("HOUSING");
  await page.getByRole("button", {name: "Lưu khoản sắp thu / chi", exact: true}).click();
  await expect(page.getByRole("status")).toContainText("Số dư hiện tại chưa thay đổi");
  await page.getByRole("button", {name: "Dự kiến còn lại", exact: true}).click();
  await expect(page.getByText(/có thể thiếu tiền từ/)).toBeVisible();
  await expect(page.getByText("−200,00 CNY", {exact: true}).first()).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({path: path.join(screenshots, "forecast-shortfall-desktop.png"), fullPage: true});
  await page.getByRole("button", {name: "Ghi nhận đã chi", exact: true}).click();
  await expect(page.getByRole("group", {name: "Xác nhận khoản thực tế"})).toBeVisible();
  await page.getByRole("button", {name: "Xác nhận ghi sổ", exact: true}).click();
  await expect(page.getByRole("status")).toContainText("không thực hiện thanh toán");
  const orders = await page.request.get("/api/v1/orders");
  expect((await orders.json()).items).toEqual([]);
  await page.getByRole("button", {name: "Đã thu / chi", exact: true}).click();
  await expect(page.getByText("Tiền nhà tháng tới", {exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Hủy ghi nhận", exact: true}).click();
  await page.getByRole("button", {name: "Xác nhận hủy ghi nhận", exact: true}).click();
  await expect(page.getByRole("status")).toContainText("Đã hủy ghi nhận");
  await openAssistant(page);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("30 ngày tới tôi có đủ tiền không?"); await page.keyboard.press("Enter");
  await expect(page.locator(".assistant-answer")).toContainText("-200.00 CNY");
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Thanh toán ngay giúp tôi");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".assistant-answer").last()).toContainText("Tôi không tự chuyển tiền");
  await page.setViewportSize({width: 390, height: 844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({path: path.join(screenshots, "copilot-mobile.png"), fullPage: true});
});

test("real image OCR, mandatory review, source download, invoice plan and FX analysis", async ({page}) => {
  await register(page);
  await page.goto("/invoices/new");
  await page.getByLabel("Tệp hóa đơn", {exact: true}).setInputFiles(path.join(root, ".local/qa-documents/invoice-ocr.png"));
  await page.getByRole("button", {name: "Đọc và điền thông tin", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.getByLabel("Mã hóa đơn", {exact: true})).toHaveValue("STUDENT-OCR-2026", {timeout: 75000});
  await expect(page.getByLabel("Số tiền (CNY)", {exact: true})).toHaveValue("800.00");
  const save = page.getByRole("button", {name: "Lưu hóa đơn", exact: true});
  await expect(save).toBeDisabled();
  await page.getByLabel("Loại khoản phí", {exact: true}).selectOption("TUITION");
  await page.getByRole("checkbox", {name: "Tôi đã đối chiếu số tiền, bên nhận, mã hóa đơn và hạn thanh toán với tệp gốc.", exact: true}).check();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({path: path.join(screenshots, "ocr-review-desktop.png"), fullPage: true});
  await save.click();
  await expect(page.getByRole("heading", {name: "Học phí", exact: true})).toBeVisible();
  const invoiceUrl = page.url(); const invoiceId = invoiceUrl.split("/").pop()!;
  await page.getByText("Chứng từ gốc và nội dung đã đọc", {exact: true}).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", {name: "Tải chứng từ gốc", exact: true}).click();
  expect((await downloadPromise).suggestedFilename()).toBe("invoice-ocr.png");
  await newWallet(page, "Học phí CNY", "1000");
  await page.goto(invoiceUrl);
  await page.getByRole("button", {name: "Đưa vào kế hoạch chi", exact: true}).click();
  await expect(page.getByRole("status")).toContainText("Chưa ghi nhận chi hoặc thanh toán");
  await page.goto("/rates");
  await page.getByLabel("Lấy số tiền từ hóa đơn", {exact: true}).selectOption(invoiceId);
  await expect(page.getByLabel("Khoản phí cần chuẩn bị (CNY)", {exact: true})).toHaveValue("800.00");
  await page.getByLabel("Ngân sách tối đa (VND, tùy chọn)", {exact: true}).fill("3100000");
  await page.getByRole("button", {name: "Phân tích ngân sách", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Ngân sách thay đổi thế nào?"})).toBeVisible();
  await expect(page.locator(".scenario-grid article")).toHaveCount(3);
  await expect(page.getByText(/Kịch bản tác động ±5%/)).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({path: path.join(screenshots, "fx-budget-desktop.png"), fullPage: true});
});

test("scanned policy PDF OCR produces a cited answer on a phone", async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await register(page);
  await page.goto("/assistant");
  await page.getByLabel("Tệp chính sách (PDF, ảnh, TXT hoặc MD)", {exact: true}).setInputFiles(path.join(root, ".local/qa-documents/policy-scanned.pdf"));
  await page.getByLabel("Tên tài liệu", {exact: true}).fill("Scanned QA policy");
  await page.getByRole("button", {name: "Tải lên và trích xuất", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Scanned QA policy", exact: true})).toBeVisible({timeout: 75000});
  await openAssistant(page);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Hồ sơ bồi thường gồm những gì?"); await page.keyboard.press("Enter");
  await expect(page.locator(".assistant-answer")).toBeVisible();
  await page.locator(".assistant-sources summary").click();
  const ownedSource = page.locator(".assistant-sources > div").filter({hasText: "Scanned QA policy"});
  await expect(ownedSource).toContainText("hospital invoices");
  await expect(ownedSource).toContainText("Trang 1");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({path: path.join(screenshots, "policy-ocr-citation-mobile.png"), fullPage: true});
});

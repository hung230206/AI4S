import {test, expect as defaultExpect, Page} from "@playwright/test";
import path from "node:path";
import fs from "node:fs";
import {randomUUID} from "node:crypto";
import {dismissWelcome} from "./guide-helper";

const expect = defaultExpect.configure({timeout: 30000});
const root = path.resolve(__dirname, "../..");
const screenshots = path.join(root, "submission/evidence/screenshots/acceptance");
fs.mkdirSync(screenshots, {recursive: true});

test.use({video: process.env.ACCEPTANCE_VIDEO ? {mode: "on", size: {width: 1280, height: 720}} : "off"});
test.afterEach(async ({page}, info) => {
  if (process.env.ACCEPTANCE_VIDEO && info.status === "passed") {
    const video = page.video();
    await page.context().close();
    if (video) await video.saveAs(path.join(root, "submission/evidence", info.title.startsWith("owner completes") ? "demo-a-z.webm" : "demo-decline-retry.webm"));
  }
});

async function register(page: Page) {
  await page.goto("/");
  await page.getByRole("button", {name: "Tạo tài khoản", exact: true}).click();
  await page.getByLabel("Họ và tên", {exact: true}).fill("Acceptance Test Student");
  await page.getByLabel("Email", {exact: true}).fill(`acceptance-${randomUUID()}@example.com`);
  await page.getByLabel("Mật khẩu", {exact: true}).fill("acceptance-browser-test-2026");
  await page.getByRole("button", {name: "Đăng ký tài khoản", exact: true}).click();
  await dismissWelcome(page);
}

async function importInvoice(page: Page, filename: string, amount: string) {
  await page.goto("/invoices/new");
  await page.getByLabel("Tệp hóa đơn", {exact: true}).setInputFiles(path.join(root, "fixtures/uploads/01_Hoa_don", filename));
  await page.getByLabel("Ngôn ngữ hóa đơn", {exact: true}).selectOption("en");
  await page.getByRole("button", {name: "Đọc và điền thông tin", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.getByLabel("Số tiền (CNY)", {exact: true})).toHaveValue(amount, {timeout: 75000});
  await expect(page.getByRole("button", {name: "Lưu hóa đơn", exact: true})).toBeDisabled();
  await page.getByRole("checkbox", {name: "Tôi đã đối chiếu số tiền, bên nhận, mã hóa đơn và hạn thanh toán với tệp gốc.", exact: true}).check();
  await page.getByRole("button", {name: "Lưu hóa đơn", exact: true}).click();
  await expect(page).toHaveURL(/\/invoices\/[0-9a-f-]{36}$/, {timeout: 30000});
  return page.url();
}

test("owner completes upload, budget, policy, automatic signed payment, ledger and evidence", async ({page}) => {
  test.setTimeout(150000);
  await register(page);
  await page.getByRole("link", {name: /Chưa có tài liệu\? Tải tệp mẫu để thử/}).click();
  await expect(page.getByRole("heading", {name: "Test trọn luồng từ A đến Z"})).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", {name: "Tải toàn bộ dữ liệu mẫu ZIP", exact: true}).click();
  expect((await download).suggestedFilename()).toBe("Demo_Upload_Test.zip");
  await page.screenshot({path: path.join(screenshots, "test-lab-desktop.png"), fullPage: true});
  const invoiceUrl = await importInvoice(page, "01_en_800.png", "800.00");
  const invoiceId = invoiceUrl.split("/").pop();
  await page.goto("/finance");
  await page.getByLabel("Tên nhóm tiền", {exact: true}).fill("Acceptance CNY");
  await page.getByLabel("Tiền bạn đang có", {exact: true}).fill("1000");
  await page.getByRole("button", {name: "Lưu số tiền ban đầu", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Acceptance CNY", exact: true, level: 2})).toBeVisible();
  await page.goto(invoiceUrl);
  await page.getByRole("button", {name: "Đưa vào kế hoạch chi", exact: true}).click();
  await expect(page.getByRole("status")).toContainText("Chưa ghi nhận chi hoặc thanh toán");
  await page.goto("/assistant");
  await page.getByLabel("Tệp chính sách (PDF, ảnh, TXT hoặc MD)", {exact: true}).setInputFiles(path.join(root, "fixtures/uploads/02_Bao_hiem/01_policy_vi_text.pdf"));
  await page.getByLabel("Loại nguồn tài liệu", {exact: true}).selectOption("TEST_FIXTURE");
  await page.getByLabel("Tên tài liệu", {exact: true}).fill("Acceptance self-authored policy");
  await page.getByRole("button", {name: "Tải lên và trích xuất", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Acceptance self-authored policy", exact: true})).toBeVisible();
  await page.getByLabel("Câu hỏi hoặc từ khóa", {exact: true}).fill("hồ sơ bồi thường");
  await page.getByRole("button", {name: "Tìm trong tài liệu", exact: true}).click();
  await expect(page.getByText("NGUỒN TÀI LIỆU · TRANG 2", {exact: true}).first()).toBeVisible();
  await page.goto(`/checkout/${invoiceId}`);
  await page.getByRole("button", {name: "Lấy tỷ giá và tính VND", exact: true}).click();
  await expect(page.getByLabel("Phương thức thử thanh toán", {exact: true})).toHaveValue("SUCCESS");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", {name: "Chạy thử thanh toán sandbox", exact: true}).click();
  await expect(page).toHaveURL(/\/payments\//);
  await expect(page.getByText("Mô phỏng thành công", {exact: true})).toBeVisible({timeout: 20000});
  await expect(page.getByText("Chữ ký: đã xác minh", {exact: true})).toBeVisible();
  await page.screenshot({path: path.join(screenshots, "automatic-success-desktop.png"), fullPage: true});
  const orderUrl = page.url();
  await page.getByRole("link", {name: "Xem biên nhận mô phỏng", exact: true}).click();
  await expect(page.locator(".receipt-warning")).toContainText("SIMULATED TRANSACTION — NO REAL FUNDS MOVED");
  await page.goto("/finance");
  await page.getByRole("button", {name: "Dự kiến còn lại", exact: true}).click();
  await page.getByRole("button", {name: "Ghi nhận đã chi", exact: true}).click();
  await page.getByRole("button", {name: "Xác nhận ghi sổ", exact: true}).click();
  await expect(page.getByRole("status")).toContainText("không thực hiện thanh toán");
  const balance = await page.request.get("/api/v1/finance/wallets");
  expect((await balance.json()).items[0].balance).toBe("200.00");
  await page.goto(orderUrl);
  const caseDownload = page.waitForEvent("download");
  await page.getByRole("button", {name: "Tải hồ sơ kiểm thử ZIP", exact: true}).click();
  expect((await caseDownload).suggestedFilename()).toMatch(/^demo-case-.*\.zip$/);
  await page.goto(`/test-lab?invoice=${invoiceId}`);
  await expect(page.getByText("Có bản ghi tương ứng", {exact: true})).toHaveCount(6);
  await page.setViewportSize({width: 390, height: 844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path: path.join(screenshots, "completed-journey-mobile.png"), fullPage: true});
});

test("declined test method requires renewed consent and allows a successful retry", async ({page}) => {
  test.setTimeout(100000);
  await register(page);
  const invoiceUrl = await importInvoice(page, "06_en_675.txt", "675.50");
  const id = invoiceUrl.split("/").pop();
  await page.goto(`/checkout/${id}`);
  await page.getByRole("button", {name: "Lấy tỷ giá và tính VND", exact: true}).click();
  await page.getByRole("checkbox").check();
  await page.getByLabel("Phương thức thử thanh toán", {exact: true}).selectOption("DECLINED");
  await expect(page.getByRole("checkbox")).not.toBeChecked();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", {name: "Chạy thử thanh toán sandbox", exact: true}).click();
  await expect(page.getByText("Mô phỏng thất bại", {exact: true})).toBeVisible({timeout: 20000});
  await expect(page.getByRole("link", {name: "Xem biên nhận mô phỏng"})).toHaveCount(0);
  await page.getByRole("link", {name: "Tạo báo giá mới", exact: true}).click();
  await page.getByRole("button", {name: "Lấy tỷ giá và tính VND", exact: true}).click();
  await page.getByLabel("Phương thức thử thanh toán", {exact: true}).selectOption("SUCCESS");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", {name: "Chạy thử thanh toán sandbox", exact: true}).click();
  await expect(page.getByText("Mô phỏng thành công", {exact: true})).toBeVisible({timeout: 20000});
});

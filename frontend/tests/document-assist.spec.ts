import {test, expect, type Page} from "@playwright/test";
import {randomUUID} from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import {dismissWelcome} from "./guide-helper";

const root = path.resolve(__dirname, "../..");
const files = path.join(root, "fixtures/china_upload_samples");
const shots = path.join(root, "submission/evidence/screenshots/document-assist");
fs.mkdirSync(shots, {recursive: true});

async function account(page: Page) {
  await page.goto("/"); await page.getByRole("button", {name: "Tạo tài khoản", exact: true}).click();
  await page.getByLabel("Họ và tên", {exact: true}).fill("Document assist QA");
  await page.getByLabel("Email", {exact: true}).fill(`doc-assist-${randomUUID()}@example.com`);
  await page.getByLabel("Mật khẩu", {exact: true}).fill("Fictional-doc-assist-test-2026");
  await page.getByRole("button", {name: "Đăng ký tài khoản", exact: true}).click(); await dismissWelcome(page);
}
async function agree(page: Page) {
  await page.getByRole("dialog").getByRole("button", {name: "Đồng ý", exact: true}).click();
}

test("real PDF fills policy without JSON, keeps review gate, preserves edits, and prefills claim", async ({page}) => {
  test.setTimeout(120000);
  const errors: string[] = []; page.on("pageerror", e => errors.push(e.message));
  await account(page); await page.goto("/insurance");
  await expect(page.locator(".insurance-samples")).toContainText("10 chứng từ Trung Quốc");
  await page.getByRole("button", {name: "Thêm hợp đồng", exact: true}).click();
  await expect(page.getByLabel("Ngày bắt đầu", {exact: true})).toHaveValue("");
  await page.getByLabel("Tệp hợp đồng (PDF, ảnh, TXT)", {exact: true}).setInputFiles(path.join(files, "04_Hop_dong_bao_hiem.pdf"));
  await page.locator(".insurance-source-upload select").selectOption("TEST_FIXTURE");
  await page.getByRole("button", {name: "Tải lên và đọc tài liệu", exact: true}).click(); await agree(page);
  await expect(page.getByLabel("Tên hợp đồng", {exact: true})).toHaveValue("留学生综合保险 / Student insurance schedule", {timeout: 20000});
  await expect(page.getByLabel("Phí bảo hiểm", {exact: true})).toHaveValue("800.00");
  await expect(page.getByLabel("Ngày bắt đầu", {exact: true})).toHaveValue("2026-09-01");
  await expect(page.getByLabel("Ngày kết thúc", {exact: true})).toHaveValue("2027-08-31");
  await expect(page.getByLabel("Ngoại trú · Hạn mức (trống = chưa rõ)", {exact: true})).toHaveValue("5000.00");
  await expect(page.getByLabel("Nội trú · Tỷ lệ chi trả %", {exact: true})).toHaveValue("100");
  await expect(page.getByLabel("Vận chuyển y tế · Nhóm quyền lợi", {exact: true})).toHaveValue("EXCLUDED");
  await expect(page.getByLabel("Ngoại trú · Trang", {exact: true})).toHaveValue("2");
  await expect(page.getByRole("button", {name: "Lưu sau khi đối chiếu", exact: true})).toBeDisabled();
  expect((await (await page.request.get("/api/v1/insurance/policies")).json()).items).toHaveLength(0);
  await page.getByText("Xem căn cứ tự điền", {exact: true}).click();
  await page.locator(".insurance-editor").screenshot({path: path.join(shots, "policy-filled-evidence.png")});
  await page.getByRole("checkbox", {name: /Tôi đã đối chiếu các trường/}).check();
  await page.getByRole("button", {name: "Lưu sau khi đối chiếu", exact: true}).click();
  await expect(page.locator(".success")).toContainText("Đã lưu");
  await page.getByRole("button", {name: "Xem / sửa", exact: true}).click();
  await expect(page.getByLabel("Tên hợp đồng", {exact: true})).toHaveValue("留学生综合保险 / Student insurance schedule");
  await page.getByLabel("Tên hợp đồng", {exact: true}).fill("Tên đã đối chiếu của tôi");
  await page.getByRole("checkbox", {name: /Tôi đã đối chiếu các trường/}).check();
  await page.getByRole("button", {name: "Lưu sau khi đối chiếu", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Tên đã đối chiếu của tôi", exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Xem / sửa", exact: true}).click();
  await expect(page.getByLabel("Tên hợp đồng", {exact: true})).toHaveValue("Tên đã đối chiếu của tôi");
  await page.getByRole("button", {name: "Đóng biểu mẫu", exact: true}).click();
  await page.getByRole("tab", {name: "Hồ sơ bồi thường", exact: true}).click();
  await page.getByLabel("Hợp đồng", {exact: true}).selectOption({label: "Tên đã đối chiếu của tôi · CNY"});
  await page.getByLabel("Điền từ chứng từ y tế (tùy chọn)", {exact: true}).setInputFiles(path.join(files, "07_Don_yeu_cau_boi_thuong.pdf")); await agree(page);
  await expect(page.getByLabel("Chi phí phát sinh", {exact: true})).toHaveValue("980.00");
  await expect(page.getByLabel("Ngày phát sinh sự kiện", {exact: true})).toHaveValue("2026-10-11");
  await expect(page.getByRole("button", {name: "Tạo hồ sơ chuẩn bị", exact: true})).toBeDisabled();
  await page.getByRole("checkbox", {name: "Tôi đã kiểm tra thông tin từ chứng từ trước khi tạo hồ sơ.", exact: true}).check();
  await page.getByRole("button", {name: "Tạo hồ sơ chuẩn bị", exact: true}).click();
  await expect(page).toHaveURL(/\/insurance\/claims\/[0-9a-f-]{36}$/);
  await expect(page.getByRole("heading", {name: "Giấy ra viện", exact: true})).toBeVisible();
  // Deliberately attach the claim form to the invoice slot; automatic comparison must warn.
  const slot = page.locator(".insurance-checklist article").filter({has: page.getByRole("heading", {name: "Hóa đơn viện phí", exact: true})});
  await slot.locator("input[type=file]").setInputFiles(path.join(files, "07_Don_yeu_cau_boi_thuong.pdf")); await agree(page);
  await expect(slot).toContainText("Có thể đã đính kèm sai mục tài liệu");
  await page.setViewportSize({width: 390, height: 844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path: path.join(shots, "claim-comparison-mobile.png"), fullPage: true});
  expect(errors).toEqual([]);
});

test("three real Chinese images suggest all five invoice fields and the correct fee; paid bill is blocked", async ({page}) => {
  test.setTimeout(180000);
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo")); await page.goto("/"); await dismissWelcome(page);
  for (const [file, amount, fee] of [["01_Hoc_phi_CNY.png", "20000.00", "TUITION"], ["02_Tien_ky_tuc_xa_CNY.png", "6000.00", "ACCOMMODATION"], ["03_Phi_bao_hiem_CNY.png", "800.00", "ANNUAL_HEALTH_INSURANCE_PREMIUM"]]) {
    await page.goto("/invoices/new");
    await page.getByLabel("Tệp hóa đơn", {exact: true}).setInputFiles(path.join(files, file));
    await page.getByLabel("Ngôn ngữ hóa đơn", {exact: true}).selectOption("zh");
    await page.getByRole("button", {name: "Đọc và điền thông tin", exact: true}).click(); await agree(page);
    await expect(page.getByLabel("Số tiền (CNY)", {exact: true})).toHaveValue(amount, {timeout: 60000});
    await expect(page.getByLabel("Loại khoản phí", {exact: true})).toHaveValue(fee);
    await expect(page.locator(".success-note")).toContainText("5/5");
  }
  await page.goto("/invoices/new");
  await page.getByLabel("Tệp hóa đơn", {exact: true}).setInputFiles(path.join(files, "05_Hoa_don_vien_phi.pdf"));
  await page.getByRole("button", {name: "Đọc và điền thông tin", exact: true}).click(); await agree(page);
  await expect(page.getByRole("heading", {name: "Chứng từ hồ sơ hoặc khoản đã chi", exact: true})).toBeVisible({timeout: 20000});
  await expect(page.getByRole("button", {name: "Lưu hóa đơn", exact: true})).toHaveCount(0);
  await page.screenshot({path: path.join(shots, "paid-bill-handoff.png"), fullPage: true});
});

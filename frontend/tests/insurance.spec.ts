import {test, expect, type Page} from "@playwright/test";
import {randomUUID} from "node:crypto";
import {execFileSync} from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {dismissWelcome} from "./guide-helper";
import type {PortfolioPolicy} from "../src/lib/insurance";
const root = path.resolve(__dirname, "../..");
const python = path.join(root, process.platform === "win32" ? "backend/.venv/Scripts/python.exe" : "backend/.venv/bin/python");
const screenshots = path.join(root, "submission/evidence/screenshots/insurance");
fs.mkdirSync(screenshots, {recursive: true});
const consumerScreenshots = path.join(root, "submission/evidence/screenshots/consumer-insurance");
fs.mkdirSync(consumerScreenshots, {recursive: true});

// Fixture JSON belongs to the test harness. Users fill the ordinary form.
async function fillPolicyDetails(page: Page, folder: string) {
  const fields = JSON.parse(fs.readFileSync(path.join(folder, "review-fields.json"), "utf8")) as PortfolioPolicy;
  for (const [key, label] of [["name", "Tên hợp đồng"], ["insurer", "Đơn vị bảo hiểm (bạn khai báo)"], ["premium", "Phí bảo hiểm"], ["premium_due", "Hạn đóng phí"], ["starts_on", "Ngày bắt đầu"], ["ends_on", "Ngày kết thúc"]] as const) {
    await page.getByLabel(label, {exact: true}).fill(fields[key], {timeout: 8000});
  }
  await page.getByLabel("Tiền tệ", {exact: true}).selectOption(fields.currency, {timeout: 8000});
  await page.getByLabel("Phạm vi lãnh thổ", {exact: true}).selectOption(fields.territory, {timeout: 8000});
  const names: Record<string, string> = {OUTPATIENT: "Ngoại trú", INPATIENT: "Nội trú", ACCIDENT: "Tai nạn", EVACUATION: "Vận chuyển y tế"};
  for (const benefit of fields.benefits) {
    const name = names[benefit.kind];
    await page.getByLabel(`${name} · Nhóm quyền lợi`, {exact: true}).selectOption(benefit.status, {timeout: 8000});
    if (benefit.status === "INCLUDED") for (const [key, label] of [["limit", "Hạn mức (trống = chưa rõ)"], ["deductible", "Khấu trừ (trống = chưa rõ)"], ["reimbursement_percent", "Tỷ lệ chi trả %"], ["waiting_days", "Thời gian chờ (ngày)"]] as const) {
      await page.getByLabel(`${name} · ${label}`, {exact: true}).fill(benefit[key] === null ? "" : String(benefit[key]), {timeout: 8000});
    }
    await page.getByLabel(`${name} · Trang`, {exact: true}).fill(benefit.source_page === null ? "" : String(benefit.source_page), {timeout: 8000});
    await page.getByLabel(`${name} · Chép nguyên văn điều khoản`, {exact: true}).fill(benefit.evidence_quote, {timeout: 8000});
  }
}

async function setup(page: Page) {
  await page.goto("/");
  await page.getByRole("button", {name: "Tạo tài khoản", exact: true}).click();
  await page.getByLabel("Họ và tên", {exact: true}).fill("Insurance journey QA");
  await page.getByLabel("Email", {exact: true}).fill(`insurance-${randomUUID()}@example.com`);
  await page.getByLabel("Mật khẩu", {exact: true}).fill("insurance-browser-test-2026");
  await page.getByRole("button", {name: "Đăng ký tài khoản", exact: true}).click();
  await dismissWelcome(page);
  await page.getByRole("link", {name: "Xem bảo hiểm", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Bảo hiểm & hồ sơ", exact: true})).toBeVisible();
  await page.route("**/api/v1/insurance/sample-pack", async route => {const r = await page.request.get("/api/v1/insurance/sample-pack?edition=regression"); await route.fulfill({response: r});});
  const downloaded = page.waitForEvent("download");
  await page.locator(".insurance-samples").getByRole("button", {name: "Tải về", exact: true}).click();
  const download = await downloaded;
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), "demo-cd-"));
  const pack = path.join(folder, "samples.zip"); await download.saveAs(pack);
  execFileSync(python, ["-c", "import zipfile,sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])", pack, folder]);
  await page.getByRole("button", {name: "Thêm hợp đồng", exact: true}).click();
  await expect(page.locator(".insurance-source-upload select")).toHaveValue("USER_PROVIDED");
  await page.getByLabel("Tệp hợp đồng (PDF, ảnh, TXT)", {exact: true}).setInputFiles(path.join(folder, "demo-policy.txt"));
  await page.locator(".insurance-source-upload select").selectOption("TEST_FIXTURE");
  await page.getByRole("button", {name: "Tải lên và đọc tài liệu", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.getByText("Xem nội dung hợp đồng", {exact: false}).first()).toBeVisible({timeout: 30000});
  await fillPolicyDetails(page, folder);
  await expect(page.getByLabel("Phí bảo hiểm", {exact: true})).toHaveValue("800.00");
  await expect(page.getByRole("button", {name: "Lưu sau khi đối chiếu", exact: true})).toBeDisabled();
  await expect(page.locator('.insurance-editor input[accept*="json"]')).toHaveCount(0);
  await expect(page.locator(".insurance-workspace")).not.toContainText(/review-fields|JSON|Nạp trường/);
  for (const title of ["1. Chọn tài liệu hợp đồng", "2. Điền thông tin theo hợp đồng", "3. Kiểm tra và lưu"]) await expect(page.getByRole("heading", {name: title, exact: true})).toBeVisible();
  await page.locator(".insurance-editor").screenshot({path: path.join(consumerScreenshots, "policy-form-desktop.png"), animations: "disabled"});
  return folder;
}
async function savePolicy(page: Page) {
  await page.getByRole("checkbox", {name: "Tôi đã đối chiếu các trường với tài liệu, bao gồm thời hạn, số tiền, lãnh thổ và điều kiện quyền lợi.", exact: true}).check();
  await page.getByRole("button", {name: "Lưu sau khi đối chiếu", exact: true}).click();
  await expect(page.getByRole("status")).toContainText("Đã lưu");
}

test("combined C+D journey: reviewed source, gap, premium budget, signed sandbox and claim ZIP", async ({page}) => {
  test.setTimeout(180000);
  const errors: string[] = []; page.on("pageerror", e => errors.push(e.message));
  await page.setViewportSize({width: 1440, height: 1100});
  const folder = await setup(page); await savePolicy(page);
  await page.goto("/finance");
  await page.getByLabel("Tên nhóm tiền", {exact: true}).fill("Insurance CNY");
  await page.getByLabel("Tiền bạn đang có", {exact: true}).fill("1000");
  await page.getByRole("button", {name: "Lưu số tiền ban đầu", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Insurance CNY", exact: true, level: 2})).toBeVisible();
  await page.goto("/insurance");
  await page.getByRole("button", {name: "Dự trù phí vào ngân sách", exact: true}).click();
  await page.getByLabel("Sổ cùng tiền tệ", {exact: true}).selectOption({label: "Insurance CNY · 1000.00 CNY"});
  await page.getByRole("button", {name: "Xác nhận cập nhật", exact: true}).click();
  await expect(page.getByRole("status")).toContainText("Đã tạo kế hoạch phí");
  await page.goto("/finance");
  await page.getByRole("button", {name: "Dự kiến còn lại", exact: true}).click();
  await expect(page.getByText("200,00 CNY", {exact: true}).first()).toBeVisible();
  await page.goto("/insurance");
  await page.getByRole("tab", {name: "Kiểm tra quyền lợi", exact: true}).click();
  await page.getByRole("button", {name: "So sánh với hợp đồng đã lưu", exact: true}).click();
  await expect(page.locator(".insurance-analysis > article").filter({hasText: "Vận chuyển y tế"})).toContainText("Có khoảng trống trong dữ liệu đã nhập");
  await page.screenshot({path: path.join(screenshots, "coverage-gap-desktop.png"), fullPage: true});
  await page.getByRole("tab", {name: "Hợp đồng", exact: true}).click();
  await page.getByRole("button", {name: "Tạo dự trù phí để thử sandbox", exact: true}).click();
  await page.getByRole("button", {name: "Xác nhận cập nhật", exact: true}).click();
  await expect(page).toHaveURL(/\/invoices\/[0-9a-f-]{36}$/);
  await expect(page.getByText(/NOT AN INSURER-ISSUED INVOICE/)).toBeVisible();
  await page.getByRole("button", {name: "Đưa vào kế hoạch chi", exact: true}).click();
  const plans = await page.request.get("/api/v1/finance/plans"); expect((await plans.json()).items).toHaveLength(1);
  await page.getByRole("link", {name: "Xem giá trị VND", exact: true}).click();
  await page.getByRole("button", {name: "Lấy tỷ giá và tính VND", exact: true}).click();
  await expect(page.getByRole("combobox", {name: "Phương thức thử thanh toán", exact: true})).toHaveValue("SUCCESS");
  await page.getByRole("checkbox").check();
  await page.getByRole("button", {name: "Chạy thử thanh toán sandbox", exact: true}).click();
  await expect(page.getByText("Mô phỏng thành công", {exact: true})).toBeVisible({timeout: 30000});
  const next = page.locator("section").filter({has: page.getByRole("heading", {name: "Đã hoàn tất thanh toán mô phỏng", exact: true})});
  await expect(next.getByRole("link", {name: "Xem hợp đồng liên quan", exact: true})).toHaveAttribute("href", /\/insurance#policy-/);
  await page.getByRole("link", {name: "Xem biên nhận mô phỏng", exact: true}).click();
  await expect(page.getByText("SIMULATED TRANSACTION — NO REAL FUNDS MOVED")).toBeVisible();
  await page.goto("/insurance");
  await page.getByRole("tab", {name: "Hồ sơ bồi thường", exact: true}).click();
  await page.getByLabel("Hợp đồng", {exact: true}).selectOption({label: "Demo student health plan · CNY"});
  await page.getByLabel("Tên hồ sơ", {exact: true}).fill("Outpatient sample claim");
  await page.getByLabel("Chi phí phát sinh", {exact: true}).fill("500");
  await page.getByRole("button", {name: "Tạo hồ sơ chuẩn bị", exact: true}).click();
  await expect(page).toHaveURL(/\/insurance\/claims\/[0-9a-f-]{36}$/);
  const caseId = page.url().split("/").pop();
  for (const [code, filename] of [["Hóa đơn viện phí", "claim-invoice.txt"], ["Bệnh án / hồ sơ khám", "claim-medical-record.txt"], ["Đơn yêu cầu bồi thường", "claim-claim-form.txt"]]) {
    const item = page.locator(".insurance-checklist article").filter({has: page.getByRole("heading", {name: code, exact: true})});
    await item.locator("input[type=file]").setInputFiles(path.join(folder, filename));
  await page.getByRole("dialog").getByRole("button", {name: "Đồng ý", exact: true}).click();
    await expect(item.getByText(filename, {exact: true})).toBeVisible();
  }
  for (const label of ["Giấy tờ định danh: giữ bên ngoài", "Thông tin nhận tiền: giữ bên ngoài"]) {
    const item = page.locator(".insurance-checklist article").filter({has: page.getByRole("heading", {name: label, exact: true})});
    await item.getByRole("checkbox").check();
    await expect(item.getByRole("checkbox")).toBeEnabled();
  }
  await page.getByRole("button", {name: "Đối chiếu xong, đánh dấu đủ checklist", exact: true}).click();
  await page.getByRole("checkbox", {name: /Tôi xác nhận cập nhật trạng thái này/}).check();
  await page.getByRole("button", {name: "Xác nhận cập nhật", exact: true}).click();
  await expect(page.locator(".badge").getByText("Đủ checklist do bạn xác nhận", {exact: true})).toBeVisible();
  const zipped = page.waitForEvent("download");
  await page.getByRole("button", {name: "Xuất bộ hồ sơ ZIP", exact: true}).click();
  const exportFile = path.join(folder, "claim.zip"); await (await zipped).saveAs(exportFile);
  const report = JSON.parse(execFileSync(python, ["-c", "import zipfile,json,sys; z=zipfile.ZipFile(sys.argv[1]); print(z.read('claim-preparation.json').decode('utf-8'))", exportFile], {encoding: "utf-8"}));
  expect(report.status).toBe("READY"); expect(report.attachments).toHaveLength(3); expect(report.ready).toBe(true);
  await page.screenshot({path: path.join(screenshots, "claim-ready-desktop.png"), fullPage: true});
  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole("button", {name: "Giao diện", exact: true}).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path: path.join(screenshots, "claim-ready-mobile-dark.png"), fullPage: true});
  const detail = await page.request.get(`/api/v1/insurance/claims/${caseId}`); expect((await detail.json()).status).toBe("READY");
  expect(errors).toEqual([]);
});

test("review UI rejects invented clauses, supports corrections and localized mobile portfolio", async ({page}) => {
  test.setTimeout(100000);
  const folder = await setup(page);
  await page.getByLabel("Ngoại trú · Chép nguyên văn điều khoản", {exact: true}).fill("This clause is invented and cannot be found in the source.");
  await page.getByRole("checkbox", {name: /Tôi đã đối chiếu các trường/}).check();
  await page.getByRole("button", {name: "Lưu sau khi đối chiếu", exact: true}).click();
  await expect(page.getByRole("alert", {name: "Lỗi thao tác"})).toContainText("POLICY_CITATION_INVALID");
  await fillPolicyDetails(page, folder);
  await expect(page.getByLabel("Ngoại trú · Chép nguyên văn điều khoản", {exact: true})).toHaveValue(JSON.parse(fs.readFileSync(path.join(folder, "review-fields.json"), "utf8")).benefits[0].evidence_quote);
  await expect(page.getByRole("checkbox", {name: /Tôi đã đối chiếu các trường/})).not.toBeChecked();
  await page.setViewportSize({width: 390, height: 844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator(".insurance-editor").screenshot({path: path.join(consumerScreenshots, "policy-form-mobile.png"), animations: "disabled"});
  await savePolicy(page);
  await page.setViewportSize({width: 390, height: 844});
  await page.getByRole("button", {name: "English", exact: true}).click();
  await expect(page.getByRole("heading", {name: "Insurance & claims", exact: true})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("button", {name: "中文", exact: true}).click();
  await expect(page.getByRole("heading", {name: "保险与理赔材料", exact: true})).toBeVisible();
  await page.screenshot({path: path.join(screenshots, "portfolio-mobile-zh.png"), fullPage: true});
  await page.getByRole("button", {name: "Tiếng Việt", exact: true}).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

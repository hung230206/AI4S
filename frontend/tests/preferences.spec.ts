import {test, expect, Page} from "@playwright/test";
import {phrases} from "../src/lib/translations";
import path from "node:path";
import fs from "node:fs";

const translated = (text: string, locale: "en" | "zh") => phrases[text]?.[locale] || text;
const evidence = path.resolve(__dirname, "../../submission/evidence/screenshots/preferences");
fs.mkdirSync(evidence, {recursive: true});
async function demo(page: Page) {
  await page.goto("/");
  await page.getByRole("button", {name: "Dùng thử sandbox với dữ liệu mẫu", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Để sau", exact: true}).click();
  await expect(page.locator("main h1")).toBeVisible();
}

test("sign-in preferences preserve input, persist on reload, and synchronize tabs", async ({page, context}) => {
  const errors: string[] = [];
  page.on("pageerror", e => errors.push(e.message));
  page.on("console", msg => {if (msg.type() === "error" && /hydrat/i.test(msg.text())) errors.push(msg.text());});
  await page.goto("/");
  await page.getByLabel("Email", {exact: true}).fill("draft@example.com");
  await page.getByLabel("Mật khẩu", {exact: true}).fill("draft-password");
  await page.getByRole("button", {name: "English", exact: true}).click();
  await expect(page.getByRole("button", {name: "Sign in", exact: true}).first()).toBeVisible();
  await expect(page.getByLabel("Password", {exact: true})).toHaveValue("draft-password");
  await expect(page.getByLabel("Email", {exact: true})).toHaveValue("draft@example.com");
  await page.getByLabel("Appearance", {exact: true}).selectOption("dark");
  await expect(page.locator("html")).toHaveClass(/dark/);
  await page.reload();
  await expect(page.getByRole("button", {name: "English", exact: true})).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Appearance", {exact: true})).toHaveValue("dark");
  await expect(page.getByLabel("Password", {exact: true})).toBeVisible();
  const other = await context.newPage();
  await other.goto("/");
  await expect(other.getByRole("button", {name: "English", exact: true})).toHaveAttribute("aria-pressed", "true");
  await other.getByRole("button", {name: "中文", exact: true}).click();
  await other.getByLabel("外观", {exact: true}).selectOption("light");
  await expect(page.locator("html")).toHaveAttribute("lang", "zh-CN");
  await expect(page.locator("html")).not.toHaveClass(/dark/);
  await expect(page.getByLabel("密码", {exact: true})).toBeVisible();
  expect(errors).toEqual([]);
});

test("system theme follows device changes, explicit selection takes priority", async ({page}) => {
  await page.emulateMedia({colorScheme: "dark"});
  await page.goto("/");
  await expect(page.getByLabel("Giao diện", {exact: true})).toHaveValue("system");
  await expect(page.locator("html")).toHaveClass(/dark/);
  await page.emulateMedia({colorScheme: "light"});
  await expect(page.locator("html")).not.toHaveClass(/dark/);
  await page.getByLabel("Giao diện", {exact: true}).selectOption("dark");
  await page.emulateMedia({colorScheme: "dark"});
  await page.emulateMedia({colorScheme: "light"});
  await expect(page.locator("html")).toHaveClass(/dark/);
});

test("translated screens, nested invoice form and guide retain draft data", async ({page}) => {
  await demo(page);
  await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByLabel("Appearance", {exact: true}).selectOption("dark");
  const routes = [
    ["/account", "Tài khoản của bạn"], ["/assistant", "Tài liệu bảo hiểm"],
    ["/invoices", "Hóa đơn của bạn"], ["/finance", "Ngân sách du học"],
    ["/rates", "Tỷ giá & ngân sách"], ["/copilot", "Trợ lý du học"],
    ["/history", "Lịch sử giao dịch"], ["/test-lab", "Thử trọn luồng A → Z"],
  ];
  for (const [route] of routes) {
    await page.goto(route);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("lang", "en");
    await expect(page.locator("main h1")).not.toContainText(/[àáảãạăâđêôơư]/i);
    await expect(page.locator(".breadcrumb")).not.toContainText("nav_");
  }
  await page.goto("/invoices/new");
  await page.getByLabel(translated("Mã hóa đơn", "en"), {exact: true}).fill("TEST-原始-hóa đơn");
  await page.getByRole("button", {name: "中文", exact: true}).click();
  await expect(page.getByLabel(translated("Mã hóa đơn", "zh"), {exact: true})).toHaveValue("TEST-原始-hóa đơn");
  await expect(page.locator("main h1")).toContainText(/[\u4e00-\u9fff]/);
  await page.screenshot({path: path.join(evidence, "invoice-zh-dark.png"), fullPage: true});
  await page.getByRole("button", {name: "Tiếng Việt", exact: true}).click();
  await expect(page.getByLabel("Mã hóa đơn", {exact: true})).toHaveValue("TEST-原始-hóa đơn");
  await page.getByRole("button", {name: "Mở hướng dẫn sử dụng", exact: true}).click();
  await page.getByRole("dialog").getByRole("button", {name: "Ngân sách", exact: true}).click();
  await expect(page.getByRole("dialog")).toContainText("Lập kế hoạch tiền");
});

test("mobile dark mode has readable surfaces and no horizontal overflow", async ({page}) => {
  await page.setViewportSize({width: 320, height: 740});
  await demo(page);
  await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByLabel("Appearance", {exact: true}).selectOption("dark");
  for (const route of ["/", "/finance", "/invoices/new", "/rates", "/copilot", "/test-lab"]) {
    await page.goto(route);
    await expect(page.locator("main h1")).toBeVisible();
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    for (const selector of [".card", "input:not([type=checkbox])", "textarea", "select"]) {
      const element = page.locator(selector).first();
      if (await element.isVisible()) {
        const color = await element.evaluate(el => getComputedStyle(el).backgroundColor);
        expect(color, `${route}: ${selector}`).not.toBe("rgb(255, 255, 255)");
      }
    }
  }
  await page.screenshot({path: path.join(evidence, "mobile-en-dark.png"), fullPage: true});
});

test("preferences tolerate unavailable local storage", async ({page}) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  await page.addInitScript(() => {
    Storage.prototype.getItem = () => {throw new Error("Storage unavailable");};
    Storage.prototype.setItem = () => {throw new Error("Storage unavailable");};
  });
  await page.goto("/");
  await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByLabel("Appearance", {exact: true}).selectOption("dark");
  await expect(page.getByLabel("Password", {exact: true})).toBeVisible();
  await expect(page.locator("html")).toHaveClass(/dark/);
  expect(errors).toEqual([]);
});

test("invalid saved preferences fall back to Vietnamese and device theme", async ({page}) => {
  await page.addInitScript(() => {localStorage.setItem("baoan.lang", "invalid"); localStorage.setItem("baoan.theme", "invalid");});
  await page.emulateMedia({colorScheme: "dark"});
  await page.goto("/");
  await expect(page.getByRole("button", {name: "Tiếng Việt", exact: true})).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Giao diện", {exact: true})).toHaveValue("system");
  await expect(page.locator("html")).toHaveClass(/dark/);
});

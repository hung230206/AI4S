import {expect, Page} from "@playwright/test";

// Legacy flow tests opt out after checking the first introduction, so they can
// concentrate on their own features. Dedicated task-UX tests retain default-on help.
export async function dismissWelcome(page: Page) {
  const intro = page.locator("dialog.page-intro-dialog");
  await expect(intro).toBeVisible();
  await intro.getByRole("button", {name: "Đã hiểu", exact: true}).click();
  const response = await page.request.get("/api/v1/auth/session");
  const uid = response.ok() ? (await response.json()).user.id : "22222222-2222-4222-8222-222222222222";
  await page.evaluate(userId => {localStorage.setItem(`demo.page-intro.v1.${userId}`, "off"); window.dispatchEvent(new Event("demo:preferences"));}, uid);
  await expect(intro).not.toBeVisible();
}

export async function openAssistant(page: Page) {
  await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Đồng ý sử dụng trợ lý?", exact: true});
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.getByLabel("Câu hỏi cho trợ lý", {exact: true})).toBeVisible();
}

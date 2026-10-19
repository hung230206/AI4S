import {expect, Page} from "@playwright/test";

export async function dismissWelcome(page: Page) {
  const guide = page.getByRole("dialog", {name: "Bắt đầu cùng Demo"});
  await expect(guide).toBeVisible();
  await guide.getByRole("button", {name: "Để sau", exact: true}).click();
  await expect(guide).not.toBeVisible();
}

export async function openAssistant(page: Page) {
  await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Đồng ý sử dụng trợ lý?", exact: true});
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(page.getByLabel("Câu hỏi cho trợ lý", {exact: true})).toBeVisible();
}

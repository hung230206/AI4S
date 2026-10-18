import {expect, Page} from "@playwright/test";

export async function dismissWelcome(page: Page) {
  const guide = page.getByRole("dialog", {name: "Bắt đầu cùng Demo"});
  await expect(guide).toBeVisible();
  await guide.getByRole("button", {name: "Để sau", exact: true}).click();
  await expect(guide).not.toBeVisible();
}

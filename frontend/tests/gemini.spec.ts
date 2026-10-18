import {test, expect, Page} from "@playwright/test";
import {dismissWelcome} from "./guide-helper";

async function openChat(page: Page, configured = true) {
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.route("**/api/v1/finance/assistant/status", route => route.fulfill({json: {gemini_configured: configured, model: configured ? "gemini-test" : null, read_only: true, history_stored: false}}));
  await page.goto("/copilot");
  await dismissWelcome(page);
  await expect(page.getByRole("button", {name: "Tra cứu trực tiếp", exact: true})).toBeEnabled();
}

test("Gemini chat sends bounded conversation context, displays sources and clears locally", async ({page}) => {
  const bodies: {message: string; use_gemini: boolean; language: string; history: {role: string; content: string}[]}[] = [];
  await page.route("**/api/v1/finance/assistant", async route => {
    bodies.push(route.request().postDataJSON());
    await route.fulfill({json: {provider: "GEMINI", model: "gemini-test", method: "GEMINI_GROUNDED", intent: "BUDGET_NEXT_STEP", answer: "Test reply from owned budget data.", executed_actions: [], actions: [{title: "Check budget", href: "/finance"}], citations: [{source_id: "B1", title: "Test budget source", href: "/finance"}, {source_id: "D1", title: "Self-authored test policy", document_kind: "TEST_FIXTURE", page: 1, excerpt: "Self-authored test excerpt."}], notice: "Test response"}});
  });
  await openChat(page);
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".copilot-privacy")).toContainText("Google Gemini");
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Giải thích ngân sách của tôi");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".copilot-answer")).toContainText("Test reply");
  await expect(page.getByRole("link", {name: "Test budget source ↗"})).toHaveAttribute("href", "/finance");
  await expect(page.locator(".copilot-source .badge.demo")).toHaveText("Dữ liệu mẫu tự soạn");
  expect(bodies[0].use_gemini).toBe(true); expect(bodies[0].history).toEqual([]);
  await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByLabel("Question for the assistant", {exact: true}).fill("Explain that again");
  await page.getByRole("button", {name: "Send question", exact: true}).click();
  await expect(page.locator(".copilot-turn")).toHaveCount(2);
  expect(bodies[1].language).toBe("en"); expect(bodies[1].history.map(turn => turn.role)).toEqual(["user", "assistant"]);
  await page.getByRole("button", {name: "Clear conversation", exact: true}).click();
  await expect(page.locator(".copilot-turn")).toHaveCount(0);
});

test("provider quota fallback is explicit and direct lookup sends no chat history", async ({page}) => {
  let mode = true;
  await page.route("**/api/v1/finance/assistant", async route => {
    const body = route.request().postDataJSON(); mode = body.use_gemini;
    if (!mode) expect(body.history).toEqual([]);
    await route.fulfill({json: {provider: "RULES", method: "GROUNDED_WORKFLOW", answer: "Local account data", fallback_reason: mode ? "PROVIDER_RATE_LIMIT" : undefined, actions: [], citations: [], executed_actions: [], notice: "Local"}});
  });
  await openChat(page);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Hỏi về ngân sách");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".copilot-fallback")).toContainText("giới hạn lượt gọi");
  await page.getByRole("button", {name: "Tra cứu trực tiếp", exact: true}).click();
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Kiểm tra tiếp ngân sách");
  await page.getByRole("button", {name: "Gửi câu hỏi", exact: true}).click();
  await expect(page.locator(".copilot-turn")).toHaveCount(2);
  expect(mode).toBe(false);
});

test("no key keeps direct lookup available without offering an active Gemini mode", async ({page}) => {
  await openChat(page, false);
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toBeDisabled();
  await expect(page.getByRole("button", {name: "Tra cứu trực tiếp", exact: true})).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".copilot-privacy")).toContainText("chưa được cấu hình");
});

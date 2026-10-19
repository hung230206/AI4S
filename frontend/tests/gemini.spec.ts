import {test, expect, type Page} from "@playwright/test";
import {dismissWelcome} from "./guide-helper";
import {AI_PRIVACY_NOTICE_VERSION, type AiPermission} from "../src/lib/privacy";

async function setup(page: Page, configured = true, notice = AI_PRIVACY_NOTICE_VERSION) {
  let permission: AiPermission = {enabled: false, revision: 0, notice_version: notice, scopes: [], data_mode: "DEMO_ONLY", granted_at: null, expires_at: null, allowed_scopes: ["history", "documents"]};
  const writes: {enabled: boolean; preset?: string}[] = [];
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.route("**/api/v1/privacy/ai-permission", async route => {
    if (route.request().method() === "POST") {
      const body = route.request().postDataJSON(); writes.push(body);
      permission = {...permission, enabled: body.enabled, revision: permission.revision + 1, scopes: body.enabled ? ["history", "documents"] : [], expires_at: body.enabled ? new Date(Date.now() + 3600000).toISOString() : null};
    }
    await route.fulfill({json: permission});
  });
  await page.route("**/api/v1/finance/assistant/status", route => route.fulfill({json: {gemini_configured: configured}}));
  await page.goto("/"); await dismissWelcome(page);
  return {writes, expire: () => {permission = {...permission, enabled: false, scopes: [], revision: permission.revision + 1};}};
}
async function allow(page: Page) {
  await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Đồng ý sử dụng trợ lý?", exact: true});
  await expect(dialog).toBeVisible(); await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click();
  await expect(dialog).not.toBeVisible(); await expect(page.getByLabel("Câu hỏi cho trợ lý", {exact: true})).toBeFocused();
}
const reply = (answer = "Test answer") => ({provider: "GEMINI", answer, actions: [], citations: []});

test("bottom-centered launcher asks fixed consent on click, decline sends nothing and permission controls stay in account", async ({page}) => {
  let sends = 0;
  await page.route("**/api/v1/study-assistant/chat", route => {sends++; return route.fulfill({json: reply()});});
  const state = await setup(page);
  const bar = page.getByRole("button", {name: "Mở trợ lý du học", exact: true});
  const bounds = (await bar.boundingBox())!; const viewport = page.viewportSize()!;
  expect(Math.abs(bounds.x + bounds.width / 2 - viewport.width / 2)).toBeLessThan(2);
  expect(viewport.height - bounds.y - bounds.height).toBeLessThan(35);
  expect(await page.locator(".floating-assistant").evaluate(el => getComputedStyle(el).position)).toBe("fixed");
  await expect(page.locator('nav a[href="/copilot"]')).toHaveCount(0);
  await bar.click();
  const dialog = page.getByRole("dialog", {name: "Đồng ý sử dụng trợ lý?"});
  await expect(dialog.getByRole("checkbox")).toHaveCount(0); await expect(dialog.getByRole("button")).toHaveCount(2);
  await expect(dialog.getByRole("link")).toHaveAttribute("href", "/privacy#assistant");
  await dialog.getByRole("button", {name: "Không đồng ý", exact: true}).click();
  await expect(dialog).not.toBeVisible(); await expect(page.locator(".floating-chat")).toHaveCount(0);
  expect(state.writes).toHaveLength(0); expect(sends).toBe(0);
  await bar.click(); await expect(dialog).toBeVisible(); await page.keyboard.press("Escape"); await expect(dialog).not.toBeVisible(); expect(state.writes).toHaveLength(0);
  await allow(page); expect(state.writes).toEqual([expect.objectContaining({enabled: true, preset: "SAMPLE_ASSISTANT"})]);
  await expect(page.getByRole("button", {name: "Thu hồi sự đồng ý", exact: true})).toHaveCount(0);
  await expect(page.getByRole("button", {name: "Xem điều khoản", exact: true})).toHaveCount(0);
  await expect(page.locator(".rag-library, .privacy-preview")).toHaveCount(0);
});

test("consent uses concise product language and links to complete public processing terms", async ({page, context}) => {
  const state = await setup(page);
  await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Đồng ý sử dụng trợ lý?", exact: true});
  await expect(dialog).toContainText("Demo xử lý nội dung bạn cung cấp");
  await expect(dialog).toContainText("dịch vụ AI bên ngoài");
  await expect(dialog).not.toContainText(/Gemini|Copilot|3 lượt|3 turns|3轮|tối đa 3|1 giờ/i);
  await expect(dialog.getByRole("button")).toHaveCount(2);
  const popupPromise = context.waitForEvent("page");
  await dialog.getByRole("link", {name: "Điều khoản và quyền riêng tư ↗", exact: true}).click();
  const terms = await popupPromise;
  await expect(terms).toHaveURL(/\/privacy#assistant$/);
  await expect(terms.locator("body")).toContainText("Google");
  await expect(terms.locator("body")).toContainText("có người đánh giá");
  await expect(terms.locator("body")).not.toContainText(/Gemini|Copilot/i);
  await terms.close(); expect(state.writes).toHaveLength(0);
  await dialog.getByRole("button", {name: "Không đồng ý", exact: true}).click();
  await expect(page.locator(".floating-chat")).toHaveCount(0); expect(state.writes).toHaveLength(0);
});

test("one floating chat uses RAG then general Gemini, folds sources and bounds conversation history", async ({page}) => {
  const bodies: {message: string; use_gemini: boolean; language: string; history: {role: string; content: string}[]}[] = [];
  await page.route("**/api/v1/study-assistant/chat", async route => {
    bodies.push(route.request().postDataJSON());
    await route.fulfill({json: {...reply(`Answer ${bodies.length}`), route: bodies.length === 1 ? "RAG" : "GEMINI", citations: bodies.length === 1 ? [{source_id: "R1", title: "Self-authored test source", href: "/knowledge/test?revision=1#page-1", page: 1, excerpt: "Fictional terms."}] : []}});
  });
  await setup(page); await allow(page);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Giải thích bảo hiểm"); await page.keyboard.press("Enter");
  await expect(page.locator(".assistant-answer")).toContainText("Answer 1");
  const source = page.getByRole("link", {name: "[R1] Self-authored test source ↗", exact: true}); await expect(source).not.toBeVisible();
  await page.getByText("Nguồn tham khảo (1)", {exact: true}).click();
  await expect(source).toHaveAttribute("href", "/knowledge/test?revision=1#page-1"); await expect(page.locator(".assistant-sources")).toContainText("Trang 1");
  await page.getByRole("button", {name: "English", exact: true}).click();
  for (let index = 2; index <= 5; index++) {
    await page.getByLabel("Question for the assistant", {exact: true}).fill(`General question ${index}`);
    await page.getByRole("button", {name: "Send question", exact: true}).click();
    await expect(page.locator(".assistant-answer").last()).toContainText(`Answer ${index}`);
  }
  expect(bodies[0].use_gemini).toBe(true); expect(bodies[0].history).toEqual([]);
  expect(bodies[1].language).toBe("en"); expect(bodies[1].history.map(turn => turn.role)).toEqual(["user", "assistant"]);
  expect(bodies[4].history).toHaveLength(6); expect(bodies[4].history[0].content).toBe("General question 2");
  await expect(page.getByRole("button", {name: "Gemini AI", exact: true})).toHaveCount(0);
});

test("Enter sends once, Shift Enter adds a newline and IME Enter never submits", async ({page}) => {
  const sent: {message: string; history: unknown[]}[] = [];
  await page.route("**/api/v1/study-assistant/chat", async route => {sent.push(route.request().postDataJSON()); await route.fulfill({json: reply("Keyboard accepted")});});
  await setup(page); await allow(page);
  const box = page.getByLabel("Câu hỏi cho trợ lý", {exact: true});
  await box.fill("Dòng đầu"); await box.press("Shift+Enter"); await box.pressSequentially("Dòng sau");
  await expect(box).toHaveValue("Dòng đầu\nDòng sau"); expect(sent).toHaveLength(0);
  await box.dispatchEvent("keydown", {key: "Enter", code: "Enter", keyCode: 229, isComposing: true, bubbles: true}); expect(sent).toHaveLength(0);
  await box.press("Enter"); await expect(page.locator(".assistant-answer")).toContainText("Keyboard accepted");
  expect(sent).toHaveLength(1); expect(sent[0].message).toBe("Dòng đầu\nDòng sau");
  await box.fill(" "); await box.press("Enter"); expect(sent).toHaveLength(1);
});

test("scrolls chat to new answers without moving the page, even after reading older messages", async ({page}) => {
  let count = 0;
  await page.route("**/api/v1/study-assistant/chat", route => route.fulfill({json: reply(`Answer ${++count}\n` + "Detailed test guidance.\n".repeat(45))}));
  await setup(page); await page.evaluate(() => window.scrollTo(0, 140)); const initialY = await page.evaluate(() => window.scrollY);
  await allow(page);
  const scroll = page.locator(".floating-chat-scroll"); const box = page.getByLabel("Câu hỏi cho trợ lý", {exact: true});
  for (let index = 1; index <= 3; index++) {
    await box.fill(`Question ${index}`); await box.press("Enter"); await expect(page.locator(".assistant-answer").last()).toContainText(`Answer ${index}`);
    await expect.poll(() => scroll.evaluate(el => Math.abs(el.scrollHeight - el.clientHeight - el.scrollTop))).toBeLessThan(3);
    expect(await page.evaluate(() => window.scrollY)).toBe(initialY); if (index < 3) await scroll.evaluate(el => {el.scrollTop = 0;});
  }
  await expect(box).toBeInViewport(); await expect(page.getByRole("button", {name: "Gửi câu hỏi", exact: true})).toBeInViewport();
  await page.screenshot({path: "../submission/evidence/screenshots/floating-assistant/desktop.png"});
});

test("minimize, route navigation and reopening preserve conversation without repeated consent", async ({page}) => {
  await page.route("**/api/v1/study-assistant/chat", route => route.fulfill({json: reply("Conversation preserved")}));
  const state = await setup(page); await allow(page);
  await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("How to study abroad?"); await page.keyboard.press("Enter");
  await expect(page.locator(".assistant-answer")).toContainText("Conversation preserved");
  await page.locator('nav a[href="/finance"]').click(); await expect(page).toHaveURL(/\/finance$/);
  await expect(page.locator(".assistant-answer")).toContainText("Conversation preserved");
  await page.getByRole("button", {name: "Thu nhỏ trợ lý", exact: true}).click(); await expect(page.getByRole("button", {name: "Mở trợ lý du học", exact: true})).toBeFocused();
  await page.locator('nav a[href="/history"]').click(); await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
  await expect(page.locator(".assistant-answer")).toContainText("Conversation preserved"); expect(state.writes).toHaveLength(1);
});

test("account revocation closes chat, clears context and ignores an in-flight reply", async ({page}) => {
  let release!: () => void; let calls = 0; let answered = false;
  const gate = new Promise<void>(resolve => {release = resolve;});
  await page.route("**/api/v1/study-assistant/chat", async route => {
    calls++; const body = route.request().postDataJSON(); if (calls === 1) await gate; else expect(body.history).toEqual([]);
    await route.fulfill({json: reply(calls === 1 ? "Reply after revoke" : "New consent answer")}); answered = true;
  });
  const state = await setup(page); await allow(page);
  const box = page.getByLabel("Câu hỏi cho trợ lý", {exact: true});
  await box.fill("First request"); await box.press("Enter"); await expect(box).toBeDisabled(); await page.keyboard.press("Enter"); expect(calls).toBe(1);
  await page.locator('nav a[href="/account"]').click(); await page.getByRole("button", {name: "Thu nhỏ trợ lý", exact: true}).click();
  await page.getByRole("button", {name: "Thu hồi sự đồng ý", exact: true}).click();
  await expect(page.locator(".floating-chat")).toHaveCount(0); expect(state.writes.at(-1)?.enabled).toBe(false);
  release(); await expect.poll(() => answered).toBe(true); await allow(page); await expect(page.locator(".assistant-turn")).toHaveCount(0);
  await box.fill("Second request"); await box.press("Enter"); await expect(page.locator(".assistant-answer")).toContainText("New consent answer");
  await expect(page.locator(".floating-chat")).not.toContainText("Reply after revoke");
});

test("provider fallback is explicit and a missing key still permits local answers", async ({page}) => {
  let cloud = true;
  await page.route("**/api/v1/study-assistant/chat", async route => {
    cloud = route.request().postDataJSON().use_gemini; await route.fulfill({json: {...reply("Local excerpt"), provider: "EXTRACTIVE", fallback_reason: "PROVIDER_RATE_LIMIT"}});
  });
  await setup(page, false); await allow(page); await page.getByLabel("Câu hỏi cho trợ lý", {exact: true}).fill("Hỏi về bảo hiểm"); await page.keyboard.press("Enter");
  await expect(page.locator(".assistant-answer")).toContainText("Local excerpt"); await expect(page.locator(".assistant-note")).toContainText("kết quả tra cứu tại máy chủ"); expect(cloud).toBe(false);
});

test("permission expiry requires renewed consent before reopening", async ({page}) => {
  const state = await setup(page); await allow(page); await page.getByRole("button", {name: "Thu nhỏ trợ lý", exact: true}).click();
  state.expire(); await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
  await expect(page.getByRole("dialog", {name: "Đồng ý sử dụng trợ lý?"})).toBeVisible(); await expect(page.locator(".floating-chat")).toHaveCount(0);
});

test("account settings immediately reflect consent granted from the floating bar", async ({page}) => {
  const state = await setup(page); await page.locator('nav a[href="/account"]').click();
  await expect(page.getByRole("button", {name: "Thu hồi sự đồng ý", exact: true})).toHaveCount(0);
  await allow(page); await page.getByRole("button", {name: "Thu nhỏ trợ lý", exact: true}).click();
  await expect(page.getByRole("button", {name: "Thu hồi sự đồng ý", exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Thu hồi sự đồng ý", exact: true}).click();
  await expect(page.getByRole("button", {name: "Thu hồi sự đồng ý", exact: true})).toHaveCount(0);
  await page.getByRole("button", {name: "Mở trợ lý du học", exact: true}).click();
  await expect(page.getByRole("dialog", {name: "Đồng ý sử dụng trợ lý?"})).toBeVisible();
  expect(state.writes.map(body => body.enabled)).toEqual([true, false]);
});

test("mobile light and dark chat, localized consent and short landscape fit the viewport", async ({page}) => {
  await page.setViewportSize({width: 390, height: 844});
  await page.route("**/api/v1/study-assistant/chat", route => route.fulfill({json: reply("Mobile answer\n" + "More guidance.\n".repeat(30))}));
  await setup(page); await page.getByRole("button", {name: "English", exact: true}).click();
  await page.getByRole("button", {name: "Open study-abroad assistant", exact: true}).click();
  const dialog = page.getByRole("dialog", {name: "Agree to use the assistant?", exact: true});
  await expect(dialog.getByRole("heading", {name: "Agree to use the assistant?", exact: true})).toBeInViewport();
  await expect(dialog.getByRole("button", {name: "Agree", exact: true})).toBeInViewport();
  await page.screenshot({path: "../submission/evidence/screenshots/floating-assistant/consent-mobile.png"});
  await dialog.getByRole("button", {name: "Disagree", exact: true}).click(); await page.getByRole("button", {name: "中文", exact: true}).click();
  await page.getByRole("button", {name: "打开留学助手", exact: true}).click();
  await page.getByRole("dialog", {name: "同意使用助手？", exact: true}).getByRole("button", {name: "同意", exact: true}).click();
  await page.getByLabel("向助手提问", {exact: true}).fill("公开资料测试"); await page.keyboard.press("Enter");
  await expect(page.locator(".assistant-answer")).toContainText("Mobile answer");
  await page.screenshot({path: "../submission/evidence/screenshots/floating-assistant/mobile-light.png"});
  await page.getByRole("button", {name: "外观", exact: true}).click(); await expect(page.locator("html")).toHaveClass(/dark/);
  await page.screenshot({path: "../submission/evidence/screenshots/floating-assistant/mobile-dark.png"});
  for (const size of [{width: 320, height: 740}, {width: 844, height: 390}]) {
    await page.setViewportSize(size); await expect(page.getByLabel("向助手提问", {exact: true})).toBeInViewport();
    await expect(page.getByRole("button", {name: "收起助手", exact: true})).toBeInViewport();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    const bounds = (await page.locator(".floating-chat").boundingBox())!; expect(bounds.y).toBeGreaterThanOrEqual(0); expect(bounds.y + bounds.height).toBeLessThanOrEqual(size.height);
  }
});

test("legacy copilot URL opens global assistant and newer unseen notices cannot be accepted", async ({page}) => {
  await setup(page, true, "future-unseen-notice"); await page.goto("/copilot"); await expect(page).toHaveURL(/\/(\?assistant=open)?$/);
  const dialog = page.getByRole("dialog", {name: "Đồng ý sử dụng trợ lý?"});
  await expect(dialog.getByRole("alert")).toContainText("Điều khoản đã được cập nhật"); await expect(dialog.getByRole("button", {name: "Đồng ý", exact: true})).toBeDisabled();
});

test("OCR asks per file, declining sends no bytes and agreeing continues original operation", async ({page}) => {
  let uploads = 0;
  await page.route("**/api/v1/invoice-imports", async route => {
    uploads++; expect(route.request().headers()["x-processing-consent"]).toBe("invoice-ocr:files-2026-10-19-v1");
    await route.fulfill({json: {id: "qa-import", filename: "fictional.txt", method: "TEXT", invoice_id: null, pages: [{page: 1, text: "Fictional invoice"}], suggestions: {fields: {}, currency: "CNY", warnings: []}}});
  });
  await setup(page); await page.goto("/invoices/new");
  await page.getByLabel("Tệp hóa đơn", {exact: true}).setInputFiles({name: "fictional.txt", mimeType: "text/plain", buffer: Buffer.from("Fictional invoice CNY 800")});
  const read = page.getByRole("button", {name: "Đọc và điền thông tin", exact: true}); await read.click();
  const dialog = page.getByRole("dialog", {name: "Cho phép đọc hóa đơn?"}); await expect(dialog).toBeVisible(); expect(uploads).toBe(0);
  await dialog.getByRole("button", {name: "Không đồng ý", exact: true}).click(); await expect(read).toBeEnabled(); expect(uploads).toBe(0);
  await read.click(); await dialog.getByRole("button", {name: "Đồng ý", exact: true}).click(); await page.getByText("Xem toàn văn đã đọc", {exact: true}).click();
  await expect(page.getByText("Fictional invoice", {exact: true})).toBeVisible(); expect(uploads).toBe(1);
});

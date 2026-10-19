// Explicit local acceptance with one real Google request, fictional sources only.
// Run after the mock browser suite with the QA API's GEMINI_ENABLED=true.
import {chromium} from "../frontend/node_modules/playwright-core/index.mjs";
import fs from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
import assert from "node:assert/strict";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const origin = process.argv[2] || "http://localhost:3104";
const china = process.argv[3] === "china";
assert(["localhost", "127.0.0.1"].includes(new URL(origin).hostname), "This acceptance script is for the local QA app only.");
const evidence = {at: new Date().toISOString(), origin, fictional_content_only: !china, public_official_content_only: china, actual_generation_requests: 0};
const browser = await chromium.launch({channel: "chrome", headless: true});
try {
  const page = await browser.newPage({viewport: {width: 1280, height: 900}});
  await page.addInitScript(() => localStorage.setItem("baoan.mode", "demo"));
  await page.goto(origin + "/knowledge");
  await page.getByRole("dialog", {name: "Bắt đầu cùng Demo"}).getByRole("button", {name: "Để sau", exact: true}).click();
  await page.getByLabel("Nguồn để tra cứu", {exact: true}).selectOption({label: china ? "[NFRA · 2021] Bảo hiểm ngắn hạn và không bảo đảm tái tục" : "Demo student health policy — fictional terms"});
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).fill(china ? "Bảo hiểm sức khỏe ngắn hạn có bảo đảm tái tục không?" : "Quyền lợi ngoại trú có hạn mức bao nhiêu?");
  await page.getByLabel("Câu hỏi bảo hiểm", {exact: true}).press("Enter");
  const consent = page.getByRole("dialog", {name: "Cho phép dùng Gemini?"});
  await consent.waitFor({state: "visible"});
  const response = page.waitForResponse(r => r.url().endsWith("/api/v1/rag/ask") && r.request().method() === "POST", {timeout: 35000});
  const started = performance.now();
  evidence.actual_generation_requests = 1;
  await consent.getByRole("button", {name: "Đồng ý", exact: true}).click();
  const answerResponse = await response;
  assert.equal(answerResponse.status(), 200);
  const answer = await answerResponse.json();
  evidence.generation_elapsed_seconds = Math.round(performance.now() - started) / 1000;
  assert.equal(answer.provider, "GEMINI"); assert.equal(answer.method, "BM25_RAG_GEMINI");
  assert(answer.citations.length > 0 && answer.executed_actions.length === 0);
  if (china) assert(/không|chưa/i.test(answer.answer) && /tái tục|gia hạn/i.test(answer.answer));
  else assert(answer.answer.replace(/\D/g, "").includes("2000"));
  await page.locator(".rag-answer").getByText(answer.model, {exact: true}).waitFor({state: "visible"});
  await page.getByRole("link", {name: "Đọc trang nguồn ↗", exact: true}).first().waitFor({state: "visible"});
  await page.locator(".rag-answer").scrollIntoViewIfNeeded();
  await page.screenshot({path: path.join(root, "submission/evidence/screenshots/rag/" + (china ? "china-rag-real.png" : "rag-llm-real.png"))});
  Object.assign(evidence, {status: "PASS", provider: answer.provider, model: answer.model, model_fallback_from: answer.model_fallback_from, answer: answer.answer, citations: answer.citations.map(c => ({id: c.source_id, page: c.page, revision: c.revision, href: c.href}))});
  await page.getByRole("button", {name: "Thu hồi quyền Gemini", exact: true}).click();
  await page.getByRole("button", {name: "Thu hồi quyền Gemini", exact: true}).waitFor({state: "hidden"});
  evidence.consent_withdrawn_after_test = true;
} catch (error) {
  Object.assign(evidence, {status: "FAIL", error: error.name});
  process.exitCode = 1;
} finally {
  await browser.close();
  await fs.writeFile(path.join(root, "submission/evidence/" + (china ? "china-rag-real-browser.json" : "rag-llm-real-browser.json")), JSON.stringify(evidence, null, 2) + "\n");
}
console.log(`${evidence.status}: local real-provider RAG browser acceptance`);

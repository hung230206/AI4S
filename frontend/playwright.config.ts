import {defineConfig} from "@playwright/test";
export default defineConfig({
  testDir: "./tests", timeout: 60000, workers: 1, fullyParallel: false,
  reporter: [["list"], ["json", {outputFile: "../submission/evidence/browser-results.json"}]],
  use: {baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000", channel: process.env.PLAYWRIGHT_CHANNEL || "chrome", headless: true, trace: "retain-on-failure", screenshot: "only-on-failure"},
});

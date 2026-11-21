import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  workers: 1,
  retries: 0,
  forbidOnly: true,
  timeout: 30000,
  outputDir: "../.local/browser-test-results",
  reporter: [
    ["list"],
    ["json", { outputFile: "../.local/browser-test-report.json" }],
  ],
  use: {
    baseURL: process.env.FIXIT_E2E_URL || "http://127.0.0.1:5173",
    channel: "chrome",
    viewport: { width: 1280, height: 1100 },
    trace: "off",
    screenshot: "only-on-failure",
  },
});

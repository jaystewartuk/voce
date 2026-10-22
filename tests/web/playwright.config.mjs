import { defineConfig, devices } from "@playwright/test";

const python = process.env.VOCE_PYTHON || "python3";

export default defineConfig({
  testDir: ".",
  testMatch: "*.spec.mjs",
  timeout: 30e3,
  retries: 0,
  reporter: process.env.CI ? [["list"], ["github"]] : "list",
  use: { ...devices["Desktop Chrome"], baseURL: "http://localhost:8787/app/" },
  webServer: {
    command: `${python} -m http.server 8787 --bind 127.0.0.1 --directory ../../site`,
    url: "http://localhost:8787/app/",
    reuseExistingServer: !process.env.CI,
    stdout: "ignore",
    stderr: "ignore",
  },
});

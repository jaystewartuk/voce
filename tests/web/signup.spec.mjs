/* Starting a library from the web app, and what it keeps there: the page as a person uses it, against a fake
   GitHub. GitHub's own screens (creating the repository, installing the app) are skipped as if pressed. */

import { expect, test } from "@playwright/test";
import { FakeGitHub, templateFiles } from "./fake.mjs";

const LIBRARY = "someone/voce-library";
let github;

test.beforeEach(async ({ context }) => {
  github = new FakeGitHub();
  await github.attach(context);
});

test.afterEach(() => {
  expect(github.offline, "requests to the real network").toEqual([]);
});

const titles = (page) => page.locator("#library .doc .name").allInnerTexts();

test("a new person makes a library from the template and hears its playlist", async ({ page }) => {
  await page.goto("./");
  await expect(page.locator("#library h1.page")).toHaveText("Read something");
  await page.locator("#signin-link").click();
  await page.locator("#signin-go").click();

  // Signed in, with nothing voce can reach yet: the two steps.
  await expect(page.locator("#choose-title")).toHaveText("Make your library");
  await expect(page.locator("#make")).toBeVisible();
  const make = new URL(await page.locator("#make-go").getAttribute("href"));
  expect(make.origin + make.pathname).toBe("https://github.com/new");
  expect(Object.fromEntries(make.searchParams)).toMatchObject({
    template_owner: "jaystewartuk", template_name: "voce-library-template", owner: "@me", name: "voce-library", visibility: "private",
  });

  // On GitHub: "Create repository", then the app installed on it.
  github.repo(LIBRARY, templateFiles());
  await page.locator("#make-install").click();

  await expect(page.locator("#library .part").first()).toHaveText("Start here");
  expect(await titles(page)).toEqual([
    expect.stringContaining("Welcome to voce"), expect.stringContaining("Code, read aloud"), expect.stringContaining("Filling your library"),
  ]);
  await page.locator("#library .doc").nth(1).click();
  await expect(page.locator("#article")).toContainText("optional chaining");
});

test("a web page opened while signed in is kept in the library for every device", async ({ page }) => {
  github.repo(LIBRARY, templateFiles());
  await page.goto("./");
  await page.locator("#signin-link").click();
  await page.locator("#signin-go").click();
  await expect(page.locator("#library .part").first()).toHaveText("Start here");

  await page.locator("#url").fill("https://example.test/post");
  await page.locator("#open-url button").click();
  await expect(page.locator("#article")).toContainText("The cache key ignores the query string.");

  const files = github.repos[LIBRARY];
  const text = Object.keys(files).find((f) => f.startsWith("texts/"));
  expect(text).toMatch(/^texts\/[0-9a-f]{64}\.md$/);
  expect(files[text]).toContain("# A post worth hearing");
  const item = JSON.parse(files[text.replace(/^texts\/(.*)\.md$/, "items/$1.json")]);
  expect(item).toMatchObject({ kind: "page", url: "https://example.test/post", title: "A post worth hearing" });

  // Another device, signed in to the same library, lists it.
  const other = await page.context().browser().newContext();
  await github.attach(other);
  const phone = await other.newPage();
  await phone.goto("./");
  await phone.locator("#signin-link").click();
  await phone.locator("#signin-go").click();
  await expect(phone.locator("#library")).toContainText("A post worth hearing");
  await other.close();
});

test("what was read before signing in, and playlists kept on the device, move into the library", async ({ page }) => {
  github.repo(LIBRARY, templateFiles());
  github.repo("someone/notes", { "README.md": "# Notes\n\n## Listen in this order\n\n1. [First](first.md)\n", "first.md": "# First\n\nHello.\n" });
  await page.goto("./");
  await page.evaluate(() => localStorage.setItem("voce.sources", JSON.stringify([{ repo: "someone/notes", path: "README.md" }])));
  await page.locator("#url").fill("https://example.test/post");
  await page.locator("#open-url button").click();
  await expect(page.locator("#article")).toContainText("The cache key ignores the query string.");
  await page.goto("./#/");

  await page.locator("#signin-link").click();
  await page.locator("#signin-go").click();
  await expect(page.locator("#choose-title")).toHaveText("Which repository?");
  await page.locator("#repos button", { hasText: LIBRARY }).click();

  await expect(page.locator("#library")).toContainText("A post worth hearing");
  await expect(page.locator("#library")).toContainText("First");
  const files = github.repos[LIBRARY];
  expect(Object.keys(files).filter((f) => /^(texts|items)\//.test(f))).toHaveLength(3); // the page's text and item, and the playlist
  expect(Object.values(files).some((t) => t.includes('"kind": "playlist"') && t.includes("someone/notes"))).toBe(true);
  expect(await page.evaluate(() => [localStorage.getItem("voce.local"), localStorage.getItem("voce.sources")])).toEqual(["[]", null]);
  await expect(page.locator("#library .part", { hasText: "On this device" })).toHaveCount(0);
});

test("an empty library opens without an error", async ({ page }) => {
  github.repo(LIBRARY, {});
  await page.goto("./");
  await page.locator("#signin-link").click();
  await page.locator("#signin-go").click();
  await expect(page.locator("#library h1.page")).toHaveText("Nothing here yet");
  await expect(page.locator("#library .error")).toHaveCount(0);
});

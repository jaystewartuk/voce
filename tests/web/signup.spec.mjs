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

  await expect(page.locator("#library .course")).toContainText("My voce library");
  await page.locator("#library .course").click();
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
  await expect(page.locator("#library .course")).toContainText("My voce library");

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

test("something read on this device can be removed from it", async ({ page }) => {
  await page.goto("./");
  await page.locator("#url").fill("https://example.test/post");
  await page.locator("#open-url button").click();
  await expect(page.locator("#article")).toContainText("The cache key ignores the query string.");
  await page.goto("./#/");

  await expect(page.locator("#library .part", { hasText: "On this device" })).toHaveCount(1);
  await page.getByRole("button", { name: "Remove A post worth hearing from this device" }).click();
  await expect(page.locator("#library .doc")).toHaveCount(0);
  await expect(page.locator("#library .part", { hasText: "On this device" })).toHaveCount(0);
  expect(await page.evaluate(() => localStorage.getItem("voce.local"))).toBe("[]");
  expect(await page.evaluate(async () => (await (await caches.open("voce-local")).keys()).length)).toBe(0);
  await page.reload();
  await expect(page.locator("#library h1.page")).toHaveText("Read something");
  await expect(page.locator("#library .doc")).toHaveCount(0);
});

test("an empty library opens without an error", async ({ page }) => {
  github.repo(LIBRARY, {});
  await page.goto("./");
  await page.locator("#signin-link").click();
  await page.locator("#signin-go").click();
  await expect(page.locator("#library h1.page")).toHaveText("Nothing here yet");
  await expect(page.locator("#library .error")).toHaveCount(0);
});

test("a playlist whose README moved into a folder is followed there, and one that's gone says what to do", async ({ page }) => {
  const playlist = (repo, path) => JSON.stringify({ kind: "playlist", repo, path, added: "2026-10-22T17:37:34Z" });
  github.repo(LIBRARY, { ...templateFiles(),
    "items/0000000000000001.json": playlist("someone/notes", "study/README.md"),
    "items/0000000000000002.json": playlist("someone/notes", "gone/README.md") });
  github.repo("someone/notes", {
    "projects/study/README.md": "# Study\n\n## Listen in this order\n\n1. [First](first.md)\n",
    "projects/study/first.md": "# First\n\nHello.\n" });
  await page.goto("./");
  await page.locator("#signin-link").click();
  await page.locator("#signin-go").click();
  await page.locator("#repos button", { hasText: LIBRARY }).click();

  await expect(page.locator("#library")).toContainText("First");
  expect(JSON.parse(github.repos[LIBRARY]["items/0000000000000001.json"]).path).toBe("projects/study/README.md");
  await expect(page.locator("#library .error")).toHaveText(
    "Couldn't read the playlist gone/README.md in someone/notes: it isn't there any more. "
    + "If it moved, remove it in Settings and add it from where it is now.");
});

test("a playlist in someone's public repository plays without voce being given access to it", async ({ page }) => {
  github.repo(LIBRARY, { ...templateFiles(),
    "items/0000000000000003.json": JSON.stringify({ kind: "playlist", repo: "someone/course", path: "README.md", added: "2026-10-26T17:00:00Z" }) });
  github.publicRepo("someone/course", {
    "README.md": "# Un curso\n\n## Listen in this order\n\n1. [La primera lección](lecciones/01.md)\n",
    "lecciones/01.md": "# La primera lección\n\nHola.\n" });
  await page.goto("./");
  await page.locator("#signin-link").click();
  await page.locator("#signin-go").click();

  await expect(page.locator("#library")).toContainText("La primera lección");
  await expect(page.locator("#library .error")).toHaveCount(0);
  await expect(page.locator("#library .course", { hasText: "Un curso" })).toContainText("Public");
  await page.locator("#library .course", { hasText: "Un curso" }).click();
  await page.locator("#library .doc", { hasText: "La primera lección" }).click();
  await expect(page.locator("#article")).toContainText("Hola.");
});

test("the home page shows each course, where it comes from and how far through, and a course page lists its parts", async ({ page }) => {
  const course = "someone/voce-course-appsec";
  github.repo(LIBRARY, { ...templateFiles(),
    "items/0000000000000004.json": JSON.stringify({ kind: "playlist", repo: course, path: "README.md", added: "2026-10-27T19:20:00Z" }) });
  github.repo(course, {
    "README.md": "# Application security\n\nA course from HTTP up to paid security work.\n\n## Listen in this order\n\n"
      + "### Part 0. Start here\n1. [The goal](00/01.md) · 7 min\n2. [How it works](00/02.md) · 7 min\n\n"
      + "### Part 1. The web\n3. [HTTP requests](01/02.md) · 12 min\n4. [Not written yet](01/03.md) · 10 min\n",
    "00/01.md": "# The goal\n\nGet paid for security work.\n",
    "00/02.md": "# How it works\n\nListen, then do.\n",
    "01/02.md": "# HTTP requests\n\nA request is a few lines of text.\n" });
  await page.goto("./");
  await page.locator("#signin-link").click();
  await page.locator("#signin-go").click();
  await page.locator("#repos button", { hasText: LIBRARY }).click();

  const card = page.locator("#library .course", { hasText: "Application security" });
  await expect(card).toContainText(course);
  await expect(card).toContainText("Private");
  await expect(card).toContainText("0 of 3 done");
  await expect(card).toContainText("Next: The goal");

  await card.click();
  await expect(page).toHaveURL(/#\/course\/0000000000000004$/);
  await expect(page.locator("#library h1.page")).toHaveText("Application security");
  await expect(page.locator("#library .lead")).toHaveText("A course from HTTP up to paid security work.");
  expect(await page.locator("#library .part").allTextContents()).toEqual(["Part 0. Start here", "Part 1. The web"]);
  await expect(page.locator("#library .coming")).toHaveText("1 more listed in the course, not written yet.");

  await page.locator("#library .doc", { hasText: "HTTP requests" }).click();
  await expect(page.locator("#article")).toContainText("A request is a few lines of text.");
  await expect(page.locator("#title a")).toHaveText("Application security");
  await page.locator("#title a").click();
  await expect(page.locator("#library h1.page")).toHaveText("Application security");
});

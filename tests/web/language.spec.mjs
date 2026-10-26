/* The device's voice reads a document in its own language: a Spanish page on a phone set to English in Mexico
   is read by a Mexican Spanish voice. */

import { expect, test } from "@playwright/test";
import { FakeGitHub } from "./fake.mjs";

let github;

test.use({ locale: "en-MX" });

test.beforeEach(async ({ context }) => {
  github = new FakeGitHub();
  await github.attach(context);
  await context.route("https://example.test/clase", (route) => route.fulfill({
    contentType: "text/markdown", headers: { "Access-Control-Allow-Origin": "*" },
    body: "# Qué es la danzaterapia\n\nEs el uso del movimiento para conocerte y para sanar. ¿Con quién se trabaja? "
      + "Con niñas y niños, con personas mayores y con quien nunca ha bailado en su vida.\n",
  }));
  await context.addInitScript(() => {
    // The device's voices, as iOS lists them, and each sentence said with the voice and language it was given.
    const voices = [
      { voiceURI: "samantha", name: "Samantha", lang: "en-US", default: true },
      { voiceURI: "monica", name: "Mónica", lang: "es-ES", default: false },
      { voiceURI: "paulina", name: "Paulina", lang: "es-MX", default: false },
    ];
    window.__spoken = [];
    window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      getVoices: () => voices,
      speak(u) { window.__spoken.push({ text: u.text, voice: u.voice && u.voice.voiceURI, lang: u.lang }); setTimeout(() => u.onend && u.onend(), 20); },
      cancel() {},
    } });
  });
});

test.afterEach(() => {
  expect(github.offline, "requests to the real network").toEqual([]);
});

async function listen(page, url, text, sentences) {
  await page.goto("./");
  await page.locator("#url").fill(url);
  await page.locator("#open-url button").click();
  await expect(page.locator("#article")).toContainText(text);
  await page.locator("#play").click();
  await expect.poll(() => page.evaluate(() => window.__spoken.length), { timeout: 10e3 }).toBe(sentences);
  return page.evaluate(() => window.__spoken);
}

test("a Spanish page is read by a voice from the device's country, a sentence at a time", async ({ page }) => {
  const spoken = await listen(page, "https://example.test/clase", "para conocerte", 4);
  expect(spoken.map((s) => s.voice)).toEqual(spoken.map(() => "paulina"));
  expect(spoken[0].lang).toBe("es-MX");
  expect(spoken.map((s) => s.text)).toContain("¿Con quién se trabaja?");
});

test("a page too short to tell its language is left to the device's default voice, as before", async ({ page }) => {
  const spoken = await listen(page, "https://example.test/post", "The cache key ignores the query string.", 3);
  expect(spoken.every((s) => !s.voice && !s.lang)).toBe(true);
});

test("with Kokoro chosen, which speaks only English here, a Spanish page is read by the device's voice", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("voce.engine", JSON.stringify("kokoro")));
  const spoken = await listen(page, "https://example.test/clase", "para conocerte", 4);
  expect(spoken.map((s) => s.voice)).toEqual(spoken.map(() => "paulina"));
});

/* The device's voice reads a document in its own language: a Spanish page on a phone set to English in Mexico
   is read by the best-sounding Mexican Spanish voice it has, never one of iOS's robotic novelty voices. */

import { expect, test } from "@playwright/test";
import { FakeGitHub } from "./fake.mjs";

let github;

// The voices as an iPhone lists them: Eloquence and novelty voices among the compact ones, before them in order.
const IPHONE = [
  { voiceURI: "com.apple.voice.compact.en-US.Samantha", name: "Samantha", lang: "en-US", default: true },
  { voiceURI: "com.apple.eloquence.es-MX.Eddy", name: "Eddy (Spanish (Mexico))", lang: "es-MX", default: false },
  { voiceURI: "com.apple.eloquence.es-MX.Grandma", name: "Grandma (Spanish (Mexico))", lang: "es-MX", default: false },
  { voiceURI: "com.apple.speech.synthesis.voice.Bahh", name: "Bahh", lang: "es-MX", default: false },
  { voiceURI: "com.apple.voice.compact.es-ES.Monica", name: "Mónica", lang: "es-ES", default: false },
  { voiceURI: "com.apple.voice.compact.es-MX.Paulina", name: "Paulina", lang: "es-MX", default: false },
];
const ENHANCED = { voiceURI: "com.apple.voice.enhanced.es-MX.Paulina", name: "Paulina (Enhanced)", lang: "es-MX", default: false };

test.use({ locale: "en-MX" });

test.beforeEach(async ({ context }) => {
  github = new FakeGitHub();
  await github.attach(context);
  await context.route("https://example.test/clase", (route) => route.fulfill({
    contentType: "text/markdown", headers: { "Access-Control-Allow-Origin": "*" },
    body: "# Qué es la danzaterapia\n\nEs el uso del movimiento para conocerte y para sanar. ¿Con quién se trabaja? "
      + "Con niñas y niños, con personas mayores y con quien nunca ha bailado en su vida.\n",
  }));
});

test.afterEach(() => {
  expect(github.offline, "requests to the real network").toEqual([]);
});

/** The device's voices, and each sentence said with the voice and language it was given. */
async function device(page, voices) {
  await page.addInitScript((voices) => {
    window.__spoken = [];
    window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
    Object.defineProperty(window, "speechSynthesis", { configurable: true, value: {
      getVoices: () => voices,
      speak(u) { window.__spoken.push({ text: u.text, voice: u.voice && u.voice.voiceURI, lang: u.lang }); setTimeout(() => u.onend && u.onend(), 20); },
      cancel() {},
    } });
  }, voices);
}

async function listen(page, url, text, sentences, voices = IPHONE) {
  await device(page, voices);
  await page.goto("./");
  await page.locator("#url").fill(url);
  await page.locator("#open-url button").click();
  await expect(page.locator("#article")).toContainText(text);
  await page.locator("#play").click();
  await expect.poll(() => page.evaluate(() => window.__spoken.length), { timeout: 10e3 }).toBe(sentences);
  return page.evaluate(() => window.__spoken);
}

const all = (spoken, voice) => expect(spoken.map((s) => s.voice)).toEqual(spoken.map(() => voice));

test("a Spanish page is read by a voice from the device's country, not a robotic one, a sentence at a time", async ({ page }) => {
  const spoken = await listen(page, "https://example.test/clase", "para conocerte", 4);
  all(spoken, "com.apple.voice.compact.es-MX.Paulina");
  expect(spoken[0].lang).toBe("es-MX");
  expect(spoken.map((s) => s.text)).toContain("¿Con quién se trabaja?");
});

test("an enhanced voice the person downloaded is used over a compact one", async ({ page }) => {
  const spoken = await listen(page, "https://example.test/clase", "para conocerte", 4, [...IPHONE, ENHANCED]);
  all(spoken, ENHANCED.voiceURI);
});

test("a page too short to tell its language is left to the device's default voice, as before", async ({ page }) => {
  const spoken = await listen(page, "https://example.test/post", "The cache key ignores the query string.", 3);
  expect(spoken.every((s) => !s.voice && !s.lang)).toBe(true);
});

test("with Kokoro chosen, which speaks only English here, a Spanish page is read by the device's voice", async ({ page }) => {
  await page.addInitScript(() => localStorage.setItem("voce.engine", JSON.stringify("kokoro")));
  const spoken = await listen(page, "https://example.test/clase", "para conocerte", 4);
  all(spoken, "com.apple.voice.compact.es-MX.Paulina");
});

test("settings offer the best voice for each document first, then the device's voices, the better ones marked", async ({ page }) => {
  await device(page, [...IPHONE, ENHANCED]);
  await page.goto("./");
  await page.locator("#settings").click();
  const options = await page.locator("#s-voice option").allInnerTexts();
  expect(options[0]).toBe("The best for each document's language");
  expect(options[1]).toBe("Samantha (en-US)");
  expect(options).toContain("Paulina (Enhanced) (es-MX) · enhanced");
  expect(options.indexOf("Paulina (Enhanced) (es-MX) · enhanced")).toBeLessThan(options.indexOf("Eddy (Spanish (Mexico)) (es-MX)"));
});

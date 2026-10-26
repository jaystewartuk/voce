/* Kokoro in the web app, with a stand-in for the model: what iOS asks of a page before it lets it play sound. */

import { expect, test } from "@playwright/test";
import { FakeGitHub } from "./fake.mjs";

// kokoro-js as the page imports it: it downloads, then takes a while to start and to make each sentence, as the
// real model does.
const KOKORO = `
const wav = (samples, rate) => {
  const b = new DataView(new ArrayBuffer(44 + samples.length * 2));
  const text = (at, t) => [...t].forEach((c, i) => b.setUint8(at + i, c.charCodeAt(0)));
  text(0, "RIFF"); b.setUint32(4, 36 + samples.length * 2, true); text(8, "WAVEfmt "); b.setUint32(16, 16, true);
  b.setUint16(20, 1, true); b.setUint16(22, 1, true); b.setUint32(24, rate, true); b.setUint32(28, rate * 2, true);
  b.setUint16(32, 2, true); b.setUint16(34, 16, true); text(36, "data"); b.setUint32(40, samples.length * 2, true);
  return new Blob([b], { type: "audio/wav" });
};
export class KokoroTTS {
  static async from_pretrained(model, options) {
    window.__kokoro = { device: options.device, dtype: options.dtype };
    const progress = (n, file = "onnx/model.onnx") => options.progress_callback({ status: "progress", progress: n, file });
    await new Promise((r) => setTimeout(r, 300)); // the small files, before the model
    progress(100, "config.json");
    progress(100, "tokenizer.json");
    progress(50);
    await new Promise((r) => setTimeout(r, 300));
    progress(100);
    await new Promise((r) => setTimeout(r, 1200)); // starting, after the download
    return new KokoroTTS();
  }
  constructor() { this.voices = { af_heart: { name: "Heart", language: "en-us", gender: "Female" } }; }
  async model() { return {}; }
  async generate() {
    await this.model({ input_ids: { data: [] } });
    await new Promise((r) => setTimeout(r, 600));
    const audio = new Float32Array(4800);
    return { audio, sampling_rate: 24000, toBlob: () => wav(audio, 24000) };
  }
}`;

let github;

test.beforeEach(async ({ context }) => {
  github = new FakeGitHub();
  await github.attach(context);
  await context.route("https://cdn.jsdelivr.net/npm/kokoro-js@*/**", (route) =>
    route.fulfill({ contentType: "text/javascript", headers: { "Access-Control-Allow-Origin": "*" }, body: KOKORO }));
  await context.addInitScript(() => {
    localStorage.setItem("voce.engine", JSON.stringify("kokoro"));
    // Each time the page asks to play, whether it was while a tap was being handled, as iOS requires.
    window.__plays = [];
    // Everything the player's status line says, in order.
    window.__said = [];
    setInterval(() => {
      const t = document.getElementById("status")?.textContent;
      if (t && window.__said.at(-1) !== t) window.__said.push(t);
    }, 20);
    const play = HTMLMediaElement.prototype.play;
    HTMLMediaElement.prototype.play = function () {
      window.__plays.push({ inTap: !!window.event && window.event.type === "click" });
      return play.call(this);
    };
  });
});

test.afterEach(() => {
  expect(github.offline, "requests to the real network").toEqual([]);
});

async function openPage(page) {
  await page.goto("./");
  await page.locator("#url").fill("https://example.test/post");
  await page.locator("#open-url button").click();
  await expect(page.locator("#article")).toContainText("The cache key ignores the query string.");
}

test("the first press of play starts sound during the tap, before the model has loaded", async ({ page }) => {
  await openPage(page);
  await page.locator("#play").click();
  await expect.poll(() => page.evaluate(() => window.__plays.length)).toBeGreaterThan(1); // the silence, then a sentence
  const plays = await page.evaluate(() => window.__plays);
  expect(plays[0].inTap, "iOS refuses sound that a page starts after a tap is over").toBe(true);
});

test("an iPhone gets the smaller model, on the CPU", async ({ browser }) => {
  const context = await browser.newContext({
    userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1",
    baseURL: "http://localhost:8787/app/",
  });
  github = new FakeGitHub();
  await github.attach(context);
  await context.route("https://cdn.jsdelivr.net/npm/kokoro-js@*/**", (route) =>
    route.fulfill({ contentType: "text/javascript", headers: { "Access-Control-Allow-Origin": "*" }, body: KOKORO }));
  await context.addInitScript(() => {
    localStorage.setItem("voce.engine", JSON.stringify("kokoro"));
    Object.defineProperty(navigator, "gpu", { value: {} }); // Safari has WebGPU from iOS 26
  });
  const page = await context.newPage();
  await openPage(page);
  await page.locator("#play").click();
  await expect.poll(() => page.evaluate(() => window.__kokoro)).toEqual({ device: "wasm", dtype: "q8" });
  await context.close();
});


test("from the tap, the player says it is getting the voice, then downloading it, starting it, then making the sentence, until it plays", async ({ page }) => {
  await openPage(page);
  await page.locator("#play").click();
  // until the first sentence has been made and the status says where the reader is again
  await expect.poll(() => page.evaluate(() => window.__said.findIndex((t) => /Making/.test(t)) >= 0
    && /left/.test(window.__said.at(-1))), { timeout: 10e3 }).toBe(true);
  const said = await page.evaluate(() => window.__said);
  const at = (re) => said.findIndex((t) => re.test(t));
  expect(at(/Getting the voice/), said.join(" | ")).toBeGreaterThanOrEqual(0);
  expect(at(/Downloading the voice: 50%/)).toBeGreaterThan(at(/Getting the voice/));
  expect(at(/Starting the voice/), "said only once the model is here").toBeGreaterThan(at(/Downloading the voice: 50%/));
  expect(at(/Making the first sentence/)).toBeGreaterThan(at(/Starting the voice/));
  expect(said.slice(at(/Making the first sentence/) + 1).every((t) => /left/.test(t)), said.join(" | ")).toBe(true);
});

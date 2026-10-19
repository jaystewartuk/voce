/* voce on any device: the library and places from your own git repository, played by a voice in the page.

   The Mac did the reading work (prepared/<hash>.json holds the blocks to show and the units to say); this page
   fetches those through the GitHub API, plays them, and writes your place back as places/<hash>.json. You sign in
   with GitHub: the voce GitHub App, installed on the one repository, gives this page a token for it, and a relay
   (relay/worker.js, a stateless function) does the code-for-token swap that GitHub won't let a page do. The
   library itself never leaves GitHub and this device. A fine-grained token pasted by hand works the same way.

   The page also carries voce's own reading code (py.js: Python in the browser), so it can read a playlist straight
   from a repository, or a file from this device, with nothing prepared on a Mac first. */

const API = "https://api.github.com";
// The GitHub App and its relay. With no client ID, the connect screen offers only the token form.
const GITHUB_APP = { client: "Iv23liKDXAS67GVEUEA6", slug: "voce-reader", relay: "https://voce-relay.jay73x.workers.dev" };
const KOKORO_URL = "https://cdn.jsdelivr.net/npm/kokoro-js@1.2.1/+esm";
const KOKORO_MODEL = "onnx-community/Kokoro-82M-v1.0-ONNX";
const AHEAD = 3;          // units generated ahead of the one playing
const SAVE_EVERY = 120e3; // ms between saves while playing
const HOST = "web";

const $ = (id) => document.getElementById(id);
const store = {
  get: (k, d = null) => { try { const v = localStorage.getItem("voce." + k); return v === null ? d : JSON.parse(v); } catch { return d; } },
  set: (k, v) => { try { localStorage.setItem("voce." + k, JSON.stringify(v)); } catch { /* private window */ } },
  del: (k) => { try { localStorage.removeItem("voce." + k); } catch { /* ignore */ } },
};
const now = () => new Date().toISOString().replace(/\.\d{3}Z$/, "Z");

// ---------------------------------------------------------------- signing in

/** The token GitHub gave this device, refreshed through the relay when it is about to expire. */
class Auth {
  constructor(fields) { Object.assign(this, { token: "", refresh: "", expires: 0, manual: false }, fields); }
  static manual(token) { return new Auth({ token, manual: true }); }
  static fromGrant(g) {
    return new Auth({ token: g.access_token, refresh: g.refresh_token || "", expires: g.expires_in ? Date.now() + g.expires_in * 1000 : 0 });
  }
  static saved() {
    const a = store.get("auth");
    if (a) return new Auth(a);
    const old = store.get("token"); // a token pasted before sign-in existed
    return old ? Auth.manual(old) : null;
  }
  save() { store.set("auth", { token: this.token, refresh: this.refresh, expires: this.expires, manual: this.manual }); }
  async bearer() {
    if (this.refresh && this.expires && Date.now() > this.expires - 120e3) {
      const g = await relay("refresh", { refresh_token: this.refresh });
      Object.assign(this, Auth.fromGrant(g));
      this.save();
    }
    return this.token;
  }
}

async function relay(step, body) {
  if (!GITHUB_APP.relay) throw new Error("Signing in isn't set up on this copy of the app.");
  let r;
  try { r = await fetch(`${GITHUB_APP.relay}/${step}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); }
  catch { throw new Error("Couldn't reach the sign-in relay. Check the connection and try again."); }
  const d = await r.json().catch(() => ({}));
  if (!r.ok || d.error) throw new Error(d.error_description || d.error || `The sign-in relay said ${r.status}.`);
  return d;
}

const here = () => location.origin + location.pathname;

/** Off to GitHub: to authorize the app, or to install it on a repository. Back at here() with a code. */
function signIn(install = false) {
  const state = crypto.randomUUID();
  store.set("signin", state);
  const u = install ? new URL(`https://github.com/apps/${GITHUB_APP.slug}/installations/new`)
                    : new URL("https://github.com/login/oauth/authorize");
  if (!install) { u.searchParams.set("client_id", GITHUB_APP.client); u.searchParams.set("redirect_uri", here()); }
  u.searchParams.set("state", state);
  location.href = u.href;
}

/** Back from GitHub with ?code=: swap it for a token. True when a sign-in was finished here. */
async function finishSignIn() {
  const q = new URLSearchParams(location.search);
  if (!q.has("code") && !q.has("error")) return false;
  history.replaceState(null, "", location.pathname + location.hash);
  const expected = store.get("signin");
  store.del("signin");
  if (q.has("error")) throw new Error(q.get("error_description") || "GitHub didn't sign you in.");
  if (!expected || q.get("state") !== expected) throw new Error("The sign-in didn't come back the way it left. Try again.");
  const grant = await relay("token", { code: q.get("code"), redirect_uri: here() });
  auth = Auth.fromGrant(grant);
  auth.save();
  return true;
}

/** One GitHub API call with this device's token. 404 is returned, not thrown. */
async function gh(auth, path, init = {}) {
  const r = await fetch(API + path, {
    ...init,
    headers: { Authorization: `Bearer ${await auth.bearer()}`, Accept: "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", ...(init.headers || {}) },
  });
  if (!r.ok && r.status !== 404) {
    const text = await r.text().catch(() => "");
    throw new Error(r.status === 401 ? (auth.manual ? "GitHub didn't accept the token." : "GitHub signed this device out. Sign in again.")
      : r.status === 403 ? "voce can't reach this repository, or the API limit is reached for the hour."
      : `GitHub said ${r.status}. ${text.slice(0, 120)}`);
  }
  return r;
}

/** The repositories the app is installed on, as owner/name. */
async function reachable(auth) {
  const { installations = [] } = await (await gh(auth, "/user/installations?per_page=100")).json();
  const names = [];
  for (const i of installations) {
    const d = await (await gh(auth, `/user/installations/${i.id}/repositories?per_page=100`)).json();
    names.push(...(d.repositories || []).map((r) => r.full_name));
  }
  return names;
}

// ---------------------------------------------------------------- the repository

class Repo {
  constructor(name, auth) { this.name = name; this.auth = auth; this.trees = {}; }

  api(path, init) { return gh(this.auth, path, init); }

  async check() {
    const r = await this.api(`/repos/${this.name}`);
    if (r.status === 404) throw new Error(this.auth.manual ? "No such repository, or the token can't see it."
                                                           : "voce can't see that repository any more. Choose another, or give voce access to it on GitHub.");
  }

  /** {path: sha} for the files in a folder, in one request; with deep, every file under it. */
  async tree(folder, deep = false) {
    const r = await this.api(`/repos/${this.name}/git/trees/${folder ? "HEAD:" + encodeURI(folder) : "HEAD"}${deep ? "?recursive=1" : ""}`);
    if (r.status === 404) return {};
    const d = await r.json();
    return Object.fromEntries(d.tree.filter((e) => e.type === "blob").map((e) => [e.path, e.sha]));
  }

  /** A blob's text, cached by its sha so an unchanged file is never fetched twice. */
  async blob(sha) {
    const cache = await caches.open("voce-blobs").catch(() => null);
    const key = `${API}/repos/${this.name}/git/blobs/${sha}`;
    const hit = cache && await cache.match(key);
    if (hit) return hit.text();
    const r = await this.api(`/repos/${this.name}/git/blobs/${sha}`, { headers: { Accept: "application/vnd.github.raw+json" } });
    if (r.status === 404) throw new Error("That file is gone from the repository.");
    const text = await r.text();
    if (cache) cache.put(key, new Response(text)).catch(() => {});
    return text;
  }

  /** Write a file; sha is the version being replaced. 409/422 means someone else wrote first. */
  async put(path, text, sha, message) {
    const body = { message, content: btoa(unescape(encodeURIComponent(text))), ...(sha ? { sha } : {}) };
    const r = await fetch(`${API}/repos/${this.name}/contents/${path}`, {
      method: "PUT", keepalive: true,
      headers: { Authorization: `Bearer ${await this.auth.bearer()}`, Accept: "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (r.status === 409 || r.status === 422) return null;
    if (!r.ok) throw new Error(`Couldn't save your place: GitHub said ${r.status}.`);
    return (await r.json()).content.sha;
  }
}

// ---------------------------------------------------------------- voce's reading code, in the page

/** py.js in a worker: Markdown in, the same prepared JSON the Mac writes out. Loaded the first time it is needed. */
const py = {
  worker: null, pending: new Map(), seq: 0,
  call(op, data) {
    if (!this.worker) {
      this.worker = new Worker("py.js", { type: "module" });
      this.worker.onmessage = ({ data: m }) => {
        if (m.progress !== undefined) { ui.busy(m.progress); return; }
        const p = this.pending.get(m.id);
        if (!p) return;
        this.pending.delete(m.id);
        m.error ? p.reject(new Error(m.error)) : p.resolve(m.result);
      };
      this.worker.onerror = (e) => {
        for (const p of this.pending.values()) p.reject(new Error(e.message || "voce's reader couldn't load"));
        this.pending.clear(); this.worker.terminate(); this.worker = null;
      };
    }
    const id = ++this.seq;
    return new Promise((resolve, reject) => { this.pending.set(id, { resolve, reject }); this.worker.postMessage({ id, op, ...data }); });
  },
  prepare(text, name) { return this.call("prepare", { text, name }); },
  /** Which reading code the page carries, from the manifest beside the wheel: names the cache of prepared copies. */
  async made() {
    if (!this._made) this._made = fetch("py/manifest.json").then((r) => r.json()).then((m) => m.made).catch(() => { this._made = null; return "unknown"; });
    return this._made;
  },
};

const sha256 = async (text) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)))].map((b) => b.toString(16).padStart(2, "0")).join("");

// A README's "## Listen in this order" section, the same way playlist.py reads it.
const PLAYLIST = /^## (?:Listen in this order|Listening order|Playlist)\b.*?$([\s\S]*?)(?=^## |$(?![\s\S]))/m;
const ITEM = /^\s*\d+\.\s+\[([^\]]+)\]\(([^)#\s]+\.md)(?:#[^)]*)?\)/;
const unmark = (s) => s.replace(/\[([^\]]+)\]\([^)]*\)/g, "$1").replace(/(\*\*|__|[*_`~])/g, "").trim();

function parsePlaylist(text) {
  const m = PLAYLIST.exec(text);
  if (!m) return [];
  const items = [];
  let part = "";
  for (const line of m[1].split("\n")) {
    const h = /^###\s+(.*)/.exec(line);
    if (h) { part = unmark(h[1]); continue; }
    const it = ITEM.exec(line);
    if (!it) continue;
    const mins = /·\s*(\d+)\s*min\b/.exec(line);
    items.push({ path: it[2], title: unmark(it[1]), part, minutes: mins ? +mins[1] : 0 });
  }
  return items;
}

/** A link as written in a README, as a path under the README's folder; null when it leads out of that folder. */
function under(rel) {
  const out = [];
  for (const seg of rel.split("/")) {
    if (seg === "..") { if (!out.length) return null; out.pop(); }
    else if (seg !== "." && seg) out.push(seg);
  }
  return out.join("/");
}

// ---------------------------------------------------------------- the library and places

/** The documents to listen to: playlists read straight from repositories, then the Mac's prepared copies, then
    files opened on this device. Each is named by the hash of its text, which is what names its place too. */
class Library {
  constructor(repo, auth) {
    this.repo = repo; this.auth = auth;
    this.docs = []; this.places = {}; this.placeShas = {}; this.local = {}; this.notes = [];
  }

  async load() {
    const [prepared, places] = await Promise.all([this.repo.tree("prepared"), this.repo.tree("places")]);
    this.prepared = prepared;
    this.placeShas = places;
    const index = prepared["index.json"] ? JSON.parse(await this.repo.blob(prepared["index.json"])) : { documents: [] };
    const entries = await Promise.all(Object.entries(places)
      .filter(([name]) => /^[0-9a-f]{64}\.json$/.test(name))
      .map(async ([name, sha]) => { try { return [name.slice(0, 64), JSON.parse(await this.repo.blob(sha))]; } catch { return null; } }));
    this.places = Object.fromEntries(entries.filter(Boolean));
    const docs = [], seen = new Set(), notes = [];
    const add = (d) => { if (!seen.has(d.hash)) { seen.add(d.hash); docs.push(d); } };
    for (const source of store.get("sources", [])) {
      try { (await this.fromSource(source)).forEach(add); }
      catch (e) { notes.push(`${source.repo} ${source.path}: ${e.message}`); }
    }
    index.documents.filter((d) => prepared[`${d.hash}.json`]).forEach(add);
    Object.values(this.local).forEach((d) => add({ hash: d.hash, title: d.title, part: "On this device", minutes: d.minutes }));
    this.docs = docs;
    this.notes = notes;
  }

  /** The documents of one playlist README in a repository, each with the sha of its text and the hash of it. */
  async fromSource(source) {
    const repo = new Repo(source.repo, this.auth);
    const dir = source.path.includes("/") ? source.path.slice(0, source.path.lastIndexOf("/")) : "";
    const tree = await repo.tree(dir, true);                       // paths under the README's folder
    const readme = tree[dir ? source.path.slice(dir.length + 1) : source.path];
    if (!readme) throw new Error("no such file");
    const items = parsePlaylist(await repo.blob(readme));
    if (!items.length) throw new Error('no "## Listen in this order" section');
    const found = items.map((it) => ({ ...it, rel: under(it.path) })).filter((it) => it.rel && tree[it.rel]);
    if (!found.length) throw new Error("none of its files are in that folder");
    const docs = [];
    for (let i = 0; i < found.length; i += 6) {        // a few at a time; each blob is fetched once and kept by its sha
      docs.push(...await Promise.all(found.slice(i, i + 6).map(async (it) => {
        const sha = tree[it.rel];
        return { hash: await sha256(await repo.blob(sha)), title: it.title, part: it.part, minutes: it.minutes,
                 sha, name: it.rel.split("/").pop(), source };
      })));
    }
    return docs;
  }

  async doc(hash) {
    if (this.local[hash]) return this.local[hash];
    const d = this.docs.find((x) => x.hash === hash);
    if (d && d.sha) return this.prepareFrom(d);
    if (this.prepared[`${hash}.json`]) return JSON.parse(await this.repo.blob(this.prepared[`${hash}.json`]));
    throw new Error("That document isn't in the library any more.");
  }

  /** A playlist document read by the page's own voce, kept by the text's sha and the reading code that made it. */
  async prepareFrom(d) {
    const cache = await caches.open("voce-blobs").catch(() => null);
    const key = `${API}/prepared/${d.sha}/${await py.made()}`;
    const hit = cache && await cache.match(key);
    if (hit) return hit.json();
    const text = await new Repo(d.source.repo, this.auth).blob(d.sha);
    const out = await py.prepare(text, d.name);
    if (cache) cache.put(key, new Response(JSON.stringify(out))).catch(() => {});
    return out;
  }

  /** A file from this device, read now and listed under "On this device" until the page is closed. */
  async open(text, name) {
    const out = await py.prepare(text, name);
    this.local[out.hash] = out;
    if (!this.docs.some((d) => d.hash === out.hash)) this.docs.push({ hash: out.hash, title: out.title, part: "On this device", minutes: out.minutes });
    return out.hash;
  }

  progress(hash) {
    const p = this.places[hash];
    if (!p) return { text: "", ratio: 0 };
    if (p.done) return { text: "done", ratio: 1, done: true };
    if (!p.pos) return { text: "", ratio: 0 };
    const ratio = p.pos / Math.max(1, p.total || 1);
    return { text: `${Math.floor(100 * ratio)}%`, ratio };
  }

  /** Save a place, keeping the newer one when another device wrote meanwhile. */
  async save(hash, title, fields) {
    const current = this.places[hash] || {};
    const place = { ...current, ...fields, updated: now(), paths: { ...(current.paths || {}), [HOST]: title } };
    this.places[hash] = place;
    for (let attempt = 0; attempt < 3; attempt++) {
      const sha = await this.repo.put(`places/${hash}.json`, JSON.stringify(place, null, 1), this.placeShas[`${hash}.json`],
                                      `web: ${title.slice(0, 60)}`);
      if (sha) { this.placeShas[`${hash}.json`] = sha; return place; }
      const fresh = await this.repo.tree("places");
      const theirSha = fresh[`${hash}.json`];
      this.placeShas[`${hash}.json`] = theirSha;
      if (theirSha) {
        const theirs = JSON.parse(await this.repo.blob(theirSha));
        if ((theirs.updated || "") > place.updated) { this.places[hash] = theirs; return theirs; }
      }
    }
    throw new Error("Couldn't save your place after three tries.");
  }
}

// ---------------------------------------------------------------- voices

class BrowserVoice {
  constructor(name) { this.name = name; this.kind = "browser"; this.utterance = null; }
  static voices() {
    return speechSynthesis.getVoices().filter((v) => v.lang.startsWith("en")).map((v) => ({ id: v.voiceURI, label: `${v.name} (${v.lang})` }));
  }
  async ready() { if (!speechSynthesis.getVoices().length) await new Promise((r) => { speechSynthesis.onvoiceschanged = r; setTimeout(r, 500); }); }
  prefetch() {}
  speak(text, speed, onEnd, onError) {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const voice = speechSynthesis.getVoices().find((v) => v.voiceURI === this.name);
    if (voice) u.voice = voice;
    u.rate = speed;
    u.onend = () => { if (this.utterance === u) onEnd(); };
    u.onerror = (e) => { if (this.utterance === u && e.error !== "interrupted" && e.error !== "canceled") onError(e.error); };
    this.utterance = u;
    speechSynthesis.speak(u);
  }
  pause() { speechSynthesis.pause(); }
  resume() { speechSynthesis.resume(); }
  stop() { this.utterance = null; speechSynthesis.cancel(); }
  setSpeed() {} // takes effect from the next sentence
}

class KokoroVoice {
  constructor(name, onProgress) {
    this.name = name || "af_heart"; this.kind = "kokoro"; this.onProgress = onProgress;
    this.audio = new Audio(); this.audio.preload = "auto";
    this.clips = new Map(); this.generating = Promise.resolve();
  }
  static async load(onProgress) {
    if (KokoroVoice.tts) return KokoroVoice.tts;
    if (!KokoroVoice.loading) {
      KokoroVoice.loading = (async () => {
        const { KokoroTTS } = await import(KOKORO_URL);
        const webgpu = !!navigator.gpu;
        KokoroVoice.tts = await KokoroTTS.from_pretrained(KOKORO_MODEL, {
          dtype: webgpu ? "fp32" : "q8", device: webgpu ? "webgpu" : "wasm",
          progress_callback: (p) => { if (p.status === "progress" && onProgress) onProgress(p.progress || 0, p.file); },
        });
        return KokoroVoice.tts;
      })().catch((e) => { KokoroVoice.loading = null; throw e; });
    }
    return KokoroVoice.loading;
  }
  static voices() {
    const tts = KokoroVoice.tts;
    if (!tts) return [{ id: "af_heart", label: "Heart (downloads the model first)" }];
    return Object.entries(tts.voices || tts.list_voices?.() || {}).map(([id, v]) => ({ id, label: `${v.name || id} · ${v.language === "en-gb" ? "British" : "American"} ${v.gender || ""}`.trim() }));
  }
  async ready() { await KokoroVoice.load(this.onProgress); }
  /** A WAV for a sentence, generated once; generation is serialised so the model is never asked twice at once. */
  clip(text) {
    if (!this.clips.has(text)) {
      const job = this.generating.then(async () => {
        const audio = await KokoroVoice.tts.generate(text, { voice: this.name });
        return URL.createObjectURL(audio.toBlob());
      });
      this.generating = job.catch(() => {});
      this.clips.set(text, job);
      if (this.clips.size > 40) this.clips.delete(this.clips.keys().next().value);
    }
    return this.clips.get(text);
  }
  prefetch(texts) { texts.forEach((t) => this.clip(t).catch(() => {})); }
  async speak(text, speed, onEnd, onError) {
    const token = this.token = {};
    let url;
    try { url = await this.clip(text); } catch (e) { if (this.token === token) onError(e.message); return; }
    if (this.token !== token) return;
    this.audio.src = url;
    this.audio.playbackRate = speed;
    this.audio.onended = () => { if (this.token === token) onEnd(); };
    this.audio.onerror = () => { if (this.token === token) onError("the clip wouldn't play"); };
    try { await this.audio.play(); } catch (e) { if (this.token === token) onError(e.message); }
  }
  pause() { this.audio.pause(); }
  resume() { this.audio.play().catch(() => {}); }
  stop() { this.token = {}; this.audio.pause(); this.audio.removeAttribute("src"); }
  setSpeed(speed) { this.audio.playbackRate = speed; }
}

// ---------------------------------------------------------------- the reader

class Reader {
  constructor(library, voice, ui) {
    this.library = library; this.voice = voice; this.ui = ui;
    this.doc = null; this.hash = ""; this.pos = 0; this.playing = false; this.timer = null; this.lastSave = 0;
    this.speed = store.get("speed", 1.0);
  }

  async open(hash) {
    this.stop();
    this.hash = hash;
    this.doc = await this.library.doc(hash);
    this.units = this.doc.units;
    this.pos = this.resume();
    this.ui.render(this.doc, this.units);
    this.show();
  }

  /** Where to start: the saved sentence, found again by its text if the document changed since. */
  resume() {
    const p = this.library.places[this.hash];
    if (!p || p.done || !this.units.length) return 0;
    const at = p.at || "";
    if (p.pos >= 0 && p.pos < this.units.length && this.units[p.pos].say.slice(0, 80) === at) return p.pos;
    const i = this.units.findIndex((u) => at && u.say.slice(0, 80) === at);
    return i >= 0 ? i : Math.max(0, Math.min(p.pos || 0, this.units.length - 1));
  }

  show() { this.ui.highlight(this.pos, this.units.length); }

  go(i, play = this.playing) {
    this.pos = Math.max(0, Math.min(i, this.units.length - 1));
    this.show();
    if (play) this.play(); else this.stopVoice();
  }

  async play() {
    if (!this.units.length) return;
    this.playing = true;
    this.ui.setPlaying(true);
    try { await this.voice.ready(); } catch (e) { this.fail(`The voice couldn't load: ${e.message}`); return; }
    this.sayCurrent();
  }

  sayCurrent() {
    const unit = this.units[this.pos];
    this.voice.prefetch(this.units.slice(this.pos + 1, this.pos + 1 + AHEAD).map((u) => u.say));
    this.ui.status(`${this.pos + 1} of ${this.units.length}`);
    this.voice.speak(unit.say, this.speed,
      () => this.after(unit),
      (why) => this.fail(`The voice stopped: ${why}`));
    if (Date.now() - this.lastSave > SAVE_EVERY) this.save();
  }

  after(unit) {
    if (!this.playing) return;
    const wait = (unit.wait ? 2.5 : unit.pause) * 1000 / this.speed;
    this.timer = setTimeout(() => {
      if (!this.playing) return;
      if (this.pos + 1 >= this.units.length) { this.finish(); return; }
      this.pos += 1;
      this.show();
      this.sayCurrent();
    }, wait);
  }

  pause() {
    this.playing = false;
    clearTimeout(this.timer);
    this.voice.stop();
    this.ui.setPlaying(false);
    this.save();
  }

  stopVoice() { clearTimeout(this.timer); this.voice.stop(); }

  stop() {
    if (this.doc && (this.playing || this.pos)) this.save();
    this.playing = false;
    this.stopVoice();
    this.ui.setPlaying(false);
  }

  finish() {
    this.playing = false;
    this.ui.setPlaying(false);
    this.ui.status("Finished.");
    this.save({ done: true, pos: 0, at: "" });
  }

  fail(message) {
    this.playing = false;
    this.stopVoice();
    this.ui.setPlaying(false);
    this.ui.status(message);
  }

  setSpeed(x) {
    this.speed = x;
    store.set("speed", x);
    this.voice.setSpeed(x);
    this.ui.speed(x);
  }

  save(fields) {
    if (!this.doc) return;
    this.lastSave = Date.now();
    const unit = this.units[this.pos];
    const place = fields || { pos: this.pos, at: unit ? unit.say.slice(0, 80) : "", total: this.units.length, done: false };
    this.library.save(this.hash, this.doc.title, place).catch((e) => this.ui.status(e.message));
  }
}

// ---------------------------------------------------------------- the screen

const INLINE = { bold: "b", italic: "i", strike: "s", code: "c", link: "l" };

function renderBlocks(doc, units) {
  const article = $("article");
  article.replaceChildren();
  const byBlock = new Map();
  units.forEach((u, i) => { if (u.block >= 0) { if (!byBlock.has(u.block)) byBlock.set(u.block, []); byBlock.get(u.block).push([u.start, u.end, i]); } });
  const h1 = document.createElement("h1"); // the title line, when the document doesn't open with one
  if (!doc.blocks.length || doc.blocks[0].kind !== "h1") { h1.textContent = doc.title; article.append(h1); }
  let list = null;
  doc.blocks.forEach((b, bi) => {
    const el = element(b);
    (el.querySelector(".body") || el).append(...segments(b, byBlock.get(bi) || []));
    if (b.kind === "li") {
      if (!list) { list = document.createElement("div"); list.className = "list"; article.append(list); }
      list.append(el);
    } else { list = null; article.append(el); }
  });
  const end = document.createElement("p"); end.className = "end"; end.textContent = "·";
  article.append(end);
}

function element(b) {
  if (/^h[1-6]$/.test(b.kind)) return document.createElement(b.kind);
  if (b.kind === "hr") return document.createElement("hr");
  if (b.kind === "code") { const pre = document.createElement("pre"); if (b.lang) pre.dataset.lang = b.lang; return pre; }
  const el = document.createElement(b.kind === "p" ? "p" : "div");
  el.className = b.kind + (b.kind === "row" && b.spans.some((s) => s[2].includes("bold")) ? " bold" : "");
  if (b.kind === "li") {
    el.style.marginLeft = `${1.4 * b.indent}em`;
    const prefix = document.createElement("span"); prefix.className = "prefix"; prefix.textContent = b.prefix || "•";
    el.append(prefix);
    const body = document.createElement("span"); body.className = "body"; el.append(body);
  }
  return el;
}

/** The block's text cut at every unit edge and every style edge, each piece knowing its unit and its styles. */
function segments(b, unitRanges) {
  const text = b.text;
  const edges = new Set([0, text.length]);
  unitRanges.forEach(([s, e]) => { edges.add(s); edges.add(e); });
  b.spans.forEach(([s, e]) => { edges.add(s); edges.add(e); });
  const cuts = [...edges].filter((x) => x >= 0 && x <= text.length).sort((a, c) => a - c);
  const out = [];
  for (let k = 0; k + 1 < cuts.length; k++) {
    const [s, e] = [cuts[k], cuts[k + 1]];
    if (s === e) continue;
    const span = document.createElement("span");
    span.textContent = text.slice(s, e);
    const classes = [];
    b.spans.forEach(([ss, se, roles]) => { if (ss <= s && e <= se) roles.forEach((r) => classes.push(INLINE[r] || r)); });
    const unit = unitRanges.find(([us, ue]) => us <= s && e <= ue);
    if (unit) span.dataset.unit = unit[2];
    if (classes.length) span.className = classes.join(" ");
    out.push(span);
  }
  return b.kind === "code" ? grouped(out) : out;
}

/** In code, one span per unit holding its styled pieces, so a line lights up as one band across the block. */
function grouped(spans) {
  const out = [];
  let wrap = null;
  for (const s of spans) {
    const unit = s.dataset.unit;
    if (unit === undefined) { wrap = null; out.push(s); continue; }
    if (!wrap || wrap.dataset.unit !== unit) { wrap = document.createElement("span"); wrap.dataset.unit = unit; out.push(wrap); }
    delete s.dataset.unit;
    wrap.append(s);
  }
  return out;
}

const ui = {
  render(doc, units) { renderBlocks(doc, units); $("title").textContent = doc.title; },
  highlight(i, total) {
    document.querySelectorAll("[data-unit].now").forEach((el) => el.classList.remove("now"));
    const els = document.querySelectorAll(`[data-unit="${i}"]`);
    els.forEach((el) => el.classList.add("now"));
    if (els[0]) { const r = els[0].getBoundingClientRect(); if (r.top < 80 || r.bottom > innerHeight - 140) els[0].scrollIntoView({ block: "center", behavior: "smooth" }); }
    $("progress").style.width = `${100 * (i + 1) / Math.max(1, total)}%`;
  },
  setPlaying(on) {
    $("play-icon").innerHTML = on ? '<path d="M7 5h4v14H7zM13 5h4v14h-4z"/>' : '<path d="M8 5v14l11-7z"/>';
    $("play").setAttribute("aria-label", on ? "Pause" : "Play");
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = on ? "playing" : "paused";
  },
  status(text) { $("status").textContent = text; },
  /** Progress while voce's reader loads: in the player's status, and in whichever "Loading…" note is on screen. */
  busy(text) { if (text) $("status").textContent = text; const n = document.querySelector(".note.busy"); if (n && text) n.textContent = text; },
  speed(x) { $("speed").textContent = `${x.toFixed(1)}×`; },
};

// ---------------------------------------------------------------- the app

let auth, repo, library, reader, voice;

function show(view) {
  ["connect", "library", "reader"].forEach((v) => $(v).classList.toggle("hidden", v !== view));
  $("player").classList.toggle("hidden", view !== "reader");
  $("refresh").classList.toggle("hidden", view === "connect");
  if (view !== "reader") $("title").textContent = "";
}

/** The connect screen in one of its states: "signin", "busy", "choose" (with the repositories) or "install". */
function connectView(state, repos = []) {
  show("connect");
  const signedIn = state !== "signin";
  $("signin").classList.toggle("hidden", signedIn);
  $("choose").classList.toggle("hidden", !signedIn);
  $("connect-status").textContent = state === "busy" ? "Signing in…" : "";
  $("signin-go").disabled = state === "busy";
  if (!signedIn) return;
  $("choose-title").textContent = state === "install" ? "Give voce access to your library" : state === "busy" ? "Signing in…" : "Which repository?";
  $("choose-lead").textContent = state === "install"
    ? "voce isn't installed on any of your repositories yet. On GitHub, choose the one voce --sync made."
    : state === "busy" ? "" : "The repositories voce can reach. Choose the one voce --sync made.";
  $("repos").replaceChildren(...repos.map((name) => {
    const b = document.createElement("button"); b.className = "btn quiet repo"; b.textContent = name;
    b.onclick = () => useRepo(name);
    return b;
  }));
  $("install-go").textContent = state === "install" ? "Choose the repository on GitHub" : "Give voce access to another repository";
}

function fail(message) {
  $("connect-error").textContent = message;
  $("connect-error").classList.remove("hidden");
}

function makeVoice() {
  const engine = store.get("engine", "browser");
  const name = store.get(`voice.${engine}`, engine === "kokoro" ? "af_heart" : "");
  return engine === "kokoro"
    ? new KokoroVoice(name, (p, file) => ui.status(`Downloading the voice: ${Math.round(p)}% of ${file || "the model"}`))
    : new BrowserVoice(name);
}

async function connect(name, with_) {
  repo = new Repo(name, with_);
  await repo.check();
  auth = with_;
  auth.save();
  store.set("repo", name);
  library = new Library(repo, auth);
  voice = makeVoice();
  reader = new Reader(library, voice, ui);
  ui.speed(reader.speed);
}

/** Signed in: settle on a repository. The remembered one, the only one, or ask. */
async function pickRepo() {
  connectView("busy");
  let repos;
  try { repos = await reachable(auth); } catch (e) { connectView("signin"); fail(e.message); return; }
  const remembered = store.get("repo");
  if (remembered && repos.includes(remembered)) return useRepo(remembered);
  if (repos.length === 1) return useRepo(repos[0]);
  connectView(repos.length ? "choose" : "install", repos.sort((a, b) => /voce/i.test(b) - /voce/i.test(a)));
}

async function useRepo(name) {
  $("connect-error").classList.add("hidden");
  try { await connect(name, auth); location.hash = "#/"; await route(); }
  catch (e) { connectView("choose", await reachable(auth).catch(() => [])); fail(e.message); }
}

async function showLibrary() {
  show("library");
  const el = $("library");
  el.innerHTML = '<p class="note">Loading your library…</p>';
  try { await library.load(); } catch (e) { el.innerHTML = `<p class="error">${e.message}</p>`; return; }
  el.replaceChildren();
  for (const n of library.notes) { const p = document.createElement("p"); p.className = "error"; p.textContent = `Couldn't read ${n}`; el.append(p); }
  if (!library.docs.length) {
    el.insertAdjacentHTML("beforeend", '<h1 class="page">Nothing here yet</h1><p class="lead">In settings, add a playlist from a repository voce can reach, or open a Markdown file below. On the Mac, <code>voce --sync</code> sends your playlist here too.</p>');
  }
  let part;
  for (const d of library.docs) {
    if (d.part !== part) { part = d.part; const h = document.createElement("div"); h.className = "part"; h.textContent = part || (library.docs[0].part ? "Also" : "Library"); el.append(h); }
    const p = library.progress(d.hash);
    const b = document.createElement("button"); b.className = "doc"; b.dataset.hash = d.hash;
    b.innerHTML = `<span class="mark ${p.done ? "done" : ""}">${p.done ? "✓" : p.text}</span>
      <span class="name">${esc(d.title)}<small>${d.minutes ? `${Math.round(d.minutes)} min` : ""}</small>
      <span class="bar"><i style="width:${100 * p.ratio}%"></i></span></span>`;
    b.onclick = () => { location.hash = `#/doc/${d.hash}`; };
    el.append(b);
  }
  const open = document.createElement("div"); open.className = "actions open-file";
  open.innerHTML = '<button class="btn quiet" id="open-file">Open a Markdown file</button><span class="note busy" id="open-note"></span>';
  el.append(open);
  $("open-file").onclick = () => $("file").click();
}

async function openFile(file) {
  if (!file || !library) return;
  $("open-note").textContent = "Reading…";
  try {
    const hash = await library.open(await file.text(), file.name);
    location.hash = `#/doc/${hash}`;
  } catch (e) { $("open-note").textContent = `Couldn't read it: ${e.message}`; }
}

function esc(s) { return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

async function showDoc(hash) {
  show("reader");
  $("article").innerHTML = '<p class="note busy">Loading…</p>';
  try {
    if (!library.docs.length) await library.load();
    await reader.open(hash);
    ui.status(`${reader.pos + 1} of ${reader.units.length}`);
    if ("mediaSession" in navigator) navigator.mediaSession.metadata = new MediaMetadata({ title: reader.doc.title, artist: "voce" });
  } catch (e) { $("article").innerHTML = `<p class="error">${esc(e.message)}</p>`; }
}

async function route() {
  if (!repo) { show("connect"); return; }
  const m = location.hash.match(/^#\/doc\/([0-9a-f]{64})$/);
  if (m) await showDoc(m[1]);
  else { if (reader) reader.stop(); await showLibrary(); }
}

function fillVoices() {
  const engine = store.get("engine", "browser");
  $("s-engine").value = engine;
  const list = engine === "kokoro" ? KokoroVoice.voices() : BrowserVoice.voices();
  const chosen = store.get(`voice.${engine}`, engine === "kokoro" ? "af_heart" : "");
  $("s-voice").replaceChildren(...list.map((v) => { const o = document.createElement("option"); o.value = v.id; o.textContent = v.label; o.selected = v.id === chosen; return o; }));
  if (!list.length) { const o = document.createElement("option"); o.textContent = "the device's default voice"; $("s-voice").append(o); }
  fillSources();
  $("s-kokoro-note").textContent = engine === "kokoro"
    ? (KokoroVoice.tts ? "Kokoro is loaded. It runs on this device; nothing is sent anywhere." : "The model is fetched from Hugging Face once and kept by the browser.")
    : "The voices your device has. Instant, and fine for prose; Kokoro reads code and names more evenly.";
}

function fillSources() {
  const sources = store.get("sources", []);
  $("s-sources").replaceChildren(...sources.map((src, i) => {
    const row = document.createElement("div"); row.className = "kv source";
    const b = document.createElement("b"); b.textContent = `${src.repo} · ${src.path}`;
    const x = document.createElement("button"); x.className = "icon"; x.setAttribute("aria-label", "Remove"); x.textContent = "×";
    x.onclick = () => { sources.splice(i, 1); store.set("sources", sources); fillSources(); if (library) library.docs = []; };
    row.append(b, x);
    return row;
  }));
  if (!sources.length) $("s-sources").innerHTML = '<p class="note">None yet. A README with a "## Listen in this order" section, in a repository voce can reach.</p>';
  if (auth && !auth.manual && !$("s-repos").children.length) {
    reachable(auth).then((names) => $("s-repos").replaceChildren(...names.map((n) => { const o = document.createElement("option"); o.value = n; return o; }))).catch(() => {});
  }
}

function addSource() {
  const repo = $("s-src-repo").value.trim().replace(/^https:\/\/github\.com\//, "").replace(/\.git$/, "");
  const path = $("s-src-path").value.trim().replace(/^\/+/, "");
  if (!/^[\w.-]+\/[\w.-]+$/.test(repo) || !path) { $("s-src-note").textContent = "Give the repository as owner/name and the README's path in it."; return; }
  const sources = store.get("sources", []);
  if (!sources.some((s) => s.repo === repo && s.path === path)) sources.push({ repo, path });
  store.set("sources", sources);
  $("s-src-path").value = ""; $("s-src-note").textContent = "";
  fillSources();
  if (library) library.docs = [];
}

function wire() {
  if (!GITHUB_APP.client) { $("signin-row").classList.add("hidden"); $("token-form").open = true; $("token-form").querySelector("summary").classList.add("hidden"); }
  $("signin-go").onclick = () => signIn();
  $("install-go").onclick = () => signIn(true);
  $("connect-go").onclick = async () => {
    const name = $("repo").value.trim().replace(/^https:\/\/github\.com\//, "").replace(/\.git$/, "");
    const token = $("token").value.trim();
    $("connect-error").classList.add("hidden");
    if (!/^[\w.-]+\/[\w.-]+$/.test(name) || !token) { fail("Give the repository as owner/name and the token."); return; }
    $("connect-go").disabled = true; $("connect-status").textContent = "Checking…";
    try { await connect(name, Auth.manual(token)); location.hash = "#/"; await route(); }
    catch (e) { fail(e.message); }
    finally { $("connect-go").disabled = false; $("connect-status").textContent = ""; }
  };
  $("refresh").onclick = async () => { if (reader) reader.stop(); if (library) { library.docs = []; await caches.delete("voce-blobs").catch(() => {}); } await route(); };
  $("settings").onclick = () => { $("s-repo").textContent = repo ? repo.name : "not connected"; $("s-change").classList.toggle("hidden", !auth || auth.manual); fillVoices(); $("sheet").classList.remove("hidden"); };
  $("s-close").onclick = () => $("sheet").classList.add("hidden");
  $("sheet").onclick = (e) => { if (e.target === $("sheet")) $("sheet").classList.add("hidden"); };
  $("s-src-add").onclick = addSource;
  $("s-src-path").onkeydown = (e) => { if (e.key === "Enter") addSource(); };
  $("file").onchange = () => { openFile($("file").files[0]); $("file").value = ""; };
  $("s-engine").onchange = () => { store.set("engine", $("s-engine").value); swapVoice(); fillVoices(); };
  $("s-voice").onchange = () => { store.set(`voice.${store.get("engine", "browser")}`, $("s-voice").value); swapVoice(); };
  $("s-change").onclick = async () => { if (reader) reader.stop(); repo = library = reader = null; $("sheet").classList.add("hidden"); location.hash = "#/"; await pickRepo(); };
  $("s-disconnect").onclick = () => { if (reader) reader.stop(); ["repo", "token", "auth", "signin"].forEach(store.del); auth = repo = library = reader = null; $("sheet").classList.add("hidden"); location.hash = "#/"; route(); };
  $("play").onclick = () => { if (!reader) return; reader.playing ? reader.pause() : reader.play(); };
  $("prev").onclick = () => reader && reader.go(reader.pos - 1);
  $("next").onclick = () => reader && reader.go(reader.pos + 1);
  $("speed").onclick = () => { if (!reader) return; const steps = [0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]; reader.setSpeed(steps[(steps.findIndex((s) => s >= reader.speed - 0.01) + 1) % steps.length]); };
  $("article").onclick = (e) => { const el = e.target.closest("[data-unit]"); if (el && reader) reader.go(+el.dataset.unit); };
  document.addEventListener("keydown", (e) => {
    if (!reader || $("reader").classList.contains("hidden") || e.target.tagName === "INPUT") return;
    if (e.key === " ") { e.preventDefault(); $("play").click(); }
    else if (e.key === "ArrowLeft") reader.go(reader.pos - 1);
    else if (e.key === "ArrowRight") reader.go(reader.pos + 1);
    else if (e.key === "+" || e.key === "=") $("speed").click();
  });
  if ("mediaSession" in navigator) {
    navigator.mediaSession.setActionHandler("play", () => reader && reader.play());
    navigator.mediaSession.setActionHandler("pause", () => reader && reader.pause());
    navigator.mediaSession.setActionHandler("nexttrack", () => reader && reader.go(reader.pos + 1));
    navigator.mediaSession.setActionHandler("previoustrack", () => reader && reader.go(reader.pos - 1));
  }
  addEventListener("hashchange", route);
  addEventListener("pagehide", () => reader && reader.doc && reader.save());
  document.addEventListener("visibilitychange", () => { if (document.hidden && reader && reader.doc) reader.save(); });
  if ("serviceWorker" in navigator && location.protocol === "https:") navigator.serviceWorker.register("sw.js").catch(() => {});
}

function swapVoice() {
  if (!reader) return;
  const wasPlaying = reader.playing;
  reader.stopVoice();
  reader.playing = false;
  voice = reader.voice = makeVoice();
  if (wasPlaying) reader.play();
}

(async () => {
  wire();
  try { if (await finishSignIn()) return pickRepo(); }
  catch (e) { connectView("signin"); fail(e.message); return; }
  auth = Auth.saved();
  const name = store.get("repo");
  if (auth && name) {
    try { await connect(name, auth); }
    catch (e) {
      if (!auth.manual && /can't see|signed this device out/.test(e.message)) {
        if (/signed this device out/.test(e.message)) { auth = null; connectView("signin"); fail(e.message); return; }
        return pickRepo();
      }
      show("connect"); $("repo").value = name; fail(e.message); return;
    }
  } else if (auth && !auth.manual) {
    return pickRepo();
  }
  await route();
})();

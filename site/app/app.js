/* voce on any device: the library and places from your own git repository, played by a voice in the page.

   The Mac did the reading work (prepared/<hash>.json holds the blocks to show and the units to say); this page
   fetches those through the GitHub API, plays them, and writes your place back as places/<hash>.json. You sign in
   with GitHub: the voce GitHub App, installed on the one repository, gives this page a token for it, and a relay
   (relay/worker.js, a stateless function) does the code-for-token swap that GitHub won't let a page do. The
   library itself never leaves GitHub and this device. A fine-grained token pasted by hand works the same way.

   The library repository holds what the person chose, as plain files: its README's "## Listen in this order" is
   a playlist, items/<id>.json is anything added from any device (a web page, a file, shared text, another
   repository's playlist), texts/<hash>.md the Markdown of the ones with no other home, places/<hash>.json the
   place in each.

   The page also carries voce's own reading code (py.js: Python in the browser), so it can read a playlist straight
   from a repository, or a file or web page from this device, with nothing prepared on a Mac first. Without
   signing in, it works on this device alone: what was opened and the places in it stay in this browser. */

const API = "https://api.github.com";
// The GitHub App and its relay. With no client ID, the connect screen offers only the token form.
const GITHUB_APP = { client: "Iv23liKDXAS67GVEUEA6", slug: "voce-reader", relay: "https://voce-relay.jay73x.workers.dev" };
// A new library starts as a private copy of this template: a README playlist of examples, and notes for a coding agent.
const TEMPLATE = { owner: "jaystewartuk", name: "voce-library-template" };
const KOKORO_URL = "https://cdn.jsdelivr.net/npm/kokoro-js@1.2.1/+esm";
const KOKORO_MODEL = "onnx-community/Kokoro-82M-v1.0-ONNX-timestamped"; // the same model, also saying how long each sound lasts
const READABILITY_URL = "https://cdn.jsdelivr.net/npm/@mozilla/readability@0.5.0/+esm"; // finds the article in a web page
const TURNDOWN_URL = "https://cdn.jsdelivr.net/npm/turndown@7.2.0/+esm";                 // and turns it into Markdown
const LOCAL_KEEP = 30;    // documents opened on this device that are kept, newest first
const AHEAD = 3;          // units generated ahead of the one playing
const SAVE_EVERY = 120e3; // ms between saves while playing
const RESUME_WITHIN = 30e3; // ms a pause can last and still pick up mid-sentence; longer, and the sentence starts again
const REWIND = 1.2;         // seconds of listening replayed on picking up, so the cut-off word is heard whole
// iPhone and iPad, including an iPad that says it is a Mac.
const IOS = /iP(hone|ad|od)/.test(navigator.userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
// A tenth of a second of silence, as a WAV: played on a tap so that iOS lets the voice's audio play later.
const SILENCE = (() => {
  const rate = 8000, n = rate / 10, b = new DataView(new ArrayBuffer(44 + n));
  const text = (at, t) => [...t].forEach((c, i) => b.setUint8(at + i, c.charCodeAt(0)));
  text(0, "RIFF"); b.setUint32(4, 36 + n, true); text(8, "WAVEfmt "); b.setUint32(16, 16, true); b.setUint16(20, 1, true);
  b.setUint16(22, 1, true); b.setUint32(24, rate, true); b.setUint32(28, rate, true); b.setUint16(32, 1, true);
  b.setUint16(34, 8, true); text(36, "data"); b.setUint32(40, n, true);
  for (let i = 0; i < n; i++) b.setUint8(44 + i, 128);
  return URL.createObjectURL(new Blob([b], { type: "audio/wav" }));
})();
const SPACE = 16;           // Kokoro's token for the gap between words; the ones below it are punctuation
const WORD = /[\p{L}\p{N}]+(?:['’]\p{L}+)*/gu;
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
  if (!GITHUB_APP.relay) throw new Error("The relay isn't set up on this copy of the app.");
  let r;
  try { r = await fetch(`${GITHUB_APP.relay}/${step}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); }
  catch { throw new Error("Couldn't reach voce's relay. Check the connection and try again."); }
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
    headers: { ...(auth ? { Authorization: `Bearer ${await auth.bearer()}` } : {}), Accept: "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", ...(init.headers || {}) },
  });
  if (!r.ok && r.status !== 404 && r.status !== 409) {
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
  /** open: another repository's playlist, which may be public without voce having been given access to it. */
  constructor(name, auth, open = false) { this.name = name; this.auth = auth; this.open = open; this.trees = {}; }

  /** A public repository voce can't see with the sign-in is asked again without it, as anyone may. */
  async api(path, init) {
    const r = await gh(this.auth, path, init);
    return r.status === 404 && this.open ? gh(null, path, init) : r;
  }

  async check() {
    const r = await this.api(`/repos/${this.name}`);
    if (r.status === 404) throw new Error(this.auth.manual ? "No such repository, or the token can't see it."
                                                           : "voce can't see that repository any more. Choose another, or give voce access to it on GitHub.");
  }

  /** {path: sha} for the files in a folder, in one request; with deep, every file under it. */
  async tree(folder, deep = false) {
    const r = await this.api(`/repos/${this.name}/git/trees/${folder ? "HEAD:" + encodeURI(folder) : "HEAD"}${deep ? "?recursive=1" : ""}`);
    if (r.status === 404 || r.status === 409) return {}; // no such folder, or a repository with nothing in it yet
    const d = await r.json();
    return Object.fromEntries(d.tree.filter((e) => e.type === "blob").map((e) => [e.path, e.sha]));
  }

  /** A file's sha and text as they are now; the browser may keep API answers for a minute, so not from its cache. */
  async file(path) {
    const r = await this.api(`/repos/${this.name}/contents/${path}`, { cache: "no-store" });
    if (r.status === 404) return null;
    const d = await r.json();
    return { sha: d.sha, text: decodeURIComponent(escape(atob(d.content.replace(/\n/g, "")))) };
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
    if (!r.ok) throw new Error(`Couldn't save to your library: GitHub said ${r.status}.`);
    return (await r.json()).content.sha;
  }

  /** Remove a file; sha is the version being removed. */
  async remove(path, sha, message) {
    const r = await this.api(`/repos/${this.name}/contents/${path}`, { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message, sha }) });
    if (!r.ok && r.status !== 404) throw new Error(`Couldn't remove it: GitHub said ${r.status}.`);
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

// ---------------------------------------------------------------- web pages

/** A web page's article as Markdown: Readability finds it, without the menus and footers, and Turndown writes it
    in the Markdown voce reads. Pictures and players have nothing to say, so they go. */
async function pageToMarkdown(html, url) {
  const [{ Readability }, { default: Turndown }] = await Promise.all([import(READABILITY_URL), import(TURNDOWN_URL)]);
  const dom = new DOMParser().parseFromString(html, "text/html");
  if (url) { const base = dom.createElement("base"); base.href = url; dom.head.prepend(base); }
  const article = new Readability(dom).parse();
  if (!article || !article.content) throw new Error("there's no article on that page to read");
  const td = new Turndown({ headingStyle: "atx", codeBlockStyle: "fenced", bulletListMarker: "-", emDelimiter: "*" });
  td.remove(["img", "picture", "svg", "video", "audio", "iframe", "button", "form"]);
  const md = td.turndown(article.content).trim();
  return /^# /.test(md) || !article.title ? md : `# ${article.title.trim()}\n\n${md}`;
}

/** A page's text and type. Straight from the site where it allows that; otherwise through the relay, which
    fetches it and hands it back, keeping nothing, because most sites won't let another site's page read them. */
async function fetchPage(address) {
  let r = null;
  try { r = await fetch(address, { headers: { Accept: "text/markdown, text/html;q=0.9, text/plain;q=0.8" } }); }
  catch { /* the site doesn't let other pages read it */ }
  if (!r) return relay("page", { url: address });
  if (!r.ok) throw new Error(`that page answered ${r.status}`);
  return { url: r.url || address, type: r.headers.get("Content-Type") || "", text: await r.text() };
}

/** What was typed or shared, as a web address: https:// is added when it's left off. Null when it isn't one. */
function address(text) {
  const s = (text || "").trim();
  const found = /https?:\/\/\S+/.exec(s);
  if (found) return found[0];
  return /^[\w-]+(\.[\w-]+)+(\/\S*)?$/.test(s) ? `https://${s}` : null;
}

// ---------------------------------------------------------------- the library and places

/** The documents to listen to: the library's own README playlist and the playlists added to it, then what was
    added from any device, then the Mac's prepared copies. Each is named by the hash of its text, which is what names
    its place too. With no repository, it is this device's alone: what was opened and the places in it are kept in
    this browser, and carried into the repository on signing in. */
class Library {
  constructor(repo, auth) {
    this.repo = repo; this.auth = auth;
    this.docs = []; this.places = {}; this.placeShas = {}; this.local = {}; this.notes = []; this.prepared = {};
    this.items = {}; this.itemShas = {}; this.texts = {};
  }

  /** The playlists added to the library, as {id, repo, path}. */
  get sources() {
    return Object.entries(this.items).filter(([, it]) => it.kind === "playlist").map(([id, it]) => ({ id, repo: it.repo, path: it.path }));
  }

  async load() {
    if (!this.repo) {
      this.places = store.get("places", {});
      this.docs = store.get("local", []).map((d) => ({ ...d, part: "On this device" }));
      this.notes = [];
      return;
    }
    const read = async (tree) => Object.fromEntries((await Promise.all(Object.entries(tree)
      .filter(([name]) => name.endsWith(".json"))
      .map(async ([name, sha]) => { try { return [name.slice(0, -5), JSON.parse(await this.repo.blob(sha))]; } catch { return null; } })))
      .filter(Boolean));
    const [prepared, places, items, texts] = await Promise.all(["prepared", "places", "items", "texts"].map((f) => this.repo.tree(f)));
    this.prepared = prepared; this.placeShas = places; this.itemShas = items; this.texts = texts;
    const index = prepared["index.json"] ? JSON.parse(await this.repo.blob(prepared["index.json"])) : { documents: [] };
    [this.places, this.items] = await Promise.all([read(places), read(items)]);
    for (const k of Object.keys(this.places)) if (!/^[0-9a-f]{64}$/.test(k)) delete this.places[k];
    await this.carry();
    const docs = [], seen = new Set(), notes = [];
    const add = (d) => { if (!seen.has(d.hash)) { seen.add(d.hash); docs.push(d); } };
    try { (await this.fromSource({ repo: this.repo.name, path: "README.md" })).forEach(add); }
    catch { /* a library made by voce --sync has no playlist of its own */ }
    for (const source of this.sources) {
      try { (await this.fromSource(source)).forEach(add); }
      catch (e) { notes.push(`Couldn't read the playlist ${source.path} in ${source.repo}: ${e.message}.`); }
    }
    Object.entries(this.items).filter(([hash, it]) => it.kind !== "playlist" && this.texts[`${hash}.md`])
      .sort(([, a], [, b]) => (b.added || "").localeCompare(a.added || ""))
      .forEach(([hash, it]) => add({ hash, title: it.title, part: "Added", minutes: it.minutes, sha: this.texts[`${hash}.md`],
                                     name: `${hash}.md`, source: { repo: this.repo.name } }));
    const fresh = new Set(docs.map((d) => d.name));              // a Mac copy of a playlist file is its past: skip it
    index.documents.filter((d) => prepared[`${d.hash}.json`] && !fresh.has(d.file)).forEach(add);
    store.get("local", []).forEach((d) => add({ ...d, part: "On this device" }));
    this.docs = docs;
    this.notes = notes;
  }

  /** What was read on this device before signing in, and playlists added before they were kept in the library:
      put into the repository, places too, so nothing is lost by signing in. */
  async carry() {
    const cache = await caches.open("voce-local").catch(() => null);
    const left = [];
    for (const d of store.get("local", [])) {
      const hit = cache && await cache.match(`${API}/local-text/${d.hash}`);
      if (!hit) { left.push(d); continue; } // opened before the text was kept: it stays on this device
      try {
        const { text, from } = await hit.json();
        await this.keep(d.hash, text, { kind: "file", ...from, title: d.title, minutes: d.minutes, added: d.added || now() });
        const place = store.get("places", {})[d.hash];
        if (place && !this.placeShas[`${d.hash}.json`]) {
          const sha = await this.repo.put(`places/${d.hash}.json`, JSON.stringify(place, null, 1), undefined, `web: ${d.title.slice(0, 60)}`);
          if (sha) { this.placeShas[`${d.hash}.json`] = sha; this.places[d.hash] = place; }
        }
      } catch { left.push(d); }
    }
    store.set("local", left);
    for (const s of store.get("sources", [])) await this.addSource(s.repo, s.path).catch(() => {});
    store.del("sources");
  }

  /** Put a text and its entry in the library: texts/<hash>.md, then items/<hash>.json. */
  async keep(hash, text, item) {
    const message = `web: ${item.title.slice(0, 60)}`;
    if (!this.texts[`${hash}.md`]) {
      const sha = await this.repo.put(`texts/${hash}.md`, text, undefined, message);
      this.texts[`${hash}.md`] = sha || (await this.repo.file(`texts/${hash}.md`))?.sha; // null: another device put it there first
    }
    if (!this.itemShas[`${hash}.json`]) {
      const sha = await this.repo.put(`items/${hash}.json`, JSON.stringify(item, null, 1), undefined, message);
      if (sha) this.itemShas[`${hash}.json`] = sha;
    }
    this.items[hash] = item;
  }

  /** Add another repository's README playlist to the library. */
  async addSource(repo, path) {
    if (this.sources.some((s) => s.repo === repo && s.path === path)) return;
    const id = (await sha256(`playlist ${repo} ${path}`)).slice(0, 16);
    const item = { kind: "playlist", repo, path, added: now() };
    const sha = await this.repo.put(`items/${id}.json`, JSON.stringify(item, null, 1), this.itemShas[`${id}.json`], `web: playlist ${repo} ${path}`);
    if (sha) this.itemShas[`${id}.json`] = sha;
    this.items[id] = item;
    this.docs = [];
  }

  /** A playlist whose README moved into a folder of its repository: follow it there, and keep the new path. */
  async follow(source, repo) {
    const all = await repo.tree("", true);
    const hits = Object.keys(all).filter((p) => p.endsWith(`/${source.path}`));
    if (hits.length !== 1) return null;
    const item = { ...this.items[source.id], path: hits[0] };
    const sha = await this.repo.put(`items/${source.id}.json`, JSON.stringify(item, null, 1), this.itemShas[`${source.id}.json`], `web: playlist ${source.repo} moved to ${hits[0]}`);
    if (sha) this.itemShas[`${source.id}.json`] = sha;
    this.items[source.id] = item;
    return { ...source, path: hits[0] };
  }

  async removeSource(id) {
    await this.repo.remove(`items/${id}.json`, this.itemShas[`${id}.json`], `web: remove playlist ${this.items[id]?.repo || ""}`);
    delete this.items[id]; delete this.itemShas[`${id}.json`];
    this.docs = [];
  }

  /** The documents of one playlist README in a repository, each with the sha of its text and the hash of it. */
  async fromSource(source) {
    const repo = new Repo(source.repo, this.auth, true);
    const dir = source.path.includes("/") ? source.path.slice(0, source.path.lastIndexOf("/")) : "";
    const tree = await repo.tree(dir, true);                       // paths under the README's folder
    const readme = tree[dir ? source.path.slice(dir.length + 1) : source.path];
    if (!readme) {
      const moved = source.id && await this.follow(source, repo);
      if (moved) return this.fromSource(moved);
      throw new Error("it isn't there any more. If it moved, remove it in Settings and add it from where it is now");
    }
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
    const kept = await caches.open("voce-local").then((c) => c.match(`${API}/local/${hash}`)).catch(() => null);
    if (kept) return (this.local[hash] = await kept.json());
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
    const text = await new Repo(d.source.repo, this.auth, true).blob(d.sha);
    const out = await py.prepare(text, d.name);
    if (cache) cache.put(key, new Response(JSON.stringify(out))).catch(() => {});
    return out;
  }

  /** A file, page or shared text, read now. Signed in, it goes into the library, listed under "Added" on every
      device; otherwise it is kept in this browser under "On this device", the newest LOCAL_KEEP of them. `from`
      says where it came from: {kind: "page", url}, {kind: "file"} or {kind: "text"}. */
  async open(text, name, from = { kind: "file" }) {
    const out = await py.prepare(text, name);
    this.local[out.hash] = out;
    const cache = await caches.open("voce-local").catch(() => null);
    if (cache) await cache.put(`${API}/local/${out.hash}`, new Response(JSON.stringify(out))).catch(() => {});
    if (this.repo) {
      try {
        await this.keep(out.hash, text, { ...from, title: out.title, minutes: out.minutes, added: now() });
        if (!this.docs.some((d) => d.hash === out.hash)) {
          this.docs.push({ hash: out.hash, title: out.title, part: "Added", minutes: out.minutes, sha: this.texts[`${out.hash}.md`],
                           name: `${out.hash}.md`, source: { repo: this.repo.name } });
        }
        return out.hash;
      } catch { /* GitHub turned it away: keep it on this device, and it is carried into the library next time */ }
    }
    if (cache) await cache.put(`${API}/local-text/${out.hash}`, new Response(JSON.stringify({ text, from }))).catch(() => {});
    const kept = [{ hash: out.hash, title: out.title, minutes: out.minutes, added: now() }, ...store.get("local", []).filter((d) => d.hash !== out.hash)];
    kept.slice(LOCAL_KEEP).forEach((d) => cache && [`local/${d.hash}`, `local-text/${d.hash}`].forEach((k) => cache.delete(`${API}/${k}`).catch(() => {})));
    store.set("local", kept.slice(0, LOCAL_KEEP));
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

  /** Save a place, keeping the newer one when another device wrote meanwhile. One save at a time: two at once
      would both replace the same version, and GitHub turns the second away. */
  save(hash, title, fields) {
    const write = () => this.write(hash, title, fields);
    this.saving = (this.saving || Promise.resolve()).then(write, write);
    return this.saving;
  }

  async write(hash, title, fields) {
    const current = this.places[hash] || {};
    const place = { ...current, ...fields, updated: now(), paths: { ...(current.paths || {}), [HOST]: title } };
    this.places[hash] = place;
    if (!this.repo) { store.set("places", { ...store.get("places", {}), [hash]: place }); return place; }
    for (let attempt = 0; attempt < 3; attempt++) {
      const sha = await this.repo.put(`places/${hash}.json`, JSON.stringify(place, null, 1), this.placeShas[`${hash}.json`],
                                      `web: ${title.slice(0, 60)}`);
      if (sha) { this.placeShas[`${hash}.json`] = sha; return place; }
      const file = await this.repo.file(`places/${hash}.json`);
      this.placeShas[`${hash}.json`] = file?.sha;
      if (file) {
        const theirs = JSON.parse(file.text);
        if ((theirs.updated || "") > place.updated) { this.places[hash] = theirs; return theirs; }
      }
    }
    throw new Error("Couldn't save your place after three tries.");
  }
}

// ---------------------------------------------------------------- voices

// The commonest small words of each language a document is told apart by. Add a language by adding its words.
const LANGUAGE_WORDS = {
  en: ["the", "and", "of", "to", "is", "that", "it", "for", "you", "with", "this", "are"],
  es: ["el", "la", "los", "las", "que", "de", "y", "en", "es", "por", "una", "con", "para", "del"],
};

/** The language a document is written in, by how often its commonest words come up: "en", "es", or "" when it
    can't tell, as with a page that is mostly code. */
function guessLanguage(units) {
  const words = units.map((u) => u.say).join(" ").slice(0, 4000).toLowerCase().match(/\p{L}+/gu) || [];
  const counts = Object.entries(LANGUAGE_WORDS).map(([lang, list]) => [lang, words.filter((w) => list.includes(w)).length]);
  const [best, next] = counts.sort((a, b) => b[1] - a[1]);
  return best[1] >= 5 && best[1] > 2 * next[1] ? best[0] : "";
}

/** How good a device voice sounds, from how the device names it: 3 premium, 2 enhanced (the voices an iPhone or a
    Mac downloads), 1 the rest, 0 the Eloquence and novelty voices (Eddy, Grandma, Bubbles), robotic on purpose. */
function quality(v) {
  const id = `${v.voiceURI} ${v.name}`;
  return /premium/i.test(id) ? 3 : /enhanced|mejorad/i.test(id) ? 2 : /eloquence|speech\.synthesis\.voice/i.test(id) ? 0 : 1;
}

class BrowserVoice {
  constructor(name) { this.name = name; this.kind = "browser"; this.utterance = null; this.lang = ""; }
  /** Every voice on the device, those in the device's own languages first, then English; the best first in each. */
  static voices() {
    const mine = navigator.languages.map((l) => l.slice(0, 2));
    const rank = (v) => { const i = mine.indexOf(v.lang.slice(0, 2)); return i >= 0 ? i : v.lang.startsWith("en") ? mine.length : mine.length + 1; };
    const tag = ["", "", " · enhanced", " · premium"];
    return [...speechSynthesis.getVoices()].sort((a, b) => rank(a) - rank(b) || quality(b) - quality(a))
      .map((v) => ({ id: v.voiceURI, label: `${v.name} (${v.lang})${tag[quality(v)]}` }));
  }
  /** The language of the document being read, as "es", or "" when it isn't known. */
  setLanguage(lang) { this.lang = lang; }
  /** The voice chosen in settings, unless the document is in another language. Then the best-sounding voice the
      device has for it, preferring the device's country (es-MX on a phone set to Mexico), then its default. */
  pick() {
    const all = speechSynthesis.getVoices(), chosen = all.find((v) => v.voiceURI === this.name);
    if (!this.lang || (chosen && chosen.lang.startsWith(this.lang))) return chosen;
    const regions = navigator.languages.map((l) => l.split("-")[1]).filter(Boolean);
    const score = (v) => quality(v) * 4 + (regions.includes(v.lang.split(/[-_]/)[1]) ? 2 : 0) + (v.default ? 1 : 0);
    return all.filter((v) => v.lang.startsWith(this.lang)).sort((a, b) => score(b) - score(a))[0] || chosen;
  }
  async ready() { if (!speechSynthesis.getVoices().length) await new Promise((r) => { speechSynthesis.onvoiceschanged = r; setTimeout(r, 500); }); }
  prefetch() {}
  speak(text, speed, onEnd, onError) {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const voice = this.pick();
    if (voice) u.voice = voice;
    if (this.lang) u.lang = voice ? voice.lang : this.lang;
    u.rate = speed;
    u.onend = () => { if (this.utterance === u) onEnd(); };
    u.onerror = (e) => { if (this.utterance === u && e.error !== "interrupted" && e.error !== "canceled") onError(e.error); };
    u.onboundary = (e) => { if (this.utterance === u && e.name === "word") this.at = e.charIndex; };
    this.utterance = u; this.at = -1;
    speechSynthesis.speak(u);
  }
  pause() { this.stop(); } // speechSynthesis.pause() is unreliable on iOS, so a paused sentence starts again
  resume() { return false; }
  /** Where in the sentence the voice is: the offset of the word being said, where the device reports it, or -1. */
  spokenAt() { return this.utterance ? this.at : -1; }
  stop() { this.utterance = null; speechSynthesis.cancel(); }
  setSpeed() {} // takes effect from the next sentence
}

class KokoroVoice {
  constructor(name, onProgress) {
    this.name = name || "af_heart"; this.kind = "kokoro"; this.onProgress = onProgress;
    this.audio = new Audio(); this.audio.preload = "auto";
    this.clips = new Map(); this.made = new Set(); this.generating = Promise.resolve();
  }
  static async load(onProgress) {
    if (KokoroVoice.tts) return KokoroVoice.tts;
    if (!KokoroVoice.loading) {
      KokoroVoice.loading = (async () => {
        const { KokoroTTS } = await import(KOKORO_URL);
        // Safari on iPhone and iPad has WebGPU from iOS 26, but the full model it needs (326 MB) is more than a
        // phone gives a web page; the smaller one (92 MB) runs on the CPU.
        const webgpu = !!navigator.gpu && !IOS;
        KokoroVoice.tts = await KokoroTTS.from_pretrained(KOKORO_MODEL, {
          dtype: webgpu ? "fp32" : "q8", device: webgpu ? "webgpu" : "wasm",
          // the model's download, and then, once it is all here, that the voice is starting from it; the small
          // files around it finish first, and would say it was starting before the download had begun
          progress_callback: (p) => { if (p.status === "progress" && /\.onnx$/.test(p.file || "") && onProgress) onProgress(p.progress || 0, p.file); },
        });
        // kokoro-js keeps only the audio; keep the sounds and how long each lasts as well, for marking words.
        const model = KokoroVoice.tts.model;
        KokoroVoice.tts.model = async (inputs) => {
          const out = await model(inputs);
          KokoroVoice.run = { ids: Array.from(inputs.input_ids.data, Number), durations: out.durations ? Array.from(out.durations.data, Number) : null };
          return out;
        };
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
  async ready() {
    // fetching kokoro-js and its small files takes a few seconds before the model's download says anything
    if (!KokoroVoice.tts && this.onProgress) this.onProgress(null);
    await KokoroVoice.load(this.onProgress);
  }
  /** iOS plays a page's audio only if it starts during a tap, and the first sentence comes seconds later, once the
      model has loaded and spoken it. So on the tap, play a moment of silence: the same element may play after. */
  unlock() {
    if (this.unlocked) return;
    this.unlocked = true;
    const audio = this.audio;
    audio.src = SILENCE;
    audio.play().then(() => { if (audio.src === SILENCE) audio.pause(); }).catch(() => { this.unlocked = false; });
  }
  /** Whether a sentence's audio is made and waiting, so it plays straight away. */
  isReady(text) { return this.made.has(text); }
  /** A WAV for a sentence, where it goes quiet and when each word starts, generated once; generation is serialised so the model is never asked twice at once. */
  clip(text) {
    if (!this.clips.has(text)) {
      const job = this.generating.then(async () => {
        KokoroVoice.run = null;
        const audio = await KokoroVoice.tts.generate(text, { voice: this.name });
        this.made.add(text);
        return {
          url: URL.createObjectURL(audio.toBlob()), quiet: quietTimes(audio.audio, audio.sampling_rate),
          words: wordTimes(text, KokoroVoice.run, audio.audio.length / audio.sampling_rate),
        };
      });
      this.generating = job.catch(() => {});
      this.clips.set(text, job);
      if (this.clips.size > 40) { const old = this.clips.keys().next().value; this.clips.delete(old); this.made.delete(old); }
    }
    return this.clips.get(text);
  }
  prefetch(texts) { texts.forEach((t) => this.clip(t).catch(() => {})); }
  async speak(text, speed, onEnd, onError, onStart) {
    const token = this.token = {};
    let clip;
    try { clip = await this.clip(text); } catch (e) { if (this.token === token) onError(e.message); return; }
    if (this.token !== token) return;
    this.current = { clip, onError };
    this.audio.src = clip.url;
    this.audio.playbackRate = speed;
    this.audio.onended = () => { if (this.token === token) onEnd(); };
    this.audio.onerror = () => { if (this.token === token) onError("the clip wouldn't play"); };
    try { await this.audio.play(); } catch (e) { if (this.token === token) onError(e.message); return; }
    if (this.token === token && onStart) onStart();
  }
  pause() { this.audio.pause(); }
  /** Pick the paused clip up `back` seconds of listening earlier, at the gap before a word. False when there's nothing left to pick up. */
  resume(back) {
    const { current, audio } = this;
    if (!current || !audio.src || audio.ended) return false;
    const target = Math.max(0, audio.currentTime - back * audio.playbackRate);
    const { words, quiet } = current.clip;
    const start = words ? words.map((w) => w.t - 0.05).findLast((t) => t <= target) : quiet.findLast((t) => t <= target && t > target - 0.8);
    audio.currentTime = Math.max(0, start ?? target);
    const token = this.token;
    audio.play().catch((e) => { if (this.token === token) current.onError(e.message); });
    return true;
  }
  /** Where in the sentence the voice is: the offset of the word being said, or -1. */
  spokenAt() {
    const words = this.current && this.current.clip.words;
    if (!words) return -1;
    let at = -1;
    for (const w of words) { if (w.t > this.audio.currentTime) break; at = w.at; }
    return at;
  }
  stop() { this.token = {}; this.current = null; this.audio.pause(); this.audio.removeAttribute("src"); }
  setSpeed(speed) { this.audio.playbackRate = speed; }
}

/** The times, in seconds, of the clip's 20 ms frames that are near silent: the gaps between words. */
function quietTimes(samples, rate) {
  const frame = Math.round(rate * 0.02), levels = [];
  for (let i = 0; i + frame <= samples.length; i += frame) {
    let sum = 0;
    for (let j = i; j < i + frame; j++) sum += samples[j] * samples[j];
    levels.push(Math.sqrt(sum / frame));
  }
  const loudest = levels.reduce((a, b) => Math.max(a, b), 1e-6);
  return levels.flatMap((level, k) => (level < loudest * 0.05 ? [k * 0.02] : []));
}

/** When each word of `text` starts, in seconds, from how long the model made each sound: [{ at, t }], `at` being
    the word's offset in `text`. Words follow the gaps in the sounds; where the two counts differ (a number said
    as several words), they are shared out evenly. */
function wordTimes(text, run, seconds) {
  if (!run || !run.durations || run.durations.length !== run.ids.length) return null;
  const total = run.durations.reduce((a, b) => a + b, 0);
  const starts = [];
  let t = 0, inWord = false;
  run.ids.forEach((id, k) => {
    if (id === SPACE) inWord = false;
    else if (id > SPACE && !inWord) { starts.push(t); inWord = true; }
    t += run.durations[k];
  });
  const words = [...text.matchAll(/\S*[\p{L}\p{N}]\S*/gu)];
  if (!total || !starts.length || !words.length) return null;
  return words.map((m, k) => ({ at: m.index, t: starts[Math.floor(k * starts.length / words.length)] * seconds / total }));
}

// ---------------------------------------------------------------- the reader

class Reader {
  constructor(library, voice, ui) {
    this.library = library; this.chosen = this.voice = voice; this.ui = ui;
    this.doc = null; this.hash = ""; this.pos = 0; this.playing = false; this.timer = null; this.lastSave = 0;
    this.pausedAt = 0; this.heard = false; // when play was paused, and whether the sentence had already finished
    this.speed = store.get("speed", 1.0);
  }

  async open(hash) {
    this.stop();
    this.hash = hash;
    this.doc = await this.library.doc(hash);
    this.units = this.doc.units;
    this.language = guessLanguage(this.units);
    this.useVoiceFor(this.language);
    this.measure();
    this.pos = this.resume();
    this.ui.render(this.doc, this.units);
    this.show();
  }

  /** The voice for a document in this language: the one chosen, except that Kokoro in the page speaks English only,
      so a document known to be in another language is read by the device's voice for it. */
  useVoiceFor(lang) {
    const english = this.chosen.kind !== "kokoro" || !lang || lang === "en";
    this.voice = english ? this.chosen : (this.deviceVoice ||= new BrowserVoice(""));
    if (this.voice.setLanguage) this.voice.setLanguage(lang);
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

  /** For saying where the reader is: the characters left from each unit on, how long one takes to say at 1×
      (from the document's own minutes), and the heading each block sits under. */
  measure() {
    this.left = [];
    let sum = 0;
    for (let i = this.units.length - 1; i >= 0; i--) { sum += this.units[i].say.length; this.left[i] = sum; }
    this.perChar = this.doc.minutes && sum ? this.doc.minutes * 60 / sum : 1 / 15;
    let heading = "";
    this.headings = this.doc.blocks.map((b) => {
      if (/^h[1-6]$/.test(b.kind) && b.text.trim() !== this.doc.title) heading = b.text.trim();
      return heading;
    });
  }

  /** "8 min left · Setup": the time left at this speed, then the heading the sentence is under. */
  where() {
    const mins = Math.round((this.left[this.pos] || 0) * this.perChar / this.speed / 60);
    const left = mins < 1 ? "Under a minute left" : mins < 60 ? `${mins} min left` : `${Math.floor(mins / 60)} h ${mins % 60} min left`;
    const unit = this.units[this.pos];
    const heading = unit && unit.block >= 0 ? this.headings[unit.block] : "";
    return heading ? `${left} · ${heading}` : left;
  }

  show() { this.ui.highlight(this.pos, this.units.length); this.ui.status(this.where()); }

  go(i, play = this.playing) {
    this.pos = Math.max(0, Math.min(i, this.units.length - 1));
    this.show();
    if (play) this.play(); else this.stopVoice();
  }

  /** Play from the current sentence, or, straight after a short pause, from just before where it stopped. */
  async play() {
    if (!this.units.length) return;
    const recent = this.pausedAt && Date.now() - this.pausedAt < RESUME_WITHIN;
    this.pausedAt = 0;
    this.playing = true;
    this.ui.setPlaying(true);
    if (this.voice.unlock) this.voice.unlock(); // before anything is awaited, while the tap still counts
    try { await this.voice.ready(); } catch (e) { this.fail(`The voice couldn't load: ${e.message}`); return; }
    if (recent && this.heard) { this.next(); return; } // paused in the silence after a sentence
    if (recent && this.voice.resume(REWIND)) { this.follow(); return; }
    this.sayCurrent();
  }

  sayCurrent() {
    const unit = this.units[this.pos];
    this.heard = false;
    this.ui.words(this.pos, unit.say);
    const making = this.voice.isReady && !this.voice.isReady(unit.say);
    if (making) this.ui.status(this.voice.made.size ? "Making this sentence…"
      : "Making the first sentence. On a phone that takes a few seconds.");
    this.voice.speak(unit.say, this.speed,
      () => this.after(unit),
      (why) => this.fail(`The voice stopped: ${why}`),
      () => { if (making) this.ui.status(this.where()); });
    // after speak, which asks for this sentence first: the voice makes one sentence at a time, and on a phone each
    // takes seconds, so the sentences after it waiting in front of it kept the first one quiet for a long while
    this.voice.prefetch(this.units.slice(this.pos + 1, this.pos + 1 + AHEAD).map((u) => u.say));
    this.follow();
    if (Date.now() - this.lastSave > SAVE_EVERY) this.save();
  }

  /** Mark the word being said, once a frame while playing. */
  follow() {
    if (this.following) return;
    this.following = true;
    const step = () => {
      if (!this.playing) { this.following = false; return; }
      this.ui.word(this.voice.spokenAt());
      requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  after(unit) {
    if (!this.playing) return;
    this.heard = true;
    const wait = (unit.wait ? 2.5 : unit.pause) * 1000 / this.speed;
    this.timer = setTimeout(() => { if (this.playing) this.next(); }, wait);
  }

  next() {
    if (this.pos + 1 >= this.units.length) { this.finish(); return; }
    this.pos += 1;
    this.show();
    this.sayCurrent();
  }

  /** Hold the sentence where it is, so a play soon after picks it up there; the saved place is still the sentence. */
  pause() {
    this.playing = false;
    clearTimeout(this.timer);
    this.voice.pause();
    this.pausedAt = Date.now();
    this.ui.setPlaying(false);
    this.save();
  }

  stopVoice() { clearTimeout(this.timer); this.pausedAt = 0; this.voice.stop(); }

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
    if (this.doc) this.ui.status(this.where());
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
// Words voce respells so the voice says them right (speech/prose.py), matched to the word as written
const RESPELLED = { moduloh: "modulo", innit: "init", eenum: "enum", eenums: "enums", itterable: "iterable",
  itterables: "iterables", reddis: "redis", eh: "a" };
const wordKey = (w) => { const k = w.toLowerCase().replace(/’/g, "'"); return RESPELLED[k] || k; };

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
  free: false, // scrolled away from the voice: the page stops following it until they come back
  render(doc, units) { renderBlocks(doc, units); $("title").textContent = doc.title; this.free = false; },
  highlight(i, total) {
    this.unmark();
    document.querySelectorAll("[data-unit].now").forEach((el) => el.classList.remove("now"));
    const els = document.querySelectorAll(`[data-unit="${i}"]`);
    els.forEach((el) => el.classList.add("now"));
    if (els[0] && !this.free) { const r = els[0].getBoundingClientRect(); if (r.top < 80 || r.bottom > innerHeight - 160) els[0].scrollIntoView({ block: "center", behavior: "smooth" }); }
    this.progress((i + 1) / Math.max(1, total));
    this.placeBack();
  },
  progress(ratio) {
    $("progress").style.width = `${100 * ratio}%`;
    $("seek").setAttribute("aria-valuenow", Math.round(100 * ratio));
  },
  /** Offer the way back to the sentence being read while it is off screen; once it is in view, follow it again. */
  placeBack() {
    const el = document.querySelector("[data-unit].now");
    const r = el && !$("reader").classList.contains("hidden") ? el.getBoundingClientRect() : null;
    const above = r && r.bottom < 60, below = r && r.top > innerHeight - 120;
    $("back").classList.toggle("hidden", !(above || below));
    $("back").classList.toggle("up", !!above);
    if (r && !above && !below) this.free = false;
  },
  back() {
    this.free = false;
    const el = document.querySelector("[data-unit].now");
    if (el) el.scrollIntoView({ block: "center", behavior: "smooth" });
  },
  /** Line the sentence's spoken words up with the words on screen, so the one being said can be marked. A line
      of code said differently from how it's shown keeps only its line marked. */
  words(i, say) {
    this.said = null;
    if (!("highlights" in CSS) || !store.get("words", true)) return;
    const shown = [];
    document.querySelectorAll(`[data-unit="${i}"]`).forEach((el) => {
      const walk = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      while (walk.nextNode()) {
        const node = walk.currentNode;
        for (const m of node.data.matchAll(WORD)) shown.push({ node, start: m.index, end: m.index + m[0].length, key: wordKey(m[0]) });
      }
    });
    const said = [...say.matchAll(WORD)].map((m) => ({ at: m.index, key: wordKey(m[0]), shown: null }));
    let next = 0, matched = 0;
    said.forEach((w) => {
      for (let k = next; k < Math.min(shown.length, next + 5); k++) {
        if (shown[k].key === w.key) { w.shown = shown[k]; next = k + 1; matched++; break; }
      }
    });
    if (matched >= said.length / 2) this.said = said;
  },
  /** Mark the word on screen for the spoken word at offset `at` in the sentence. */
  word(at) {
    if (!this.said || at < 0) return;
    let target = null;
    for (const w of this.said) { if (w.at > at) break; if (w.shown) target = w.shown; }
    if (!target || target === this.marked) return;
    this.marked = target;
    const range = new Range();
    range.setStart(target.node, target.start);
    range.setEnd(target.node, target.end);
    CSS.highlights.set("word", new Highlight(range));
  },
  unmark() { this.marked = null; if ("highlights" in CSS) CSS.highlights.delete("word"); },
  setPlaying(on) {
    $("play-icon").innerHTML = on ? '<path d="M7 5h4v14H7zM13 5h4v14h-4z"/>' : '<path d="M8 5v14l11-7z"/>';
    $("play").setAttribute("aria-label", on ? "Pause" : "Play");
    $("play-label").textContent = on ? "Pause" : "Play";
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
  if (view !== "reader") $("back").classList.add("hidden");
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
  $("choose-title").textContent = state === "install" ? "Make your library" : state === "busy" ? "Signing in…" : "Which repository?";
  $("choose-lead").textContent = state === "install"
    ? "Two steps on GitHub, a minute in all. Already have a library, made by voce --sync on a Mac? Skip to step 2 and choose it."
    : state === "busy" ? "" : "The repositories voce can reach. Choose your library.";
  $("make").classList.toggle("hidden", state !== "install");
  $("choose-actions").classList.toggle("hidden", state === "install" || state === "busy");
  $("repos").replaceChildren(...repos.map((name) => {
    const b = document.createElement("button"); b.className = "btn quiet repo"; b.textContent = name;
    b.onclick = () => useRepo(name);
    return b;
  }));
  $("install-go").textContent = state === "install" ? "Choose the repository on GitHub" : "Give voce access to another repository";
}

/** GitHub's new-repository page, filled in: a private copy of the starter library, named voce-library. */
function makeUrl() {
  const u = new URL("https://github.com/new");
  Object.entries({ template_owner: TEMPLATE.owner, template_name: TEMPLATE.name, owner: "@me", name: "voce-library",
                   visibility: "private", description: "What I listen to with voce" }).forEach(([k, v]) => u.searchParams.set(k, v));
  return u.href;
}

function fail(message) {
  $("connect-error").textContent = message;
  $("connect-error").classList.remove("hidden");
}

function makeVoice() {
  const engine = store.get("engine", "browser");
  const name = store.get(`voice.${engine}`, engine === "kokoro" ? "af_heart" : "");
  return engine === "kokoro"
    ? new KokoroVoice(name, (p, file) => ui.status(p === null ? "Getting the voice…" : p >= 100
      ? "Starting the voice on this device. It takes a few seconds the first time."
      : `Downloading the voice: ${Math.round(p)}% of ${file || "the model"}`))
    : new BrowserVoice(name);
}

async function connect(name, with_) {
  repo = new Repo(name, with_);
  await repo.check();
  auth = with_;
  auth.save();
  store.set("repo", name);
  start(new Library(repo, auth));
}

/** No sign-in: this device alone, for files and web pages, with the places kept in this browser. */
function onDevice() {
  repo = null;
  start(new Library(null, null));
}

function start(lib) {
  library = lib;
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
  for (const n of library.notes) { const p = document.createElement("p"); p.className = "error"; p.textContent = n; el.append(p); }
  const open = document.createElement("div"); open.className = "open";
  open.innerHTML = `<form class="open-url" id="open-url"><input id="url" type="url" inputmode="url" placeholder="A web page to read: https://…"
      autocapitalize="off" autocorrect="off" spellcheck="false" aria-label="Web page address"><button class="btn">Read</button></form>
    <div class="actions"><button class="btn quiet" id="open-file">Open a file</button><span class="note busy" id="open-note"></span></div>`;
  if (!library.repo) {
    el.insertAdjacentHTML("beforeend", `<h1 class="page">Read something</h1><p class="lead">A web page or a Markdown file, read aloud with
      each sentence and word marked as it is said. It stays on this device: <a href="../privacy.html">what goes where</a>.
      <a href="#/" id="signin-link">Sign in with GitHub</a> to keep what you read, and your place in it, on every device.</p>`);
    el.append(open);
  } else if (!library.docs.length) {
    el.insertAdjacentHTML("beforeend", '<h1 class="page">Nothing here yet</h1><p class="lead">Open a web page or a file below and it stays in your library, on every device. Or write a playlist in your library\'s README, add one from another repository in settings, or run <code>voce --sync</code> on a Mac.</p>');
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
  if (library.repo) { open.classList.add("below"); el.append(open); }
  $("open-file").onclick = () => $("file").click();
  if ($("signin-link")) $("signin-link").onclick = (e) => { e.preventDefault(); if (reader) reader.stop(); signInView(); };
  $("open-url").onsubmit = (e) => { e.preventDefault(); openPage($("url").value); };
}

/** Read something new and go to it, saying how it's going under the open buttons. */
async function openDoc(doing, get) {
  if (!library) return;
  const note = (text) => { const n = $("open-note"); if (n) n.textContent = text; };
  note(doing);
  try {
    const { text, name, from } = await get(note);
    if (library.repo) note("Adding it to your library…");
    location.hash = `#/doc/${await library.open(text, name, from)}`;
  } catch (e) { note(`Couldn't read it: ${e.message}`); }
}

const isHtml = (name) => /\.x?html?$/i.test(name);

function openFile(file) {
  if (!file) return;
  return openDoc("Reading…", async () => {
    const text = await file.text();
    const from = { kind: "file", file: file.name };
    return isHtml(file.name) ? { text: await pageToMarkdown(text), name: file.name.replace(/\.\w+$/, ".md"), from } : { text, name: file.name, from };
  });
}

function openPage(typed) {
  const url = address(typed);
  if (!url) { $("open-note").textContent = "That isn't a web address. Try one like https://example.com/post."; return; }
  return openDoc("Fetching the page…", async (note) => {
    const page = await fetchPage(url);
    note("Reading…");
    const name = `${new URL(page.url).hostname}.md`, from = { kind: "page", url: page.url };
    return /html|xml/.test(page.type) ? { text: await pageToMarkdown(page.text, page.url), name, from } : { text: page.text, name, from };
  });
}

/** Something shared to voce from another app (Android's share sheet): a page's address, or text to read as it is. */
let shared = null;
function takeShare() {
  const q = new URLSearchParams(location.search);
  if (!["url", "text", "title"].some((k) => q.has(k))) return;
  history.replaceState(null, "", location.pathname + location.hash);
  shared = { url: q.get("url") || "", text: q.get("text") || "", title: q.get("title") || "" };
}

function openShared(s) {
  const url = address(s.url) || address(s.text);
  if (url) return openPage(url);
  if (!s.text.trim()) return;
  return openDoc("Reading…", async () => ({ text: s.title ? `# ${s.title}\n\n${s.text}` : s.text, name: "shared.md", from: { kind: "text" } }));
}

function esc(s) { return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

async function showDoc(hash) {
  show("reader");
  $("article").innerHTML = '<p class="note busy">Loading…</p>';
  try {
    if (!library.docs.length) await library.load();
    await reader.open(hash);
    if ("mediaSession" in navigator) {
      const art = (n) => ({ src: new URL(`../assets/icon-${n}.png`, location.href).href, sizes: `${n}x${n}`, type: "image/png" });
      navigator.mediaSession.metadata = new MediaMetadata({ title: reader.doc.title, artist: "voce", artwork: [art(192), art(512)] });
    }
  } catch (e) { $("article").innerHTML = `<p class="error">${esc(e.message)}</p>`; }
}

async function route() {
  if (!library) { show("connect"); return; }
  const m = location.hash.match(/^#\/doc\/([0-9a-f]{64})$/);
  if (m) await showDoc(m[1]);
  else {
    if (reader) reader.stop();
    await showLibrary();
    if (shared) { const s = shared; shared = null; await openShared(s); }
  }
}

function fillVoices() {
  const engine = store.get("engine", "browser");
  $("s-engine").value = engine;
  const list = engine === "kokoro" ? KokoroVoice.voices()
    : [{ id: "", label: "The best for each document's language" }, ...BrowserVoice.voices()];
  const chosen = store.get(`voice.${engine}`, engine === "kokoro" ? "af_heart" : "");
  $("s-voice").replaceChildren(...list.map((v) => { const o = document.createElement("option"); o.value = v.id; o.textContent = v.label; o.selected = v.id === chosen; return o; }));
  if (!list.length) { const o = document.createElement("option"); o.textContent = "the device's default voice"; $("s-voice").append(o); }
  fillSources();
  $("s-kokoro-note").textContent = engine === "kokoro"
    ? (KokoroVoice.tts ? "Kokoro is loaded. It runs on this device; nothing is sent anywhere." : "The model is fetched from Hugging Face once and kept by the browser.")
      + " It speaks English; a document in another language is read by the device's voice."
    : "The voices your device has. Instant, and fine for prose; Kokoro reads code and names more evenly. "
      + "For a better voice on an iPhone, download one marked Enhanced or Premium in Settings, Accessibility, "
      + "Spoken Content, Voices, then come back here.";
}

function fillSources() {
  const sources = library && library.repo ? library.sources : [];
  $("s-sources").replaceChildren(...sources.map((src) => {
    const row = document.createElement("div"); row.className = "kv source";
    const b = document.createElement("b"); b.textContent = `${src.repo} · ${src.path}`;
    const x = document.createElement("button"); x.className = "icon"; x.setAttribute("aria-label", "Remove"); x.textContent = "×";
    x.onclick = () => library.removeSource(src.id).then(fillSources, (e) => { $("s-src-note").textContent = e.message; });
    row.append(b, x);
    return row;
  }));
  if (!sources.length) $("s-sources").innerHTML = '<p class="note">None yet. A README with a "## Listen in this order" section, in a repository voce can reach.</p>';
  if (auth && !auth.manual && !$("s-repos").children.length) {
    reachable(auth).then((names) => $("s-repos").replaceChildren(...names.map((n) => { const o = document.createElement("option"); o.value = n; return o; }))).catch(() => {});
  }
}

async function addSource() {
  const repo = $("s-src-repo").value.trim().replace(/^https:\/\/github\.com\//, "").replace(/\.git$/, "");
  const path = $("s-src-path").value.trim().replace(/^\/+/, "");
  if (!/^[\w.-]+\/[\w.-]+$/.test(repo) || !path) { $("s-src-note").textContent = "Give the repository as owner/name and the README's path in it."; return; }
  if (!library || !library.repo) return;
  try { await library.addSource(repo, path); } catch (e) { $("s-src-note").textContent = e.message; return; }
  $("s-src-path").value = ""; $("s-src-note").textContent = "";
  fillSources();
}

function wire() {
  if (!GITHUB_APP.client) { $("signin-row").classList.add("hidden"); $("token-form").open = true; $("token-form").querySelector("summary").classList.add("hidden"); }
  $("signin-go").onclick = () => signIn();
  $("install-go").onclick = () => signIn(true);
  $("make-install").onclick = () => signIn(true);
  $("make-go").href = $("make-again").href = makeUrl();
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
  $("settings").onclick = () => {
    $("s-repo").textContent = repo ? repo.name : "none: this device only";
    $("s-change").classList.toggle("hidden", !repo || !auth || auth.manual);
    $("s-sources-box").classList.toggle("hidden", !repo);
    $("s-disconnect").textContent = repo ? "Disconnect this device" : "Sign in to your library";
    fillVoices();
    $("sheet").classList.remove("hidden");
  };
  $("s-close").onclick = () => $("sheet").classList.add("hidden");
  $("sheet").onclick = (e) => { if (e.target === $("sheet")) $("sheet").classList.add("hidden"); };
  $("s-src-add").onclick = addSource;
  $("s-src-path").onkeydown = (e) => { if (e.key === "Enter") addSource(); };
  $("file").onchange = () => { openFile($("file").files[0]); $("file").value = ""; };
  $("s-engine").onchange = () => { store.set("engine", $("s-engine").value); swapVoice(); fillVoices(); };
  $("s-words").checked = store.get("words", true);
  $("s-words").onchange = () => { store.set("words", $("s-words").checked); if (!$("s-words").checked) ui.unmark(); ui.said = null; };
  $("s-voice").onchange = () => { store.set(`voice.${store.get("engine", "browser")}`, $("s-voice").value); swapVoice(); };
  $("s-change").onclick = async () => { if (reader) reader.stop(); repo = library = reader = null; $("sheet").classList.add("hidden"); location.hash = "#/"; await pickRepo(); };
  $("s-disconnect").onclick = () => {
    if (reader) reader.stop();
    $("sheet").classList.add("hidden");
    if (!repo) { signInView(); return; }
    ["repo", "token", "auth", "signin"].forEach(store.del);
    auth = repo = null; onDevice(); location.hash = "#/"; route();
  };
  $("device-go").onclick = () => { onDevice(); location.hash = "#/"; route(); };
  $("back").onclick = () => ui.back();
  // Scrolling the page by hand lets go of the voice; the player itself never scrolls the page.
  const letGo = (e) => { if (!e.target.closest || !e.target.closest("#player")) ui.free = true; };
  addEventListener("wheel", letGo, { passive: true });
  addEventListener("touchmove", letGo, { passive: true });
  addEventListener("scroll", () => ui.placeBack(), { passive: true });
  addEventListener("resize", () => ui.placeBack());
  wireSeek();
  $("play").onclick = () => { if (!reader) return; reader.playing ? reader.pause() : reader.play(); };
  $("prev").onclick = () => reader && reader.go(reader.pos - 1);
  $("next").onclick = () => reader && reader.go(reader.pos + 1);
  $("speed").onclick = () => { if (!reader) return; const steps = [0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0]; reader.setSpeed(steps[(steps.findIndex((s) => s >= reader.speed - 0.01) + 1) % steps.length]); };
  // A tap on the sentence being read plays or pauses it; a tap on any other sentence goes there.
  $("article").onclick = (e) => {
    const el = e.target.closest("[data-unit]");
    if (!el || !reader) return;
    if (+el.dataset.unit === reader.pos) $("play").click(); else reader.go(+el.dataset.unit);
  };
  document.addEventListener("keydown", (e) => {
    if (!reader || $("reader").classList.contains("hidden") || e.target.tagName === "INPUT") return;
    if (e.key === " ") { e.preventDefault(); $("play").click(); }
    else if (["PageUp", "PageDown", "Home", "End", "ArrowUp", "ArrowDown"].includes(e.key)) ui.free = true;
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

/** The progress bar is a place to go: drag along it to see where, and let go to read from there. */
function wireSeek() {
  const bar = $("seek");
  const at = (e) => {
    const r = bar.getBoundingClientRect();
    return Math.min(reader.units.length - 1, Math.floor(Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * reader.units.length));
  };
  const ready = () => reader && reader.units && reader.units.length;
  bar.onpointerdown = (e) => { if (!ready()) return; bar.setPointerCapture(e.pointerId); ui.progress((at(e) + 1) / reader.units.length); };
  bar.onpointermove = (e) => { if (ready() && bar.hasPointerCapture(e.pointerId)) ui.progress((at(e) + 1) / reader.units.length); };
  bar.onpointerup = (e) => { if (!ready()) return; ui.free = false; reader.go(at(e)); };
  bar.onpointercancel = () => ready() && reader.show();
}

/** The sign-in screen, from reading on this device alone. */
function signInView() {
  library = reader = null;
  location.hash = "#/";
  connectView("signin");
}

function swapVoice() {
  if (!reader) return;
  const wasPlaying = reader.playing;
  reader.stopVoice();
  reader.playing = false;
  voice = reader.chosen = makeVoice();
  reader.useVoiceFor(reader.language || "");
  if (wasPlaying) reader.play();
}

(async () => {
  wire();
  takeShare();
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
  } else if (!auth) {
    onDevice();
  }
  await route();
})();

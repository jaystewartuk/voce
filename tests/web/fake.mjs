/* A fake GitHub, relay and web for the web app's tests: everything the page would reach on the network, answered
   from memory. Requests to anywhere else are refused and recorded, so a test can say none were made. */

import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const ROOT = new URL("../..", import.meta.url).pathname;
const PYTHON = process.env.VOCE_PYTHON || (existsSync(join(ROOT, ".venv/bin/python")) ? join(ROOT, ".venv/bin/python") : "python3");
const APP = "http://localhost:8787/app/";

const blobSha = (text) => {
  const body = Buffer.from(text, "utf8");
  return createHash("sha1").update(`blob ${body.length}\0`).update(body).digest("hex");
};

/** The starter library, as GitHub would copy it from the template: every file under template/. */
export function templateFiles() {
  const dir = join(ROOT, "template"), files = {};
  const walk = (d) => readdirSync(d).forEach((n) => {
    const p = join(d, n);
    if (statSync(p).isDirectory()) walk(p); else files[relative(dir, p)] = readFileSync(p, "utf8");
  });
  walk(dir);
  return files;
}

/** One person's GitHub: their repositories, as {owner/name: {path: text}}, and which the app is installed on. */
export class FakeGitHub {
  constructor() {
    this.repos = {};          // owner/name -> {path: text}
    this.installed = new Set();
    this.offline = [];        // requests the page tried to make anywhere else
    this.made = execFileSync(PYTHON, [join(ROOT, "tests/web/prepare.py"), "made"], { encoding: "utf8" }).trim();
  }

  repo(name, files = {}, installed = true) {
    this.repos[name] = { ...files };
    if (installed) this.installed.add(name);
    return this.repos[name];
  }

  /** Answer the page's requests; call before the page loads. */
  async attach(context) {
    await context.route("**/*", (route) => this.answer(route));
  }

  async answer(route) {
    const req = route.request(), url = new URL(req.url());
    if (url.host === "localhost:8787") {
      if (url.pathname === "/app/py.js") return route.fulfill({ path: join(ROOT, "tests/web/py-stand-in.js"), contentType: "text/javascript" });
      if (url.pathname === "/app/py/manifest.json") return route.fulfill({ json: { wheel: "-", made: this.made } });
      if (url.pathname === "/__prepare") return route.fulfill({ contentType: "application/json", body: this.prepare(req.postData()) });
      return route.continue();
    }
    if (url.host === "api.github.com") return this.api(route, req, url);
    if (url.host === "voce-relay.jay73x.workers.dev") return route.fulfill({ json: { access_token: "t", expires_in: 28800, refresh_token: "r" } });
    if (url.host === "github.com" && /^\/(login\/oauth\/authorize|apps\/[^/]+\/installations\/new)/.test(url.pathname)) {
      // GitHub agrees straight away and sends the person back with a code, as it does once they press the button.
      const back = new URL(APP);
      back.searchParams.set("code", "c");
      back.searchParams.set("state", url.searchParams.get("state"));
      return route.fulfill({ status: 302, headers: { Location: back.href } });
    }
    if (url.host === "example.test") {
      return route.fulfill({ contentType: "text/markdown", headers: { "Access-Control-Allow-Origin": "*" },
                             body: "# A post worth hearing\n\nThe cache key ignores the query string. So two pages share one entry.\n" });
    }
    this.offline.push(req.url());
    return route.abort();
  }

  prepare(body) {
    return execFileSync(PYTHON, [join(ROOT, "tests/web/prepare.py")], { input: body, encoding: "utf8" });
  }

  api(route, req, url) {
    const ok = (json, status = 200) => route.fulfill({ status, json });
    const missing = () => route.fulfill({ status: 404, json: { message: "Not Found" } });
    const p = url.pathname, method = req.method();
    if (p === "/user/installations") return ok({ installations: this.installed.size ? [{ id: 1 }] : [] });
    if (p === "/user/installations/1/repositories") return ok({ repositories: [...this.installed].map((full_name) => ({ full_name })) });
    const m = /^\/repos\/([^/]+\/[^/]+)(\/.*)?$/.exec(p);
    if (!m || !this.installed.has(m[1])) return missing();
    const files = this.repos[m[1]], rest = m[2] || "";
    if (!rest) return ok({ full_name: m[1] });

    let t;
    if ((t = /^\/git\/trees\/HEAD(?::(.*))?$/.exec(rest))) {
      if (!Object.keys(files).length) return route.fulfill({ status: 409, json: { message: "Git Repository is empty." } });
      const folder = t[1] ? decodeURIComponent(t[1]) + "/" : "", deep = url.searchParams.has("recursive");
      const under = Object.keys(files).filter((f) => f.startsWith(folder) && (deep || !f.slice(folder.length).includes("/")));
      if (folder && !under.length) return missing();
      return ok({ tree: under.map((f) => ({ path: f.slice(folder.length), type: "blob", sha: blobSha(files[f]) })) });
    }
    if ((t = /^\/git\/blobs\/([0-9a-f]{40})$/.exec(rest))) {
      const hit = Object.values(files).find((text) => blobSha(text) === t[1]);
      return hit === undefined ? missing() : route.fulfill({ contentType: "application/vnd.github.raw+json", body: hit });
    }
    if ((t = /^\/contents\/(.+)$/.exec(rest))) {
      const path = decodeURIComponent(t[1]), have = files[path];
      if (method === "GET") {
        return have === undefined ? missing() : ok({ sha: blobSha(have), content: Buffer.from(have).toString("base64") });
      }
      const body = JSON.parse(req.postData() || "{}");
      if (method === "PUT") {
        if (have !== undefined && body.sha !== blobSha(have)) return ok({ message: "sha wasn't supplied, or is not the latest" }, have !== undefined && body.sha ? 409 : 422);
        files[path] = Buffer.from(body.content, "base64").toString("utf8");
        return ok({ content: { path, sha: blobSha(files[path]) } }, have === undefined ? 201 : 200);
      }
      if (method === "DELETE") {
        if (have === undefined) return missing();
        if (body.sha !== blobSha(have)) return ok({ message: "sha does not match" }, 409);
        delete files[path];
        return ok({ commit: {} });
      }
    }
    return missing();
  }
}

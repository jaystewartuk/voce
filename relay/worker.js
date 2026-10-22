/* voce's relay: the two steps a static page can't do for itself.

   GitHub hands the web app a code; swapping it for a token needs the app's client secret, and GitHub's token
   endpoint won't answer a browser at all. This worker does that swap. The token goes back to the page and from
   there only to api.github.com; the library itself never passes through here.

   And most sites won't let a page on another site read them, so a web page to be read aloud is fetched here
   (/page) and handed back as it came: the address the user gave, nothing of theirs sent with it.

   It keeps no state, writes no log, and answers only the web app's origin.

   Settings: ORIGIN and CLIENT_ID in wrangler.toml; CLIENT_SECRET with `wrangler secret put CLIENT_SECRET`. */

const GITHUB = "https://github.com/login/oauth/access_token";

export default {
  async fetch(request, env) {
    const cors = {
      "Access-Control-Allow-Origin": env.ORIGIN, "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type", "Access-Control-Max-Age": "86400", Vary: "Origin",
    };
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    const path = new URL(request.url).pathname;
    if (request.method !== "POST" || !["/token", "/refresh", "/page"].includes(path)) {
      return new Response("voce's relay. It swaps a GitHub sign-in code for a token, fetches a web page for the app to read, and keeps nothing.\n",
                          { status: path === "/" ? 200 : 404, headers: { ...cors, "Content-Type": "text/plain" } });
    }
    if (request.headers.get("Origin") !== env.ORIGIN) return json({ error: "origin", error_description: "Not from the voce app." }, 403, cors);

    const body = await request.json().catch(() => ({}));
    if (path === "/page") return page(body.url, cors);
    const form = { client_id: env.CLIENT_ID, client_secret: env.CLIENT_SECRET };
    if (path === "/token") {
      if (typeof body.code !== "string") return json({ error: "code", error_description: "No code." }, 400, cors);
      form.code = body.code;
      if (typeof body.redirect_uri === "string") form.redirect_uri = body.redirect_uri;
    } else {
      if (typeof body.refresh_token !== "string") return json({ error: "refresh", error_description: "No refresh token." }, 400, cors);
      form.grant_type = "refresh_token";
      form.refresh_token = body.refresh_token;
    }

    const r = await fetch(GITHUB, {
      method: "POST", headers: { Accept: "application/json", "Content-Type": "application/json" }, body: JSON.stringify(form),
    });
    const grant = await r.json().catch(() => ({ error: "github", error_description: `GitHub said ${r.status}.` }));
    return json(grant, grant.error ? 400 : 200, cors);
  },
};

const PAGE_LIMIT = 5e6; // characters: more than any article

/** A web page's text, its type and where it ended up after redirects. Web pages and plain text only. */
async function page(address, cors) {
  let url;
  try { url = new URL(address); } catch { /* not an address */ }
  if (!url || !/^https?:$/.test(url.protocol)) return json({ error: "url", error_description: "That isn't a web address." }, 400, cors);
  let r;
  try {
    r = await fetch(url, { redirect: "follow", headers: {
      Accept: "text/html,application/xhtml+xml,text/markdown,text/plain;q=0.9",
      "User-Agent": "Mozilla/5.0 (compatible; voce; +https://jaystewartuk.github.io/voce/)" } });
  } catch { return json({ error: "fetch", error_description: "That site didn't answer." }, 502, cors); }
  if (!r.ok) return json({ error: "page", error_description: `That page answered ${r.status}.` }, 502, cors);
  const type = r.headers.get("Content-Type") || "";
  if (!/^text\/|xhtml/.test(type)) return json({ error: "type", error_description: "That address isn't a web page or text." }, 415, cors);
  const text = await r.text();
  if (text.length > PAGE_LIMIT) return json({ error: "size", error_description: "That page is too long to read." }, 413, cors);
  return json({ url: r.url, type, text }, 200, cors);
}

function json(data, status, headers) {
  return new Response(JSON.stringify(data), { status, headers: { ...headers, "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

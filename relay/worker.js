/* voce's sign-in relay: the one step a static page can't do for itself.

   GitHub hands the web app a code; swapping it for a token needs the app's client secret, and GitHub's token
   endpoint won't answer a browser at all. This worker does that swap and nothing else. It keeps no state, writes
   no log, and answers only the web app's origin. The token goes back to the page and from there only to
   api.github.com; the library itself never passes through here.

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
    if (request.method !== "POST" || (path !== "/token" && path !== "/refresh")) {
      return new Response("voce's sign-in relay. It swaps a GitHub sign-in code for a token and keeps nothing.\n",
                          { status: path === "/" ? 200 : 404, headers: { ...cors, "Content-Type": "text/plain" } });
    }
    if (request.headers.get("Origin") !== env.ORIGIN) return json({ error: "origin", error_description: "Not from the voce app." }, 403, cors);

    const body = await request.json().catch(() => ({}));
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

function json(data, status, headers) {
  return new Response(JSON.stringify(data), { status, headers: { ...headers, "Content-Type": "application/json", "Cache-Control": "no-store" } });
}

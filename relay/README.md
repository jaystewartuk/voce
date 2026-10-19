# The sign-in relay

The web app signs you in with GitHub instead of asking for a token. GitHub's half of that is a GitHub App; the
other half is this worker, because GitHub's token endpoint needs the app's client secret and refuses browsers.
The worker swaps the sign-in code for a token, returns it to the page, and keeps nothing. The library never
passes through it. If it is ever down, devices already signed in carry on; only new sign-ins wait.

## Set it up once

1. **Register the GitHub App** at [github.com/settings/apps/new](https://github.com/settings/apps/new):
   - Name: `voce reader` (the name `voce` is taken). Homepage: `https://jaystewartuk.github.io/voce/`.
   - Callback URL: `https://jaystewartuk.github.io/voce/app/`. Tick **Request user authorization (OAuth) during
     installation**. Leave **Expire user authorization tokens** on; the app refreshes them through the relay.
   - Leave the webhook off (untick **Active**).
   - Repository permissions: **Contents: Read and write**. Nothing else.
   - Where can this app be installed: **Any account**.
   - After creating it, **Generate a new client secret** and keep it for step 2. Note the **Client ID** and the
     app's slug (the end of its public URL, `github.com/apps/<slug>`).
2. **Deploy the worker** from this folder:
   ```sh
   npx wrangler login
   npx wrangler secret put CLIENT_SECRET     # paste the client secret
   npx wrangler deploy                       # prints the worker's URL, like https://voce-relay.<you>.workers.dev
   ```
   Put the client ID in `wrangler.toml` first, and change `ORIGIN` if the app is served from somewhere else.
3. **Tell the web app** in `site/app/app.js`, at the top: the client ID, the slug and the worker's URL in `GITHUB_APP`.
   While `client` is empty, the app shows only the token form, so the site works before this is done.

That is the whole server: one stateless function. Anyone running their own copy of the site registers their own
app and worker the same way, or leaves `GITHUB_APP.client` empty and keeps the token form.

## What the user sees

1. **Sign in with GitHub** on the connect screen. GitHub asks them to authorize voce, once.
2. If voce isn't installed on any of their repositories yet, a second step sends them to GitHub's install screen,
   where they pick the library repository `voce --sync` made. GitHub returns them to the app signed in.
3. The app lists the repositories voce can reach; with one, it is used without asking.

Disconnecting in settings forgets the token on that device. Revoking the app at
[github.com/settings/installations](https://github.com/settings/installations) cuts off every device at once.

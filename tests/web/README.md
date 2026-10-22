# The web app's tests

`site/app/` in headless Chromium, used the way a person would: signing in, making a library from the template,
opening a web page, signing in after reading on the device alone. Everything the page reaches on the network is
answered by `fake.mjs`: GitHub's API, the relay, GitHub's sign-in and install pages (pressed straight away), and a
web page. Any other request fails the test. Documents are prepared by this checkout's voce through `prepare.py`, in
place of Pyodide.

```bash
cd tests/web
npm ci
npx playwright install chromium
VOCE_PYTHON=../../.venv/bin/python npx playwright test
```

GitHub's own screens aren't tested here. Before a release, or after changing the GitHub App, run through them by
hand with an account that has no library: sign in, "Make your library", "Create repository", "Give voce access
to it", and check the "Start here" playlist plays. Do it once from the iOS home-screen app too.

`.github/workflows/live.yml` checks once a week that the template, the relay and the published app are still there.

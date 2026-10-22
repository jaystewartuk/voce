/* Stands in for site/app/py.js in the web tests: the same messages, answered by this checkout's voce through the
   test's fake network (prepare.py), so the tests don't load Pyodide from its CDN. */

onmessage = async ({ data }) => {
  const { id, op } = data;
  try {
    if (op !== "prepare") throw new Error(`unknown op ${op}`);
    const r = await fetch("/__prepare", { method: "POST", body: JSON.stringify({ text: data.text, name: data.name }) });
    postMessage({ id, result: await r.json() });
  } catch (e) {
    postMessage({ id, error: String(e.message || e) });
  }
};

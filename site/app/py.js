/* voce's own reading code, in the page. A module worker, so the screen never waits on it.

   Pyodide (Python compiled to WebAssembly) loads once from the CDN, then voce's wheel from py/ beside this file,
   with pygments from Pyodide's own packages. From then on the page can turn any Markdown into the same blocks and
   spoken units the Mac makes, and read a playlist straight from a repository. Messages in: {id, op, ...}; out:
   {id, result} or {id, error}, and {progress} while loading. */

const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

let ready = null;

function load() {
  if (!ready) ready = (async () => {
    postMessage({ progress: "Loading voce's reader, once: Python for the browser" });
    const { loadPyodide } = await import(PYODIDE + "pyodide.mjs");
    const py = await loadPyodide({ indexURL: PYODIDE });
    postMessage({ progress: "Loading voce's reader: the words for code" });
    await py.loadPackage(["micropip", "pygments"], { messageCallback: () => {} });
    const manifest = await (await fetch(new URL("py/manifest.json", self.location.href))).json();
    const wheel = new URL("py/" + manifest.wheel, self.location.href).href;
    await py.runPythonAsync(`
import micropip
await micropip.install(${JSON.stringify(wheel)}, deps=False)
import hashlib, json
from pathlib import Path
from voce.document import from_markdown
from voce.playlist import parse_playlist
from voce.prepared import as_json, MADE_BY

def prepare(text, name):
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return json.dumps(as_json(from_markdown(text, Path(name)), key), ensure_ascii=False)

def playlist(text):
    return json.dumps(parse_playlist(text))
`);
    self.made = py.globals.get("MADE_BY");
    self.prepare = py.globals.get("prepare");
    self.playlist = py.globals.get("playlist");
    postMessage({ progress: "" });
    return py;
  })().catch((e) => { ready = null; throw e; });
  return ready;
}

onmessage = async ({ data }) => {
  const { id, op } = data;
  try {
    await load();
    let result;
    if (op === "made") result = self.made;
    else if (op === "prepare") result = JSON.parse(self.prepare(data.text, data.name || "-"));
    else if (op === "playlist") result = JSON.parse(self.playlist(data.text));
    else throw new Error(`unknown op ${op}`);
    postMessage({ id, result });
  } catch (e) {
    postMessage({ id, error: String(e.message || e).split("\n").filter((l) => l.trim()).slice(-1)[0] || "the reader failed" });
  }
};

#!/bin/sh
# The web app's copy of voce: a wheel of this package and a manifest naming it, in site/app/py/. The page loads the
# wheel into Pyodide so a phone can read any Markdown itself. Run from the repository root; the Pages workflow runs
# it before uploading site/. Needs pip with network access, to fetch hatchling once.
set -eu
out=site/app/py
rm -rf "$out" && mkdir -p "$out"
python -m pip wheel . --no-deps --no-build-isolation -q -w "$out" 2>/dev/null || python -m pip wheel . --no-deps -q -w "$out"
wheel=$(basename "$out"/voce-*.whl)
made=$(PYTHONPATH=src python -c "from voce.prepared import MADE_BY; print(MADE_BY)")
printf '{"wheel": "%s", "made": "%s"}\n' "$wheel" "$made" > "$out/manifest.json"
echo "$out/$wheel, made by $made"

#!/usr/bin/env bash
# Re-record docs/assets/demo.gif and the screenshot. Needs vhs (brew install vhs) and voce in .venv.
#
# It builds a throwaway Claude Code transcript holding docs/demo/reply.md, so the recording shows `voce -r`
# exactly as you would use it, with empty state and cache folders so nothing from your machine shows up.
set -euo pipefail
cd "$(dirname "$0")/../.."
VOCE_DEMO_HOME="$(mktemp -d)"
export VOCE_DEMO_HOME
python3 - "$VOCE_DEMO_HOME" <<'PY'
import json, pathlib, re, sys
home = pathlib.Path(sys.argv[1])
folder = home / "claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(pathlib.Path.cwd().resolve()))
folder.mkdir(parents=True)
reply = pathlib.Path("docs/demo/reply.md").read_text()
lines = [{"type": "user", "message": {"role": "user", "content": "Why does the cache miss?"}},
         {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": reply}]}}]
(folder / "demo.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")
PY
# Fetch the audio first, so the recording never waits on the voice.
CLAUDE_CONFIG_DIR="$VOCE_DEMO_HOME/claude" XDG_STATE_HOME="$VOCE_DEMO_HOME/state" \
  XDG_CACHE_HOME="$VOCE_DEMO_HOME/cache" .venv/bin/voce -r --prepare >/dev/null
vhs docs/demo/demo.tape
rm -rf "$VOCE_DEMO_HOME"

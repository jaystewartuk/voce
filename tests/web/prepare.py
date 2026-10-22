"""What the web app's reader (site/app/py.js) answers, for the web tests: Markdown in on stdin, prepared JSON out.

The same calls py.js makes in Pyodide, run with this checkout's voce, so the tests read documents exactly as the
page would without loading Python into the browser.
"""

import hashlib
import json
import sys
from pathlib import Path

from voce.document import from_markdown
from voce.prepared import MADE_BY, as_json

if sys.argv[1:] == ["made"]:
    print(MADE_BY)
else:
    request = json.load(sys.stdin)
    text = request["text"]
    key = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(json.dumps(as_json(from_markdown(text, Path(request.get("name") or "-")), key), ensure_ascii=False))

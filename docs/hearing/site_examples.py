#!/usr/bin/env python3
"""Write the language switcher on the landing page, so the page says exactly what voce says.

The lines to show are listed below. Each is read with spoken_line, in the language's own words, and the result goes
into site/index.html between the two language-switcher comments. Nothing on the page is typed by hand.

Each line can be played. Its clip is what Kokoro's af_heart says for the exact text voce sends the voice, and is
named by a hash of that text, so a line that reads differently needs a new clip and an old clip is never played
for a new reading.

    .venv/bin/python docs/hearing/site_examples.py           # rewrite the switcher in site/index.html
    .venv/bin/python docs/hearing/site_examples.py --record  # and record any missing clips, removing old ones
    .venv/bin/python docs/hearing/site_examples.py --check   # exit 1 if the page or its clips are out of date

tests/test_site_examples.py runs --check, so a change to how a language reads that the page shows must be followed
by running this once with --record.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from voce.speech import speakable, spoken_line
from voce.speech.words import language

PAGE = Path(__file__).resolve().parents[2] / "site" / "index.html"
CLIPS = PAGE.parent / "assets" / "lang"
START, END = "<!-- language-switcher:start -->", "<!-- language-switcher:end -->"
VOICE = "af_heart"  # the demo's voice

# tab label, fence name, the manual in words, and the lines to show. The first language is the one open on load.
EXAMPLES = [
    ("Python", "python", "the Python reference", [
        "while chunk := f.read(8192):",
        "def __init__(self, **kwargs) -> None:",
        "value: str | None = None",
        "total //= 2",
    ]),
    ("JavaScript", "javascript", "MDN", [
        "user?.name ?? 'guest'",
        "options ??= {}",
        "const mid = (low + high) >>> 1;",
        "if (typeof value === 'function') {",
    ]),
    ("TypeScript", "typescript", "the TypeScript Handbook", [
        "function first<T>(items: T[]): T | undefined {",
        "const el = document.getElementById('app')!;",
        "readonly items?: ReadonlyArray<Item>;",
        "return <Card title={user.name} />",
    ]),
    ("Go", "go", "the Go specification", [
        "if err := json.Unmarshal(data, &v); err != nil {",
        "x := <-ch",
        "ch <- v",
        "y := x &^ mask",
    ]),
    ("Rust", "rust", "the Rust Reference and Book", [
        "let n = reader.read(&mut buf)?;",
        "let v = s.parse::<i32>();",
        'println!("hello {}", name);',
        "for i in 0..=n {",
    ]),
    ("PHP", "php", "the PHP manual", [
        "$totals[$channel] ??= 0;",
        "fn ($a, $b) => $a['nights'] <=> $b['nights']",
        "foreach ($rows as &$row) {",
        "$reservation->guest?->notify($booking);",
    ]),
    ("Ruby", "ruby", "the Ruby documentation", [
        "list << item",
        "name = user&.name || 'guest'",
        "return if list.empty?",
        "Integer === value",
    ]),
    ("Java", "java", "the Java Language Specification", [
        "names.forEach(System.out::println);",
        "List<String> names = new ArrayList<>();",
        "int h = hash >>> 16;",
        "void log(String format, Object... params) {",
    ]),
    ("C#", "csharp", "Microsoft's C# reference", [
        'person?.Name ?? "unknown"',
        "var last = values[^1];",
        "items.Where(x => x.IsActive)",
        "_cache ??= new Dictionary<string, int>();",
    ]),
    ("Swift", "swift", "The Swift Programming Language", [
        'user?.name ?? "Anonymous"',
        "for i in 0..<count {",
        "let total = a &+ b",
        "func greet(person: String) -> String {",
    ]),
    ("Kotlin", "kotlin", "the Kotlin documentation", [
        "val l = b?.length ?: 0",
        "val l = b!!.length",
        "for (i in 1..10) println(i)",
        "if (other !is Pin) return false",
    ]),
    ("Shell", "bash", "the Bash manual", [
        'grep -r "TODO" . | wc -l',
        '[ "$a" -eq 1 ] && echo ok',
        'cat <<< "$text"',
        "make build > out.log",
    ]),
    ("SQL", "sql", "the PostgreSQL manual", [
        "SELECT data->>'name' FROM users WHERE meta ? 'admin';",
        "SELECT created_at::date FROM orders;",
        "WHERE tags @> ARRAY['a']",
        "SELECT * FROM film WHERE title ~* 'ace'",
    ]),
]


def sent(line: str, fence: str) -> str:
    """What voce sends the voice for this line, as document.py does for a line of code."""
    return speakable(spoken_line(line, fence))


def clip_name(text: str) -> str:
    return hashlib.sha1(f"{VOICE}\n{text}".encode()).hexdigest()[:12] + ".mp3"


def clips() -> dict[str, str]:
    """Each clip the page plays, and the text it says."""
    return {clip_name(sent(line, fence)): sent(line, fence) for _, fence, _, lines in EXAMPLES for line in lines}


def switcher() -> str:
    """The tabs and their panels, as the HTML that goes between the two comments."""
    tabs, panels = [], []
    for n, (label, fence, manual_name, lines) in enumerate(EXAMPLES):
        key = fence if fence != "bash" else "shell"
        first = n == 0
        tab_index = "" if first else ' tabindex="-1"'
        hidden = "" if first else " hidden"
        tabs.append(
            f'        <button type="button" role="tab" id="tab-{key}" aria-controls="lang-{key}" '
            f'aria-selected="{str(first).lower()}"{tab_index}>{html.escape(label)}</button>')
        rows = "\n".join(
            f"            <tr><td><code>{html.escape(line)}</code></td>"
            f'<td><button type="button" class="say" data-clip="assets/lang/{clip_name(sent(line, fence))}" '
            f'aria-label="Hear it" hidden></button>'
            f"&quot;{html.escape(spoken_line(line, fence))}&quot;</td></tr>" for line in lines)
        url = language(fence).manual
        panels.append(f'''      <div class="lang-panel" id="lang-{key}" role="tabpanel" aria-labelledby="tab-{key}"
           data-lang="{fence}"{hidden}>
        <div class="card">
          <table class="said-table">
            <thead><tr><th scope="col">On the line</th><th scope="col">What you hear</th></tr></thead>
            <tbody>
{rows}
            </tbody>
          </table>
          <p class="small"><button type="button" class="say-all" hidden>Hear all four</button>
            Operators are named as <a href="{html.escape(url)}">{html.escape(manual_name)}</a> names them.</p>
        </div>
      </div>''')
    return (f'{START}\n      <div class="lang-tabs" role="tablist" aria-label="Language">\n' + "\n".join(tabs)
            + "\n      </div>\n" + "\n".join(panels) + f"\n      {END}")


def rewrite(page: str) -> str:
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(page):
        raise SystemExit(f"{PAGE} has no {START} ... {END} to fill in")
    return pattern.sub(lambda _: switcher(), page, count=1)


def stale() -> tuple[list[str], list[str]]:
    """The clips the page needs that aren't recorded, and the recorded clips it no longer plays."""
    want, have = set(clips()), {p.name for p in CLIPS.glob("*.mp3")}
    return sorted(want - have), sorted(have - want)


def record() -> None:
    """Record each missing clip with Kokoro, as the demo's clips are, and remove the ones no longer played."""
    from voce import voices
    from voce.state import State

    missing, unused = stale()
    for name in unused:
        (CLIPS / name).unlink()
    if not missing:
        return
    CLIPS.mkdir(parents=True, exist_ok=True)
    texts = clips()
    voice = voices.make("kokoro", VOICE, State())
    try:
        with tempfile.TemporaryDirectory() as work:
            for name in missing:
                wav = voice.fetch(texts[name])
                tmp = Path(work) / name
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-ar", "24000", "-ac", "1",
                                "-b:a", "48k", str(tmp)], check=True)
                tmp.replace(CLIPS / name)
                print(f"  {name}  {texts[name]}")
    finally:
        voice.close()
    print(f"{len(missing)} clips recorded, {len(unused)} removed")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if the page or its clips differ, and write nothing")
    ap.add_argument("--record", action="store_true", help="also record missing clips with Kokoro (needs ffmpeg)")
    args = ap.parse_args()
    page = PAGE.read_text()
    new = rewrite(page)
    if args.check:
        missing, unused = stale()
        if new != page or missing or unused:
            print("site/index.html or its clips are out of date: run "
                  ".venv/bin/python docs/hearing/site_examples.py --record", file=sys.stderr)
            return 1
        return 0
    PAGE.write_text(new)
    print(f"{len(EXAMPLES)} languages written to {PAGE}")
    if args.record:
        record()
    else:
        missing, _ = stale()
        if missing:
            print(f"{len(missing)} lines have no clip yet: run again with --record")
    return 0


if __name__ == "__main__":
    sys.exit(main())

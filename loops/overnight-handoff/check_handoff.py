#!/usr/bin/env python3
"""Resume check: refuse to start a run if HANDOFF.md is malformed.

Usage: python3 check_handoff.py path/to/HANDOFF.md
Exit 0 and print the status if the file is well formed; exit 1 and list every problem if not.
Python 3.9+ standard library only. The runner imports check() from here.
"""
import re
import sys
from datetime import datetime

SECTIONS = ["State", "Done", "Next", "Open questions"]
FIELDS = ["Task", "Status", "Run", "Updated"]
STATUSES = {"in-progress", "done", "blocked"}
MAX_LINES = 150  # a handoff is a summary, not a diary; past this it is growing a history
MAX_BYTES = 16_000
EMPTY_ITEMS = {"(none)", "(none yet)"}


def _items(lines):
    """Non-empty lines of a list section, without the '- ' marker. Returns (items, bad_lines)."""
    items, bad = [], []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("- ") or s.startswith("- ["):
            items.append(s[2:].strip())
        else:
            bad.append(s)
    return items, bad


def _real(items):
    return [i for i in items if i.lower() not in EMPTY_ITEMS]


def check(text):
    """Return (problems, info). problems is a list of strings; info has the parsed fields."""
    problems, info = [], {}
    if len(text.encode("utf-8")) > MAX_BYTES:
        problems.append(f"file is over {MAX_BYTES} bytes")
    lines = text.splitlines()
    if len(lines) > MAX_LINES:
        problems.append(f"file has {len(lines)} lines; the limit is {MAX_LINES} (replace old State, don't append)")
    if "{{" in text or "}}" in text:
        problems.append("template placeholder {{...}} left in the file")

    first = next((l.strip() for l in lines if l.strip()), "")
    if first != "# Handoff":
        problems.append("first line must be '# Handoff'")

    # Header fields: everything before the first '## ' heading.
    head_end = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    for name in FIELDS:
        hits = [l for l in lines[:head_end] if re.match(rf"^{re.escape(name)}:\s", l + " ")]
        if len(hits) != 1:
            problems.append(f"header field '{name}:' must appear exactly once before the first section (found {len(hits)})")
            continue
        info[name] = hits[0].split(":", 1)[1].strip()
        if not info[name]:
            problems.append(f"header field '{name}:' is empty")

    status = info.get("Status")
    if status is not None and status not in STATUSES:
        problems.append(f"Status is '{status}'; it must be one of {', '.join(sorted(STATUSES))}")
    run = info.get("Run")
    if run is not None and not re.fullmatch(r"\d+", run):
        problems.append(f"Run is '{run}'; it must be a whole number")
    updated = info.get("Updated")
    if updated:
        try:
            datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except ValueError:
            problems.append(f"Updated is '{updated}'; it must be an ISO 8601 time such as 2026-11-02T22:00:00Z")

    # Sections: exactly these four, once each, in this order, and nothing else.
    found = [(i, l[3:].strip()) for i, l in enumerate(lines) if l.startswith("## ")]
    names = [n for _, n in found]
    for extra in [n for n in names if n not in SECTIONS]:
        problems.append(f"unexpected section '## {extra}'")
    for name in SECTIONS:
        if names.count(name) != 1:
            problems.append(f"section '## {name}' must appear exactly once (found {names.count(name)})")
    if [n for n in names if n in SECTIONS] != SECTIONS and all(names.count(n) == 1 for n in SECTIONS):
        problems.append("sections must be in this order: " + ", ".join(SECTIONS))

    body = {}
    for k, (start, name) in enumerate(found):
        end = found[k + 1][0] if k + 1 < len(found) else len(lines)
        body[name] = lines[start + 1:end]

    if "State" in body and not any(l.strip() for l in body["State"]):
        problems.append("State is empty")
    parsed = {}
    for name in ("Done", "Next", "Open questions"):
        if name not in body:
            continue
        items, bad = _items(body[name])
        parsed[name] = items
        for b in bad:
            problems.append(f"'{name}' has a line that is not a '- ' list item: {b[:60]}")
        if not items:
            problems.append(f"'{name}' has no items (write '- (none)' if there are none)")

    if status == "in-progress" and "Next" in parsed and not _real(parsed["Next"]):
        problems.append("Status is in-progress but Next lists nothing to do")
    if status == "blocked" and "Open questions" in parsed and not _real(parsed["Open questions"]):
        problems.append("Status is blocked but Open questions is empty; say what a person must answer")

    info["next"] = _real(parsed.get("Next", []))
    return problems, info


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        text = open(argv[1], encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"MALFORMED {argv[1]}: cannot read it ({e})")
        return 1
    problems, info = check(text)
    if problems:
        print(f"MALFORMED {argv[1]}:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK status={info['Status']} run={info['Run']} next={len(info['next'])} item(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""Hook 3, big-file-guard. PreToolUse, matcher "Bash".

Before any git add, ask git which files it would add (git add --dry-run, which changes nothing)
and block if one is over the limit. Exit 2 blocks the command.
"""
import json
import os
import re
import subprocess
import sys

LIMIT_MB = 5

data = json.load(sys.stdin)
inp = data.get("tool_input") if isinstance(data, dict) else None
inp = inp if isinstance(inp, dict) else {}
cmd = str(inp.get("command") or "")


def words(part):
    # Split like a shell for the simple cases: 'single', "double" and bare words.
    return [a or b or c for a, b, c in re.findall(r"'([^']*)'|\"([^\"]*)\"|(\S+)", part)]


adds = [w[2:] for w in map(words, re.split(r"&&|\|\||;|\||\n", cmd)) if w[:2] == ["git", "add"]]
out = "".join(subprocess.run(["git", "add", "--dry-run", *a], capture_output=True, text=True).stdout
              for a in adds)
big = [f"{f} ({os.path.getsize(f) / 1048576:.0f} MB)"
       for f in re.findall(r"^add '(.+)'$", out, re.M)
       if os.path.isfile(f) and os.path.getsize(f) > LIMIT_MB * 1048576]
if big:
    print(f"Blocked by big-file-guard: over {LIMIT_MB} MB: " + ", ".join(big)
          + ". Add it to .gitignore or use Git LFS.", file=sys.stderr)
    sys.exit(2)

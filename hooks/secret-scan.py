#!/usr/bin/env python3
"""Hook 2, secret-scan. PreToolUse, matcher "Bash".

Before any git commit, scan every change that could be committed (staged, unstaged and new
untracked files) for strings that look like secrets. Exit 2 blocks the command, and Claude
sees the message on stderr.
"""
import json
import os
import re
import subprocess
import sys

PATTERNS = {
    "AWS access key": r"AKIA[0-9A-Z]{16}",
    "GitHub token": r"gh[pousr]_[A-Za-z0-9]{36}",
    "private key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "API key": r"sk-[A-Za-z0-9_-]{20,}",
}

cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
# "git ... commit" anywhere, so git -c x=y commit, git -C dir commit and git  commit count too.
if not re.search(r"\bgit\b.*\bcommit\b", cmd, re.S):
    sys.exit(0)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


text = git("diff", "--cached", "-U0") + git("diff", "-U0")
for path in git("ls-files", "-o", "--exclude-standard").splitlines():
    if os.path.isfile(path):
        text += "".join("+" + line + "\n" for line in open(path, errors="ignore").read().splitlines())
added = "\n".join(line for line in text.splitlines() if line.startswith("+"))

hits = [name for name, pattern in PATTERNS.items() if re.search(pattern, added)]
if hits:
    print("Blocked by secret-scan: the commit would include " + ", ".join(hits)
          + ". Move it to an untracked .env file and use an environment variable.", file=sys.stderr)
    sys.exit(2)

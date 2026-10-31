#!/bin/bash
# PreToolUse hook: blocks dangerous shell commands no matter what Claude decides.
# CLAUDE.md is context, not enforced configuration; a hook is enforced (https://code.claude.com/docs/en/memory).
# Exit code 2 blocks the tool call and shows stderr to Claude. Any other failure here also blocks.
# Needs bash and python3. Make it executable: chmod +x .claude/hooks/block-dangerous.sh
python3 -c '
import sys, json, re
try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    print("hook could not read the command", file=sys.stderr); sys.exit(2)
rules = [
    r"\brm\s+(?=(?:[^;&|]*\s)?-[a-zA-Z]*[rR])(?=(?:[^;&|]*\s)?-[a-zA-Z]*f)[^;&|]*\s(/|/\*|~|~/|~/\*|\*|\.|\./)(?=\s|$|[;&|])",
    r"\bgit\s+push\b[^;&|]*(\s-f\b|\s--force|\s\+\S)",
    r"\.env\b",
]
for r in rules:
    if re.search(r, cmd):
        print("Blocked by .claude/hooks/block-dangerous.sh: " + cmd, file=sys.stderr); sys.exit(2)
'
s=$?
[ "$s" -eq 0 ] && exit 0
exit 2

#!/bin/bash
# PreToolUse hook: blocks dangerous shell commands no matter what Claude decides.
# CLAUDE.md is context, not enforced configuration; a hook is enforced (https://code.claude.com/docs/en/memory).
# Exit code 2 blocks the tool call and shows stderr to Claude.
cmd=$(python3 -c 'import sys,json; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))')
if echo "$cmd" | grep -Eq 'rm -rf (/|~|\*|\.)( |$)|git push (-f|--force)|cat .*\.env'; then
  echo "Blocked by .claude/hooks/block-dangerous.sh: $cmd" >&2
  exit 2
fi
exit 0

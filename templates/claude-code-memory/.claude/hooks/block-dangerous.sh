#!/bin/bash
# PreToolUse hook: blocks dangerous shell commands no matter what Claude decides.
# CLAUDE.md is context, not enforced configuration; a hook is enforced (https://code.claude.com/docs/en/memory).
# Exit code 2 blocks the tool call and shows stderr to Claude. Any other failure here also blocks.
# Needs bash and python3. Make it executable: chmod +x .claude/hooks/block-dangerous.sh
# A guardrail, not a sandbox: it parses the command like a shell, but a determined script can still hide a command.
python3 "$(dirname "$0")/block_dangerous.py"
s=$?
[ "$s" -eq 0 ] && exit 0
exit 2

#!/bin/bash
# PreToolUse hook for Edit|Write. Based on https://code.claude.com/docs/en/hooks-guide
# Blocks edits to protected files. Exit 2 blocks; stderr becomes Claude's feedback.
# Make executable once: chmod +x .claude/hooks/protect-files.sh
# Needs jq.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Normalize Windows backslash separators so the patterns below match
FILE_PATH="${FILE_PATH//\\//}"

PROTECTED_PATTERNS=(".env" "package-lock.json" ".git/")

for pattern in "${PROTECTED_PATTERNS[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    echo "Blocked: $FILE_PATH matches protected pattern '$pattern'" >&2
    exit 2
  fi
done

exit 0

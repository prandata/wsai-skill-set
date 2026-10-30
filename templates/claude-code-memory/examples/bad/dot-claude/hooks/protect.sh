#!/bin/bash
# BAD EXAMPLE. Each problem is explained in docs/claude-code-memory-deep-dive.md, section 4.3.
# 1. Extra stdout before the JSON, so the JSON is read as plain text and ignored.
# 2. permissionDecision at the top level instead of inside hookSpecificOutput.
# 3. exit 1, which is a non-blocking error. The edit still goes ahead.
echo "checking..."
if grep -q ".env"; then
  echo '{"permissionDecision": "deny"}'
  exit 1
fi

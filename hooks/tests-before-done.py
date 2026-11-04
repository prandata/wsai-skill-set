#!/usr/bin/env python3
"""Hook 4, tests-before-done. Stop hook.

When Claude says it is done, run the tests. If they fail, exit 2: Claude Code sends Claude back
to work with the failure. stop_hook_active is true when Claude is already continuing because of
a Stop hook, so the hook lets it stop then, and it cannot loop.

The test command is TEST_CMD from the environment Claude Code starts in, else "npm test --silent".
With the default command and no package.json, the hook does nothing.
"""
import json
import os
import subprocess
import sys

data = json.load(sys.stdin)
if isinstance(data, dict) and data.get("stop_hook_active") is True:
    sys.exit(0)
test = os.environ.get("TEST_CMD", "npm test --silent")
if test == "npm test --silent" and not os.path.isfile("package.json"):
    sys.exit(0)
r = subprocess.run(test, shell=True, capture_output=True, text=True)
if r.returncode == 0:
    sys.exit(0)
out = [line for line in (r.stdout + r.stderr).splitlines() if line.strip()]
keep = [line for line in out
        if line.strip().startswith(("✖", "not ok", "actual:", "expected:", "ℹ fail", "ℹ pass"))][:8]
print("Blocked by tests-before-done: tests fail, keep going.\n" + "\n".join(keep or out[:8]), file=sys.stderr)
sys.exit(2)

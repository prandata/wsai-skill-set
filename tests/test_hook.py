"""Feeds each case to the hook as JSON on stdin and checks its exit code. Nothing in the cases is executed."""
import json, os, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
hook = os.path.join(here, "..", "templates", "claude-code-memory", ".claude", "hooks", "block-dangerous.sh")
cases = json.load(open(os.path.join(here, "hook_cases.json")))


def code(stdin, env=None):
    return subprocess.run(["/bin/bash", hook], input=stdin, capture_output=True, text=True, env=env).returncode


fails = 0
for want, items in (("block", cases["block"]), ("allow", cases["allow"])):
    for c in items:
        got = code(json.dumps({"tool_input": {"command": c}}))
        ok = (got == 2) if want == "block" else (got == 0)
        fails += not ok
        print(f"{'ok ' if ok else 'BAD'} {want:5} exit={got} {c}")
got = code("not json")
fails += got != 2
print(f"{'ok ' if got == 2 else 'BAD'} block exit={got} <invalid JSON>")
got = code(json.dumps({"tool_input": {"command": "ls"}}), env={"PATH": "/nonexistent"})
fails += got != 2
print(f"{'ok ' if got == 2 else 'BAD'} block exit={got} <python3 missing>")
print(f"{fails} failed")
sys.exit(1 if fails else 0)

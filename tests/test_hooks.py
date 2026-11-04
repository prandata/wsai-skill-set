"""Offline tests for the hooks in hooks/ (hooks 2 to 5; hook 1 is tests/test_hook.py).

Each case builds a throwaway git repo in a temporary folder, feeds the hook the JSON Claude Code
would send on stdin, and checks the exit code (2 blocks, 0 allows). Nothing reaches the network.
The AWS key is the example access key ID from AWS's own docs, assembled at run time so
this file holds no key-shaped string. The 60 MB file is sparse: it takes no disk space.
Run: python3 tests/test_hooks.py   (HOOKS_DIR=<folder> tests another copy of the same four files)
"""
import json, os, shutil, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
hooks = os.environ.get("HOOKS_DIR") or os.path.join(here, "..", "hooks")
tmp = tempfile.mkdtemp(prefix="wsai-hooks-test-")
env0 = {k: v for k, v in os.environ.items() if k != "TEST_CMD"}
env0.update(HOME=tmp, GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="demo", GIT_AUTHOR_EMAIL="demo@example.com",
            GIT_COMMITTER_NAME="demo", GIT_COMMITTER_EMAIL="demo@example.com")
fails = total = 0

CART = "export function total(items) {\n  return items.reduce((sum, i) => sum + i.price * i.qty, 0);\n}\n"
CART_TEST = ('import { test } from "node:test";\nimport assert from "node:assert";\nimport { total } from "./cart.js";\n'
             'test("total adds price times qty", () => {\n'
             '  assert.equal(total([{ price: 5, qty: 2 }, { price: 1, qty: 3 }]), 13);\n});\n')
AWS_EXAMPLE = "AKIA" + "IOSFODNN7EXAMPLE"


def repo(name, files=None):
    """A demo project like the Short's: package.json, cart.js and its test, committed; then extra files, uncommitted."""
    d = os.path.join(tmp, name)
    os.makedirs(d)
    base = {"package.json": '{ "name": "demo-shop", "version": "1.0.0", "type": "module", "scripts": { "test": "node --test" } }\n',
            "cart.js": CART, "cart.test.js": CART_TEST, ".gitignore": "node_modules/\n.env\n"}
    for f, body in base.items():
        open(os.path.join(d, f), "w").write(body)
    for c in (["git", "init", "-q", "-b", "main"], ["git", "add", "-A"], ["git", "commit", "-qm", "demo shop"]):
        subprocess.run(c, cwd=d, env=env0, check=True)
    for f, body in (files or {}).items():
        os.makedirs(os.path.dirname(os.path.join(d, f)), exist_ok=True)
        open(os.path.join(d, f), "w").write(body)
    return d


def check(label, hook, cwd, payload, want, env=None, stderr_has=None):
    global fails, total
    r = subprocess.run([sys.executable, os.path.join(hooks, hook)], input=json.dumps(payload), capture_output=True,
                       text=True, cwd=cwd, env={**env0, **(env or {})})
    ok = r.returncode == want and (stderr_has is None or stderr_has in r.stderr)
    total += 1
    fails += not ok
    first = (r.stderr.strip().splitlines() or [""])[0][:100]
    print(f"{'ok ' if ok else 'BAD'} {hook:22} exit={r.returncode} want={want} {label}" + (f"  | {first}" if first else ""))


def bash(c):
    return {"tool_name": "Bash", "tool_input": {"command": c}}


# Hook 2, secret-scan. The Short: "Claude went to commit a file with an AWS key. The commit never ran."
config_js = f'export const config = {{\n  region: "ap-southeast-2",\n  accessKeyId: "{AWS_EXAMPLE}",\n}};\n'
s = repo("secret", {"config.js": config_js})
check('the Short\'s run: git add config.js && git commit -m "add export config"', "secret-scan.py", s,
      bash('git add config.js && git commit -m "add export config"'), 2, stderr_has="AWS access key")
for c in ["git commit -am x", "cd . && git commit -m x", "git -c user.name=a commit -m x", "git -C . commit -m x",
          "git  commit -m x"]:
    check(c, "secret-scan.py", s, bash(c), 2)
check("not a commit: git status", "secret-scan.py", s, bash("git status"), 0)
check("not a commit: grep the file", "secret-scan.py", s, bash("grep -n accessKeyId config.js"), 0)
subprocess.run(["git", "add", "config.js"], cwd=s, env=env0, check=True)
check("key already staged: git commit -m x", "secret-scan.py", s, bash("git commit -m x"), 2)
for name, line in [("GitHub token", "ghp_" + "a" * 36), ("private key", "-----BEGIN OPENSSH " + "PRIVATE KEY-----"),
                   ("API key", "sk-" + "b" * 24)]:
    d = repo("secret-" + name.replace(" ", "-"), {"notes.txt": line + "\n"})
    check(f"{name} in a new file (untracked files count, on purpose)", "secret-scan.py", d, bash("git commit -m x"), 2,
          stderr_has=name)
check("clean change: git commit -m x", "secret-scan.py", repo("secret-clean", {"version.js": "export const v = 2;\n"}),
      bash("git add version.js && git commit -m x"), 0)
# known gap, listed in hooks/README.md: it scans the project folder, not the folder git -C names
other = os.path.join(s, "other")
os.makedirs(other)
subprocess.run(["git", "init", "-q", "-b", "main"], cwd=other, env=env0, check=True)
open(os.path.join(other, "c.txt"), "w").write(f"k={AWS_EXAMPLE}\n")
check("known gap: git -C other commit, the key only in other/", "secret-scan.py",
      repo("secret-gap"), bash(f"git -C {other} commit -am x"), 0)

# Hook 3, big-file-guard. The Short: "It caught a sixty megabyte dump before it reached git."
b = repo("big", {"version.js": "export const v = 2;\n"})
os.makedirs(os.path.join(b, "data"))
with open(os.path.join(b, "data", "orders-dump.sql"), "wb") as f:
    f.truncate(60 * 1048576)
check('the Short\'s run: git add data version.js && git commit -m "snapshot"', "big-file-guard.py", b,
      bash('git add data version.js && git commit -m "snapshot"'), 2, stderr_has="data/orders-dump.sql (60 MB)")
for c, w in [("git add -A", 2), ("git add .", 2), ("git add -f data/orders-dump.sql", 2), ('git add "data"', 2),
             ("git status; git add data", 2), ("git status\ngit add data", 2), ("git add *.sql", 2),
             ("git add version.js", 0), ("git status", 0),
             # known gaps, listed in hooks/README.md: the hook checks from the project folder only
             ("cd data && git add orders-dump.sql", 0), ("git -C . add data", 0)]:
    check(c, "big-file-guard.py", b, bash(c), w)
status = subprocess.run(["git", "status", "--porcelain"], cwd=b, env=env0, capture_output=True, text=True).stdout
total += 1
ok = "A  data/orders-dump.sql" not in status
fails += not ok
print(f"{'ok ' if ok else 'BAD'} {'big-file-guard.py':22} the dry run staged nothing (git status has no 'A  data/')")

# Hook 4, tests-before-done. The Short: "Claude said done. The hook ran the tests, one failed, so Claude went back."
t = repo("tests")
stop = {"hook_event_name": "Stop", "stop_hook_active": False}
fail_cmd = {"TEST_CMD": f"{sys.executable} -c \"print('not ok 1 - total adds price times qty'); raise SystemExit(1)\""}
pass_cmd = {"TEST_CMD": f"{sys.executable} -c \"print('ok 1')\""}
check("failing tests (TEST_CMD)", "tests-before-done.py", t, stop, 2, env=fail_cmd, stderr_has="tests fail, keep going")
check("failing tests, stop_hook_active true: lets Claude stop, no loop", "tests-before-done.py", t,
      {"hook_event_name": "Stop", "stop_hook_active": True}, 0, env=fail_cmd)
check("green tests (TEST_CMD)", "tests-before-done.py", t, stop, 0, env=pass_cmd)
check("failure output matches no pattern: still blocks", "tests-before-done.py", t, stop, 2,
      env={"TEST_CMD": f"{sys.executable} -c \"print('boom'); raise SystemExit(3)\""}, stderr_has="boom")
nopkg = os.path.join(tmp, "nopkg")
os.makedirs(nopkg)
check("default command, no package.json: does nothing", "tests-before-done.py", nopkg, stop, 0)
if shutil.which("npm") and shutil.which("node"):
    check("npm: tests green", "tests-before-done.py", t, stop, 0)
    open(os.path.join(t, "cart.js"), "w").write(CART.replace("function total", "function sum"))
    check("npm, the Short's run: total renamed to sum, cart.test.js still imports total", "tests-before-done.py", t,
          stop, 2, stderr_has="tests fail, keep going")
else:
    print("skip npm cases: npm or node not on PATH")

# Hook 5, env-guard. The Short: "Claude tried to read dot env. Blocked, so the password stayed put."
e = repo("env")
check('the Short\'s run: grep -E "^DATABASE_URL" .env', "env-guard.py", e, bash('grep -E "^DATABASE_URL" .env'), 2,
      stderr_has="env-guard")
for c, w in [("cat .env", 2), ("cat ./.env", 2), ("cat .env.local", 2), ("cat .env.production.local", 2),
             ("cat .env.example.local", 2), ("cat .env*", 2), ("cat .env?", 2),
             ("cat .ENV", 2), ("sed -n 1p .env", 2), ("source .env", 2), ("cat .env.example", 0), ("ls -a", 0),
             ("cat env.js", 0), ("cat .envrc", 0),
             # known gaps, listed in hooks/README.md: a command that never names the file
             ("cat .en?", 0), ("grep -r DATABASE_URL .", 0)]:
    check(c, "env-guard.py", e, bash(c), w)
for tool, path, w in [("Read", "/x/.env", 2), ("Edit", "/x/.env", 2), ("Write", "/x/.env.production", 2),
                      ("Read", "/x/.env.example", 0), ("Read", "/x/cart.js", 0)]:
    check(f"{tool} {path}", "env-guard.py", e, {"tool_name": tool, "tool_input": {"file_path": path}}, w)

# Odd input: Claude Code always sends an object, but a hook must not crash on null or a non-string value.
for hook, payload in [("secret-scan.py", {"tool_input": None}), ("big-file-guard.py", {"tool_input": None}),
                      ("env-guard.py", {"tool_input": None}), ("env-guard.py", {"tool_input": {"command": 7}}),
                      ("secret-scan.py", {"tool_input": {"command": ["git", "commit"]}}), ("big-file-guard.py", [])]:
    check(f"odd input {json.dumps(payload)}: no crash", hook, e, payload, 0)
check('odd input stop_hook_active "false" (a string): still runs the tests', "tests-before-done.py", t,
      {"stop_hook_active": "false"}, 2, env=fail_cmd)
check("odd input [] to the Stop hook: still runs the tests", "tests-before-done.py", t, [], 2, env=fail_cmd)

# settings.json registers all five hooks on the events the README names.
cfg = json.load(open(os.path.join(here, "..", "hooks", "settings.json")))["hooks"]
reg = {(ev, m.get("matcher", ""), h["command"].rsplit("/", 1)[1]) for ev, ms in cfg.items() for m in ms for h in m["hooks"]}
want = {("PreToolUse", "Bash", "block-dangerous.sh"), ("PreToolUse", "Bash", "secret-scan.py"),
        ("PreToolUse", "Bash", "big-file-guard.py"), ("PreToolUse", "Read|Edit|Write|Bash", "env-guard.py"),
        ("Stop", "", "tests-before-done.py")}
total += 1
fails += reg != want
print(f"{'ok ' if reg == want else 'BAD'} settings.json registers {len(reg)} hooks: {sorted(x[2] for x in reg)}")

shutil.rmtree(tmp)
print(f"{fails} failed of {total}")
sys.exit(1 if fails else 0)

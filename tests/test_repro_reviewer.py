"""Offline checks for agents/repro-reviewer.

1. The subagent file has the frontmatter Claude Code needs and no write tools.
2. make-sample-repo.sh builds the same commit SHAs every time.
3. Each planted problem is what the README says it is, and the sample repo's own tests miss all three.
4. Each saved example log ends with the verdict the README states, at the branch's SHA.

No network, no Claude Code. Run: python3 tests/test_repro_reviewer.py
"""
import os, re, shutil, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
agent_dir = os.path.join(here, "..", "agents", "repro-reviewer")
examples = os.path.join(agent_dir, "examples")

SHAS = {
    "main": "241e4554feee3a29ee19618fb4640a6060bcc2f2",
    "real-bug": "8bc7eded2f4b0ea4f940d16a09c118fcc7f4b536",
    "false-alarm": "89771d2e319f29156908bdfe2e7043b487f870f4",
    "cannot-run": "2f9054ff88f4356a8104284af72eea582cdf8316",
}
LOGS = {"01-real-bug": ("real-bug", "FIX"), "02-false-alarm": ("false-alarm", "PASS"),
        "03-cannot-run": ("cannot-run", "FIX")}

fails = 0


def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))
    fails += not ok


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True).stdout.strip()


def py(repo, code):
    r = subprocess.run([sys.executable, "-I", "-c", "import sys; sys.path.insert(0, '.')\n" + code],
                       cwd=repo, capture_output=True, text=True)
    return r.returncode, r.stdout.strip()


# 1. the definition
text = open(os.path.join(agent_dir, "repro-reviewer.md")).read()
check("file starts with ---", text.startswith("---\n"))
front = text.split("---\n")[1]
fields = dict(line.split(":", 1) for line in front.strip().split("\n"))
check("name is repro-reviewer", fields.get("name", "").strip() == "repro-reviewer")
check("description present", len(fields.get("description", "").strip()) > 40)
tools = [t.strip() for t in fields.get("tools", "").split(",")]
check("tools are Read, Grep, Glob, Bash", tools == ["Read", "Grep", "Glob", "Bash"], str(tools))
check("no Edit or Write tool", not {"Edit", "Write", "NotebookEdit"} & set(tools))
check("verdict lines in prompt", "VERDICT: PASS @ <sha>" in text and "VERDICT: FIX @ <sha>" in text)

for root, _, files in os.walk(agent_dir):
    for f in files:
        p = os.path.join(root, f)
        check(f"no em dash in {os.path.relpath(p, agent_dir)}", "\u2014" not in open(p, encoding="utf-8").read())

# 2. deterministic sample repo
tmp = tempfile.mkdtemp(prefix="repro-reviewer-test-")
try:
    a, b = os.path.join(tmp, "a"), os.path.join(tmp, "b")
    for d in (a, b):
        subprocess.run(["bash", os.path.join(examples, "make-sample-repo.sh"), d], capture_output=True, check=True)
    for branch, sha in SHAS.items():
        check(f"{branch} SHA is {sha[:12]}", git(a, "rev-parse", branch) == sha == git(b, "rev-parse", branch),
              git(a, "rev-parse", branch))
    r = subprocess.run(["bash", os.path.join(examples, "make-sample-repo.sh"), a], capture_output=True, text=True)
    check("refuses a non-empty folder", r.returncode == 2)

    # 3. planted problems, and the repo's own tests miss them
    for branch in SHAS:
        git(a, "checkout", "-q", branch)
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                           cwd=a, capture_output=True, text=True)
        check(f"{branch}: sample tests pass", r.returncode == 0, r.stderr[-300:])
        if branch == "real-bug":
            rc, out = py(a, "from tinyshop.pricing import split_bill as s; print(sum(s(100, 3)), sum(s(200, 3)))")
            check("real-bug: shares miss the total (99, 201)", (rc, out) == (0, "99 201"), out)
        if branch == "false-alarm":
            rc, out = py(a, "from tinyshop.durations import parse_duration as p; print(p('90s'))")
            check("false-alarm: '90s' is 90, the bot claim is false", (rc, out) == (0, "90"), out)
        if branch == "cannot-run":
            rc, out = py(a, "from tinyshop.links import download_link\n"
                            "class S:\n    def generate_presigned_url(self, op, Params, ExpiresIn): return ExpiresIn\n"
                            "print(download_link(S(), 'b', 'k'))")
            check("cannot-run: default expiry 2592000 s, over S3's 604800", (rc, out) == (0, "2592000"), out)
finally:
    shutil.rmtree(tmp)

# 4. saved logs
for name, (branch, verdict) in LOGS.items():
    log = open(os.path.join(examples, name + ".log")).read()
    lines = [l for l in log.strip().split("\n") if l.strip()]
    check(f"{name}: header names {branch} @ SHA", f"branch {branch} @ {SHAS[branch]}" in log)
    check(f"{name}: ends with VERDICT: {verdict} @ SHA", lines[-1] == f"VERDICT: {verdict} @ {SHAS[branch]}", lines[-1])
    check(f"{name}: has a Not run section", "## Not run" in log)
    check(f"{name}: no home or temp paths", not re.search(r"/Users/|/home/|/var/folders/", log))

print("failures:", fails)
sys.exit(1 if fails else 0)

"""Offline tests for loops/overnight-handoff (the resume check and the runner's stop rules).

The runner is pointed at a fake `claude` (a small Python script) so nothing calls a model,
spends money or touches the network. Everything happens in a temporary folder that is deleted
at the end. Run: python3 tests/test_overnight_handoff.py
"""
import json, os, shutil, subprocess, sys, tempfile, time

here = os.path.dirname(os.path.abspath(__file__))
loop = os.path.join(here, "..", "loops", "overnight-handoff")
sys.dont_write_bytecode = True
sys.path.insert(0, loop)
from check_handoff import check  # noqa: E402

FAKE = r'''#!/usr/bin/env python3
import json, os, re, signal, sys, time
mode = os.environ["FAKE_MODE"]
with open(os.environ["FAKE_LOG"], "a") as f:
    f.write(json.dumps(sys.argv[1:]) + "\n")
def result(subtype="success", code=0):
    print(json.dumps({"type": "result", "subtype": subtype, "is_error": subtype != "success",
                      "num_turns": 3, "total_cost_usd": 0.01, "session_id": "fake"}))
    sys.exit(code)
h = open("HANDOFF.md").read()
run = int(re.search(r"^Run: (\d+)", h, re.M).group(1)) + 1
if mode == "step":
    h = re.sub(r"^Run: \d+", f"Run: {run}", h, flags=re.M)
    h = h.replace("## Done\n\n- (none yet)", "## Done\n\n- step 1")
    h = h.replace("## Done\n\n", "## Done\n\n- another step\n", 1) if run > 1 else h
    open("HANDOFF.md", "w").write(h); result()
if mode == "done":
    h = re.sub(r"^Status: .*", "Status: done", h, flags=re.M)
    h = re.sub(r"## Next\n\n(- .*\n)+", "## Next\n\n- (none)\n", h)
    open("HANDOFF.md", "w").write(h); result()
if mode == "blocked":
    h = re.sub(r"^Status: .*", "Status: blocked", h, flags=re.M)
    h = h.replace("## Open questions\n\n- (none)", "## Open questions\n\n- Which file is the real config?")
    open("HANDOFF.md", "w").write(h); result()
if mode == "break":
    open("HANDOFF.md", "w").write("# Handoff\n\nI got bored.\n"); result()
if mode == "noop":
    result()
if mode == "hang":
    def on_int(*_):
        h2 = re.sub(r"^Run: \d+", f"Run: {run}", h, flags=re.M)
        open("HANDOFF.md", "w").write(h2)
        result("error_during_execution", 130)
    signal.signal(signal.SIGINT, on_int)
    if os.environ.get("FAKE_IGNORE_INT"):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
    open("started", "w").write("1")
    time.sleep(120)
'''

TEMPLATE = open(os.path.join(loop, "HANDOFF.template.md")).read()
GOOD = TEMPLATE.replace("{{TASK}}", "Tidy the TODO list").replace("{{UPDATED}}", "2026-11-02T22:00:00Z")

tmp = tempfile.mkdtemp(prefix="overnight-handoff-test-")
fake = os.path.join(tmp, "fake-claude")
open(fake, "w").write(FAKE)
os.chmod(fake, 0o755)
fails = 0


def ok(name, cond, detail=""):
    global fails
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  [{detail}]"))
    fails += 0 if cond else 1


# ---- the resume check ---------------------------------------------------------------
def problems(text):
    return check(text)[0]


ok("template, filled in, is well formed", problems(GOOD) == [], problems(GOOD))
ok("unfilled template is refused", any("placeholder" in p for p in problems(TEMPLATE)))
ok("missing title", any("# Handoff" in p for p in problems(GOOD.replace("# Handoff", "# Notes"))))
ok("missing section", any("'## Next'" in p for p in problems(GOOD.replace("## Next", "## Later"))))
ok("unexpected section", any("unexpected" in p for p in problems(GOOD + "\n## History\n\nlots\n")))
ok("duplicate section", any("exactly once" in p for p in problems(GOOD + "\n## Done\n\n- again\n")))
swapped = GOOD.replace("## Done", "## TMP").replace("## Next", "## Done").replace("## TMP", "## Next")
ok("sections out of order", any("order" in p for p in problems(swapped)))
ok("bad status", any("Status is" in p for p in problems(GOOD.replace("Status: in-progress", "Status: nearly"))))
ok("run not a number", any("Run is" in p for p in problems(GOOD.replace("Run: 0", "Run: two"))))
ok("bad time", any("Updated is" in p for p in problems(GOOD.replace("2026-11-02T22:00:00Z", "last night"))))
ok("missing header field", any("'Task:'" in p for p in problems(GOOD.replace("Task: Tidy the TODO list\n", ""))))
ok("header field twice", any("'Run:'" in p for p in problems(GOOD.replace("Run: 0", "Run: 0\nRun: 1"))))
ok("empty State", any("State is empty" in p for p in problems(GOOD.replace("Not started. Nothing has been changed yet.", ""))))
ok("prose under Done", any("not a '- ' list item" in p for p in problems(GOOD.replace("- (none yet)", "I did some things"))))
ok("empty Next", any("no items" in p for p in problems(GOOD.replace("- Start with step 1 in the task file.", ""))))
ok("in-progress with nothing next", any("nothing to do" in p for p in problems(GOOD.replace("- Start with step 1 in the task file.", "- (none)"))))
ok("done with nothing next is fine", problems(GOOD.replace("Status: in-progress", "Status: done").replace("- Start with step 1 in the task file.", "- (none)")) == [])
ok("blocked without a question", any("blocked" in p for p in problems(GOOD.replace("Status: in-progress", "Status: blocked"))))
ok("blocked with a question is fine", problems(GOOD.replace("Status: in-progress", "Status: blocked").replace("- (none)\n", "- Which file?\n")) == [])
ok("too long", any("lines" in p for p in problems(GOOD.replace("Not started.", "x\n" * 200))))
ok("time with offset is fine", problems(GOOD.replace("22:00:00Z", "22:00:00+11:00")) == [])
r = subprocess.run([sys.executable, os.path.join(loop, "check_handoff.py"), os.path.join(tmp, "nope.md")], capture_output=True, text=True)
ok("CLI: missing file exits 1", r.returncode == 1 and "MALFORMED" in r.stdout, r.stdout)


# ---- the runner -------------------------------------------------------------------------
def workdir(handoff=GOOD):
    d = tempfile.mkdtemp(dir=tmp)
    shutil.copy(os.path.join(loop, "sample", "TASK.md"), d)
    if handoff is not None:
        open(os.path.join(d, "HANDOFF.md"), "w").write(handoff)
    return d


def runner(d, mode, *args, env_extra=None, timeout=60):
    logf = os.path.join(d, "fake.log")
    env = dict(os.environ, FAKE_MODE=mode, FAKE_LOG=logf, **(env_extra or {}))
    r = subprocess.run([sys.executable, os.path.join(loop, "run.py"), d, "--claude-bin", fake, *args],
                       capture_output=True, text=True, env=env, timeout=timeout)
    calls = [json.loads(l) for l in open(logf)] if os.path.exists(logf) else []
    return r, calls


d = workdir(handoff=None)
r, calls = runner(d, "step")
ok("no handoff and no --init: refused, claude not called", r.returncode == 2 and not calls, r.stdout)
r, calls = runner(d, "step", "--init", "--dry-run")
h = open(os.path.join(d, "HANDOFF.md")).read()
ok("--init creates a valid handoff with the task title", problems(h) == [] and "Task: Tidy the TODO list" in h, h)
ok("--dry-run calls nothing and prints the command", r.returncode == 0 and not calls and "--max-budget-usd" in r.stdout, r.stdout)

d = workdir(GOOD.replace("## Next", "## Later"))
r, calls = runner(d, "step")
ok("malformed handoff: refused before any call", r.returncode == 2 and not calls and "malformed" in r.stdout, r.stdout)

d = workdir()
r, calls = runner(d, "step", "--max-sessions", "1")
ok("one session runs, then stops at the session limit", r.returncode == 0 and len(calls) == 1, r.stdout)
a = calls[0] if calls else []
ok("flags: json output, budget, turns, no prompts", all(x in a for x in ["--output-format", "--max-budget-usd", "--max-turns", "--permission-prompts", "--no-session-persistence"]), a)
ok("flags: no shell tool for the agent", "--tools" in a and "Bash" not in a[a.index("--tools") + 1].split(",") and "Bash" in a, a)
d2 = workdir()
r2, c2 = runner(d2, "step", "--max-sessions", "1", "--tools", "Read,Edit,Write,Bash")
b = c2[0] if c2 else []
ok("Bash added on purpose: warned, and not also disallowed", "Bash is enabled" in r2.stdout and b and "Bash" not in b[b.index("--disallowedTools"):b.index("--permission-mode")], b)
ok("prompt names the handoff and the run number", any("HANDOFF.md" in x and "session 1 " in x for x in a), a)
rec = [json.loads(l) for l in open(os.path.join(d, ".overnight", "runs.jsonl"))]
ok("runs.jsonl records the session", rec and rec[-1]["outcome"] == "success" and rec[-1]["handoff_changed"], rec)
r, calls = runner(d, "step", "--max-sessions", "1")
ok("second invocation resumes at run 2 and is told how run 1 ended", any("session 2 " in x and "session 1 ended with 'success'" in x for x in calls[-1]), calls[-1][2][:200] if calls else "")

d = workdir()
r, calls = runner(d, "done")
ok("done: loop stops after the session that finished, no further call", r.returncode == 0 and len(calls) == 1 and "DONE" in r.stdout, r.stdout)
r, calls = runner(d, "done")
ok("done handoff: next invocation calls nothing", r.returncode == 0 and len(calls) == 1, r.stdout)

d = workdir()
r, calls = runner(d, "blocked")
ok("blocked: exit 3 and no further call", r.returncode == 3 and len(calls) == 1, r.stdout)

d = workdir()
r, calls = runner(d, "break")
ok("agent breaks the handoff: exit 2, no further call", r.returncode == 2 and len(calls) == 1, r.stdout)

d = workdir()
r, calls = runner(d, "noop")
ok("no progress: exit 4 after one call", r.returncode == 4 and len(calls) == 1, r.stdout)

d = workdir()
open(os.path.join(d, "STOP"), "w").close()
r, calls = runner(d, "step")
ok("STOP file before start: nothing runs", r.returncode == 0 and not calls and "STOP" in r.stdout, r.stdout)

d = workdir()
r, calls = runner(d, "step", "--total-budget-usd", "0.50", "--budget-usd", "1.00")
ok("total budget smaller than one session: nothing runs", r.returncode == 0 and not calls, r.stdout)

d = workdir()
t = time.monotonic()
r, calls = runner(d, "hang", "--session-minutes", "0.05", "--max-sessions", "1", "--grace-seconds", "5")
ok("time limit: SIGINT ends the session cleanly", "time limit" in r.stdout and "error_during_execution" not in r.stdout.split("ended")[0] and time.monotonic() - t < 30, r.stdout)
rec = [json.loads(l) for l in open(os.path.join(d, ".overnight", "runs.jsonl"))]
ok("time limit is recorded as the outcome", rec[-1]["outcome"] == "time limit" and rec[-1]["exit"] == 130, rec)

d = workdir()
logf = os.path.join(d, "fake.log")
p = subprocess.Popen([sys.executable, os.path.join(loop, "run.py"), d, "--claude-bin", fake, "--grace-seconds", "5"],
                     stdout=subprocess.PIPE, text=True, env=dict(os.environ, FAKE_MODE="hang", FAKE_LOG=logf))
for _ in range(100):
    if os.path.exists(os.path.join(d, "started")):
        break
    time.sleep(0.1)
open(os.path.join(d, "STOP"), "w").close()
out = p.communicate(timeout=30)[0]
ok("STOP file mid-session: SIGINT, clean exit 0, handoff kept", p.returncode == 0 and "STOP file" in out and "Run: 1" in open(os.path.join(d, "HANDOFF.md")).read(), out)

d = workdir()
t = time.monotonic()
r, calls = runner(d, "hang", "--session-minutes", "0.05", "--max-sessions", "1", "--grace-seconds", "2",
                  env_extra={"FAKE_IGNORE_INT": "1"})
rec = [json.loads(l) for l in open(os.path.join(d, ".overnight", "runs.jsonl"))]
ok("a session that ignores SIGINT is stopped with SIGTERM", rec[-1]["exit"] == -15 and time.monotonic() - t < 30, rec)
ok("a killed session with no result records its cost as unknown", rec[-1]["cost_usd"] is None and rec[-1]["subtype"] is None, rec)

shutil.rmtree(tmp)
print(f"\n{'all passed' if not fails else str(fails) + ' failed'}")
sys.exit(1 if fails else 0)

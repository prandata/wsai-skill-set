#!/usr/bin/env python3
"""Overnight agent loop with a handoff file.

Runs `claude -p` in fresh sessions, one after another, on one bounded task in one folder.
Every session starts from HANDOFF.md, not from the last transcript, and must keep HANDOFF.md
current after each step. The loop stops at the first of: the task is done, the agent says it is
blocked, a time limit, a spend limit, a session limit, a STOP file, or a session that made no
progress. Before every session the resume check runs; a malformed handoff stops the loop.

    python3 run.py WORKDIR --init --dry-run     # create HANDOFF.md, print the command, spend nothing
    python3 run.py WORKDIR                       # run until done or a limit
    touch WORKDIR/STOP                           # from another terminal: stop cleanly

Python 3.9+ standard library only. Exit codes: 0 done or stopped cleanly at a limit,
2 refused (missing or malformed handoff), 3 blocked (needs a person), 4 no progress, 1 error.
"""
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True  # no __pycache__ next to the scripts
sys.path.insert(0, HERE)
from check_handoff import check  # noqa: E402

PROMPT = """You are running unattended: session {run} of a task that may take several sessions.
Nobody can answer questions during this session. You have no memory of earlier sessions;
HANDOFF.md is the only record of them.

Previous session: {previous}
Current time (UTC): {now}

1. Read HANDOFF.md, then {task}. Do not redo anything listed under Done. An earlier session may
   have stopped in the middle of a step, so check the current state of the files before you change them.
2. Work through the steps in {task}, starting with the first item under Next. Edit only the files
   {task} names, plus HANDOFF.md.
3. After you finish EACH step, before you start the next one, rewrite HANDOFF.md:
   - keep the exact headings and header fields of the current file;
   - Status: in-progress, Run: {run}, Updated: {now};
   - State: two to five lines on where things stand now (replace the old text, do not append);
   - Done: add the step you finished; Next: what remains, in order;
   - Open questions: anything a person must decide, or "- (none)".
4. When every step is finished, set Status: done and Next to "- (none)".
   If you cannot go on without a person, set Status: blocked and write the question under Open questions.
5. Every line under Done, Next and Open questions starts with "- ". Keep HANDOFF.md under 100 lines.
"""


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def digest(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None


def read_handoff(path):
    try:
        return check(open(path, encoding="utf-8").read())
    except (OSError, UnicodeDecodeError) as e:
        return [f"cannot read {os.path.basename(path)}: {e}"], {}


def build_cmd(a, prompt):
    tools = a.tools.split(",")
    cmd = [a.claude_bin, "-p", prompt,
           "--output-format", "json",
           "--max-budget-usd", f"{a.budget_usd:.2f}",
           "--max-turns", str(a.max_turns),
           "--tools", a.tools,
           # A second lock on anything you did not ask for in --tools (a bare name in
           # --disallowedTools removes the tool even if --tools lists it, so skip those).
           "--disallowedTools", *[t for t in ("Bash", "WebFetch", "WebSearch") if t not in tools], "mcp__*",
           "--permission-mode", "acceptEdits",
           "--permission-prompts", "none",
           "--setting-sources", "project",
           "--strict-mcp-config",
           "--no-session-persistence"]
    if a.model:
        cmd += ["--model", a.model]
    return cmd


def stop_session(proc, grace):
    """SIGINT ends the turn cleanly; SIGTERM then SIGKILL only if it does not exit in time."""
    for sig, wait in ((signal.SIGINT, grace), (signal.SIGTERM, 10), (signal.SIGKILL, 5)):
        if proc.poll() is not None:
            return
        try:
            proc.send_signal(sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("workdir", help="folder the agent works in (its working directory)")
    p.add_argument("--task", default="TASK.md", help="task file inside WORKDIR (default TASK.md)")
    p.add_argument("--init", action="store_true", help="create HANDOFF.md from the template if it is missing")
    p.add_argument("--dry-run", action="store_true", help="run the resume check, print the command, call nothing")
    p.add_argument("--hours", type=float, default=8.0, help="wall-clock limit for the whole loop (default 8)")
    p.add_argument("--session-minutes", type=float, default=30.0, help="wall-clock limit per session (default 30)")
    p.add_argument("--budget-usd", type=float, default=1.00, help="--max-budget-usd per session (default 1.00)")
    p.add_argument("--total-budget-usd", type=float, default=5.00, help="stop before a session once this much is spent (default 5.00)")
    p.add_argument("--max-turns", type=int, default=40, help="--max-turns per session (default 40)")
    p.add_argument("--max-sessions", type=int, default=6, help="most sessions in one loop (default 6)")
    p.add_argument("--model", default=None, help="model alias or name; default is your Claude Code default")
    p.add_argument("--tools", default="Read,Edit,Write", help="built-in tools the agent gets (default Read,Edit,Write: no shell)")
    p.add_argument("--grace-seconds", type=float, default=30.0, help="wait after SIGINT before SIGTERM (default 30)")
    p.add_argument("--claude-bin", default="claude", help=argparse.SUPPRESS)  # tests swap in a fake
    a = p.parse_args(argv)

    work = os.path.abspath(a.workdir)
    task = os.path.join(work, a.task)
    handoff = os.path.join(work, "HANDOFF.md")
    stopfile = os.path.join(work, "STOP")
    logdir = os.path.join(work, ".overnight")
    if not os.path.isfile(task):
        log(f"REFUSED: no task file {a.task} in the work folder")
        return 2
    if "Bash" in a.tools.split(","):
        log("note: Bash is enabled. The loop never pushes, but the agent could; add your own deny rules.")

    if not os.path.exists(handoff):
        if not a.init:
            log("REFUSED: no HANDOFF.md. Run once with --init to create it from the template.")
            return 2
        tmpl = open(os.path.join(HERE, "HANDOFF.template.md"), encoding="utf-8").read()
        title = next((l.lstrip("# ").strip() for l in open(task, encoding="utf-8") if l.strip()), a.task)
        with open(handoff, "w", encoding="utf-8") as f:
            f.write(tmpl.replace("{{TASK}}", title).replace("{{UPDATED}}", now_utc()))
        log("created HANDOFF.md from the template")

    os.makedirs(logdir, exist_ok=True)
    runs_log = os.path.join(logdir, "runs.jsonl")
    previous = "none (this is the first session)"
    if os.path.exists(runs_log):
        last = [l for l in open(runs_log, encoding="utf-8") if l.strip()]
        if last:
            r = json.loads(last[-1])
            previous = f"session {r['run']} ended with '{r['outcome']}' after {r.get('num_turns')} turns"

    loop_deadline = time.monotonic() + a.hours * 3600
    spent = 0.0
    interrupted = {"sig": None}

    def on_signal(signum, _frame):
        interrupted["sig"] = signum
        log(f"got signal {signum}: ending the current session cleanly, then stopping")

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    for _ in range(a.max_sessions):
        problems, info = read_handoff(handoff)
        if problems:
            log("REFUSED: HANDOFF.md is malformed; fix it by hand, then run again:")
            for x in problems:
                log(f"  - {x}")
            return 2
        run = int(info["Run"]) + 1
        log(f"resume check OK: status={info['Status']} run={info['Run']} next={info['next'][:1]}")
        if info["Status"] == "done":
            log("DONE: the handoff says the task is finished. Nothing to run.")
            return 0
        if info["Status"] == "blocked":
            log("BLOCKED: the handoff has an open question for a person. Answer it in HANDOFF.md, set Status: in-progress, run again.")
            return 3
        if os.path.exists(stopfile):
            log("STOPPED: STOP file present. Delete it to run again.")
            return 0
        if interrupted["sig"]:
            log("STOPPED: interrupted.")
            return 0
        left = loop_deadline - time.monotonic()
        if left <= 60 and not a.dry_run:
            log("STOPPED: the loop's time limit is reached.")
            return 0
        if spent + a.budget_usd > a.total_budget_usd + 1e-9:
            log(f"STOPPED: spent ${spent:.2f}; another session could pass the ${a.total_budget_usd:.2f} total.")
            return 0

        prompt = PROMPT.format(run=run, previous=previous, now=now_utc(), task=a.task)
        cmd = build_cmd(a, prompt)
        if a.dry_run:
            shown = [c if c != prompt else "<prompt below>" for c in cmd]
            log("DRY RUN: would run, in " + os.path.basename(work) + "/:")
            print("  " + " ".join(json.dumps(c) if (" " in c or "*" in c) else c for c in shown))
            print("--- prompt ---\n" + prompt + "--- end ---")
            return 0

        session_deadline = time.monotonic() + min(a.session_minutes * 60, left - 30)
        before = digest(handoff)
        out_path = os.path.join(logdir, f"session-{run}.json")
        log(f"session {run}: starting (limits: {a.session_minutes:g} min, ${a.budget_usd:.2f}, {a.max_turns} turns)")
        started, started_at = time.monotonic(), now_utc()
        with open(out_path, "wb") as out:
            proc = subprocess.Popen(cmd, cwd=work, stdin=subprocess.DEVNULL, stdout=out,
                                    start_new_session=True)  # a terminal Ctrl-C reaches only us; we pass SIGINT on
            cause = None
            while proc.poll() is None:
                if time.monotonic() >= session_deadline:
                    cause = "time limit"
                elif os.path.exists(stopfile):
                    cause = "STOP file"
                elif interrupted["sig"]:
                    cause = "signal"
                if cause:
                    log(f"session {run}: {cause}; sending SIGINT and waiting up to {a.grace_seconds:g}s")
                    stop_session(proc, a.grace_seconds)
                    break
                time.sleep(1)
        code = proc.wait()

        result = {}
        try:
            result = json.load(open(out_path, encoding="utf-8"))
        except (OSError, ValueError):
            pass
        cost = result.get("total_cost_usd")
        spent += cost if isinstance(cost, (int, float)) else a.budget_usd  # unknown cost: assume the cap
        outcome = cause or result.get("subtype") or f"exit {code}"
        changed = digest(handoff) != before
        record = {"run": run, "started": started_at, "ended": now_utc(), "seconds": round(time.monotonic() - started),
                  "outcome": outcome, "subtype": result.get("subtype"), "exit": code, "num_turns": result.get("num_turns"),
                  "cost_usd": cost, "handoff_changed": changed}
        with open(runs_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        log(f"session {run}: ended '{outcome}' (result: {record['subtype']}) exit={code} turns={record['num_turns']} "
            f"cost={'$%.4f' % cost if isinstance(cost, (int, float)) else 'unknown'} handoff_changed={changed}")
        previous = f"session {run} ended with '{outcome}' after {record['num_turns']} turns"

        problems, info = read_handoff(handoff)
        if problems:
            log("REFUSED: the session left HANDOFF.md malformed; fix it by hand, then run again:")
            for x in problems:
                log(f"  - {x}")
            return 2
        log(f"handoff now: status={info['Status']} run={info['Run']} next={info['next'][:1]}")
        if cause in ("STOP file", "signal"):
            log(f"STOPPED: {cause}. The next run resumes from HANDOFF.md.")
            return 0
        if not changed:
            log("NO PROGRESS: the session did not update HANDOFF.md. Stopping so it does not loop; read "
                f".overnight/session-{run}.json.")
            return 4

    problems, info = read_handoff(handoff)
    status = info.get("Status")
    log(f"STOPPED: reached {a.max_sessions} session(s); handoff status={status}.")
    return {"blocked": 3}.get(status, 0)


if __name__ == "__main__":
    sys.exit(main())

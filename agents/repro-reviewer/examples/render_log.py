#!/usr/bin/env python3
"""Turn a `claude -p --output-format stream-json --verbose` run into a readable log.

Every tool call is printed in order with its input and the output the agent saw, then the agent's
final report. Paths given with --mask are replaced, and so is the per-user temp folder, so a log
carries no machine-specific paths. Long tool outputs are cut at 80 lines, marked with [...].
"""
import argparse, json, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("stream")
for opt in ("--name", "--branch", "--sha", "--prompt", "--started", "--exit", "--version"):
    ap.add_argument(opt, default="")
ap.add_argument("--mask", action="append", default=[], help="FROM=TO, longest first is applied first")
a = ap.parse_args()

masks = sorted((m.split("=", 1) for m in a.mask), key=lambda p: -len(p[0]))
masks += [(p.replace("/var/", "/private/var/", 1), r) for p, r in masks if p.startswith("/var/")]
masks.sort(key=lambda p: -len(p[0]))
TMP = re.compile(r"/(?:private/)?var/folders/[^/\s]+/[^/\s]+/T/")


def clean(text):
    for frm, to in masks:
        text = text.replace(frm, to)
    return TMP.sub("$TMPDIR/", text)


def cut(text, n=80):
    lines = text.rstrip("\n").split("\n")
    return "\n".join(lines[:n] + (["[...]"] if len(lines) > n else []))


def indent(text, pad="    "):
    return "\n".join(pad + line if line else line for line in text.split("\n"))


def result_text(content):
    if isinstance(content, str):
        return content
    return "\n".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")


calls, outputs, final, model, usage = [], {}, None, "", {}
for line in open(a.stream):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    t = d.get("type")
    if t == "system" and d.get("subtype") == "init":
        model = d.get("model", "")
    elif t == "assistant":
        for c in d["message"].get("content", []):
            if c.get("type") == "tool_use":
                calls.append(c)
    elif t == "user":
        content = d.get("message", {}).get("content", [])
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    outputs[c["tool_use_id"]] = (result_text(c.get("content", "")), c.get("is_error", False))
    elif t == "result":
        final = d.get("result", "")
        usage = {"turns": d.get("num_turns"), "seconds": round((d.get("duration_ms") or 0) / 1000)}

out = [
    f"# repro-reviewer example: {a.name}",
    "",
    f"Sample repo: make-sample-repo.sh, branch {a.branch} @ {a.sha}",
    f"Run: {a.started}, {a.version}, model {model}, exit {a.exit}, "
    f"{usage.get('turns')} turns, {usage.get('seconds')} s",
    "Command: run-example.sh (claude -p --agent repro-reviewer, isolated from user settings)",
    "",
    "## Prompt",
    "",
    indent(a.prompt),
    "",
    f"## Tool calls ({len(calls)}, in order)",
]
for i, c in enumerate(calls, 1):
    inp = c.get("input", {})
    if c["name"] == "Bash":
        head = inp.get("command", "")
    elif c["name"] == "Read":
        head = inp.get("file_path", "") + (f" (from line {inp['offset']})" if inp.get("offset") else "")
    else:
        head = json.dumps(inp)
    text, err = outputs.get(c["id"], ("(no output recorded)", False))
    out += ["", f"[{i}] {c['name']}: " + clean(head).replace("\n", "\n    "),
            "--- output" + (" (tool error)" if err else "") + ":", indent(clean(cut(text)))]
out += ["", "## Final report", "", clean(final or "(no final report)"), ""]
sys.stdout.write("\n".join(out))

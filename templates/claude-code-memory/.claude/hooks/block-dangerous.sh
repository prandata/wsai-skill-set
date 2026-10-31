#!/bin/bash
# PreToolUse hook: blocks dangerous shell commands no matter what Claude decides.
# CLAUDE.md is context, not enforced configuration; a hook is enforced (https://code.claude.com/docs/en/memory).
# Exit code 2 blocks the tool call and shows stderr to Claude. Any other failure here also blocks.
# Needs bash and python3. Make it executable: chmod +x .claude/hooks/block-dangerous.sh
# A guardrail, not a sandbox: it parses the command like a shell, but a determined script can still hide a command.
python3 -c '
import sys, json, re, shlex

def block(why):
    print("Blocked by .claude/hooks/block-dangerous.sh: " + why, file=sys.stderr)
    sys.exit(2)

try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    block("could not read the command")

WRAPPERS = {"sudo", "env", "command", "nohup", "time", "nice", "doas", "xargs"}
SHELLS = {"bash", "sh", "zsh", "dash"}
DANGER_TARGETS = {"/", "/*", "~", "~/", "~/*", "*", ".", "./", "..", "$HOME", "${HOME}", "$HOME/", "${HOME}/", "$HOME/*"}

def is_env(tok):
    return re.search(r"(^|/)\.env(\..*)?$", tok) is not None

def check(text, depth=0):
    if depth > 3:
        block("nested shell too deep to inspect")
    for seg in re.split(r"&&|\|\||[;&|\n]|\$\(|`", text):
        if not seg.strip():
            continue
        try:
            toks = shlex.split(seg, comments=False)
        except ValueError:
            block("could not parse: " + seg.strip())
        while toks and (toks[0] in WRAPPERS or re.match(r"^\w+=", toks[0])):
            toks = toks[1:]
            while toks and toks[0].startswith("-"):
                toks = toks[1:]
        if not toks:
            continue
        prog = toks[0].rsplit("/", 1)[-1]
        args = toks[1:]
        if prog in SHELLS and "-c" in args:
            i = args.index("-c")
            if i + 1 < len(args):
                check(args[i + 1], depth + 1)
        if any(is_env(t) for t in args):
            block(".env is off limits: " + seg.strip())
        if prog == "rm":
            flags = [a for a in args if a.startswith("-")]
            rec = any(a in ("--recursive",) or (not a.startswith("--") and re.search(r"[rR]", a)) for a in flags)
            force = any(a == "--force" or (not a.startswith("--") and "f" in a) for a in flags)
            if rec and force and any(a.rstrip() in DANGER_TARGETS for a in args if not a.startswith("-")):
                block("recursive force-delete of a root, home or whole folder: " + seg.strip())
        if prog == "git" and "push" in args:
            after = args[args.index("push") + 1:]
            for a in after:
                if a == "--force" or a.startswith("--force") or a.startswith("+") or (re.match(r"^-[a-zA-Z]+$", a) and "f" in a):
                    block("force-push: " + seg.strip())

check(cmd)
'
s=$?
[ "$s" -eq 0 ] && exit 0
exit 2

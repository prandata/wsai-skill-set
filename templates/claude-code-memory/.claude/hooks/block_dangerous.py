import sys, json, re, shlex, posixpath, fnmatch

def block(why):
    print("Blocked by .claude/hooks/block-dangerous.sh: " + why, file=sys.stderr)
    sys.exit(2)

try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    block("could not read the command")

SEPS = {";", "&", "&&", "|", "||", "(", ")", "\n", ";;", "|&"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
DANGER = {"/", "/*", "~", "~/*", "~/.*", ".", "..", "*", "**", ".*", "../*", "$HOME", "${HOME}",
          "$HOME/*", "${HOME}/*", "$PWD", "${PWD}", "$PWD/*", "${PWD}/*"}
FIND_FILTERS = ("-name", "-iname", "-path", "-ipath", "-regex", "-type", "-mtime", "-mmin", "-newer", "-size", "-user", "-empty")
LONG_PUSH = ("--force", "--force-with-lease", "--force-if-includes", "--delete", "--mirror", "--prune")

def danger(a):
    n = posixpath.normpath(a) if a else a
    n = re.sub(r"^/+", "/", n)
    return n in DANGER

def is_env(tok):
    if re.search(r"(?:^|[/=@<>:])\.env(?![A-Za-z0-9_-])", tok):
        return True
    b = posixpath.basename(tok)
    return len(b) >= 3 and b.startswith(".") and re.search(r"[*?\[]", b) is not None and fnmatch.fnmatchcase(".env", b)

def lex(text):
    s = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>\n")
    s.whitespace_split = True
    s.whitespace = " \t\r"
    s.commenters = ""
    return list(s)

def segments(toks):
    seg, out = [], []
    for t in toks:
        if t in SEPS:
            out.append(seg); seg = []
        else:
            seg.append(t)
    out.append(seg)
    return [s for s in out if s]

HEREDOC = re.compile(r"(\bcat\b[^\n<]*<<-?\s*(['\"]?)(\w+)\2[^\n]*)\n(.*?)\n[ \t]*\3[ \t]*(?=\n|$)", re.S)
PIPE_TO_SHELL = re.compile(r"\|\s*(?:sudo\s+)?(?:\S*/)?(?:ba|z|da|k)?sh\b")
BRACES = re.compile(r"\{([^{}]*,[^{}]*)\}")

def expand(tok):
    m = BRACES.search(tok)
    if not m:
        return [tok]
    return [x for part in m.group(1).split(",") for x in expand(tok[:m.start()] + part + tok[m.end():])]

def check(text, depth=0):
    if depth > 4:
        block("nested shell too deep to inspect")
    for m in HEREDOC.finditer(text):
        if PIPE_TO_SHELL.search(m.group(1)):
            check(m.group(4), depth + 1)   # cat <<EOF | bash: the body runs
    text = HEREDOC.sub(r"\1", text)
    for inner in re.findall(r"`([^`]*)`", text) + re.findall(r"\$\(([^()]*)\)", text):
        check(inner, depth + 1)
    if re.search(r"\$'|\$\{?IFS\b", text):
        block("quoting form the hook cannot inspect ($'..' or IFS): " + text.strip()[:80])
    try:
        toks = lex(text)
    except ValueError:
        block("could not parse: " + text.strip()[:80])
    prev = []
    for seg in segments(toks):
        for t in seg:
            if "$(" in t or "`" in t:
                for inner in re.findall(r"\$\((.*)\)", t, re.S) + re.findall(r"`([^`]*)`", t):
                    check(inner, depth + 1)
            if any(is_env(x) for x in expand(t)):
                block(".env is off limits: " + " ".join(seg)[:80])
        base = [posixpath.basename(t) for t in seg]
        for i, b in enumerate(base):
            rest = seg[i + 1:]
            if b == "eval":
                check(" ".join(rest), depth + 1)
            if b in SHELLS:
                for j, a in enumerate(rest):
                    if (re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", a) or a == "--command") and j + 1 < len(rest):
                        check(rest[j + 1], depth + 1)
                    if a == "<<<" and j + 1 < len(rest):
                        check(rest[j + 1], depth + 1)
                if i == 0 and prev and not any(re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", a) or not a.startswith("-") for a in rest):
                    check(" ".join(prev), depth + 1)   # echo '...' | sh
            if b == "rm":
                flags = [a for a in rest if a.startswith("-")]
                rec = any(a == "--recursive" or (not a.startswith("--") and re.search(r"[rR]", a)) for a in flags)
                force = any(a == "--force" or (not a.startswith("--") and "f" in a) for a in flags)
                if rec and force and any(danger(a) for a in rest if not a.startswith("-")):
                    block("recursive force-delete of a root, home or whole folder: " + " ".join(seg)[:80])
            if b == "find" and "-delete" in rest or (b == "find" and any(posixpath.basename(r) == "rm" for r in rest)):
                paths = [a for a in rest if not a.startswith("-")][:1]
                broad = paths and danger(paths[0])
                root = paths and posixpath.normpath(paths[0]) in ("/", "~", "$HOME", "${HOME}")
                if broad and (root or not any(f in rest for f in FIND_FILTERS)):
                    block("find that deletes everything under a root, home or whole folder: " + " ".join(seg)[:80])
            if b == "git" and "push" in rest:
                for a in rest[rest.index("push") + 1:]:
                    key = a.split("=")[0]
                    if (a.startswith("+") or re.fullmatch(r":[^:]+", a)
                            or (a.startswith("--") and len(key) >= 4 and any(o.startswith(key) for o in LONG_PUSH))
                            or re.fullmatch(r"-[a-zA-Z]+", a) and re.search(r"[fd]", a)):
                        block("force-push or remote delete: " + " ".join(seg)[:80])
        prev = seg

check(cmd)

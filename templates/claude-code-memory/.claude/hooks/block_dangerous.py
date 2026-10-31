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
    if re.search(r"(?:^|[/=@<>:])\.env(?![A-Za-z0-9_-])", tok, re.I):
        return True
    b = posixpath.basename(tok)
    return len(b) >= 3 and b.startswith(".") and re.search(r"[*?\[]", b) is not None and fnmatch.fnmatchcase(".env", b.lower())

def hides_expansion(text):
    """True if $'..', $".." or $IFS/${IFS} appears outside quotes (bash expands these into words the lexer cannot see)."""
    st, i, n = None, 0, len(text)
    while i < n:
        c = text[i]
        if st == "'":
            if c == "'": st = None
        elif c == "\\":
            i += 1
        elif st == '"':
            if c == '"': st = None
        elif c in "'\"":
            st = c
        elif c == "$" and (text[i+1:i+2] in ("'", '"') or re.match(r"\$\{?IFS\b", text[i:])):
            return True
        i += 1
    return False

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

HEREDOC = re.compile(r"(?m)^([^\n<]*?<<-?[ \t]*(['\"]?)(\w+)\2[^\n]*)\n((?s:.*?))\n[ \t]*\3[ \t]*(?=\n|$)")
PIPE_TO_SHELL = re.compile(r"\|\s*(?:(?:\S*/)?(?:sudo|doas|env|nohup|nice|timeout|command|exec|time|setsid|stdbuf)\b[^|;&]*?\s+)?(?:\S*/)?(?:ba|z|da|k)?sh\b")
WRAPPERS = {"sudo", "doas", "env", "nohup", "nice", "timeout", "command", "exec", "time", "setsid", "stdbuf"}

def heredoc_reader_is_shell(header):
    seg = re.split(r"&&|\|\||[;|(&]|\bthen\b|\bdo\b", header.split("<<")[0])[-1].split()
    i = 0
    while i < len(seg) and (posixpath.basename(seg[i]) in WRAPPERS or seg[i].startswith("-") or re.fullmatch(r"\w+=.*", seg[i]) or (i > 0 and seg[i - 1].startswith("-"))):
        i += 1
    return i < len(seg) and posixpath.basename(seg[i]) in SHELLS
BRACES = re.compile(r"\{([^{}]*,[^{}]*)\}")

def expand(tok, budget=[0]):
    m = BRACES.search(tok)
    if not m:
        return [tok]
    out = [x for part in m.group(1).split(",") for x in expand(tok[:m.start()] + part + tok[m.end():])]
    if len(out) > 256:
        block("brace expansion too large to inspect")
    return out

def check(text, depth=0):
    if depth > 4:
        block("nested shell too deep to inspect")
    text = re.sub(r"(?<!\\)((?:\\\\)*)\\\n", r"\1", text)   # bash drops backslash-newline; shlex would keep a newline char in the word
    def strip(m):
        line_start = m.string.rfind("\n", 0, m.start(1)) + 1
        prefix = m.string[line_start:m.start(1)]
        unquoted = re.sub(r"'[^']*'|\"[^\"]*\"", "", prefix)
        if prefix.count("'") % 2 or re.search(r"(^|\s)#", unquoted) or m.group(1).count("'") % 2:
            return m.group(0)               # 'cat <<EOF' inside a string or comment: not a heredoc, keep the lines
        if PIPE_TO_SHELL.search(m.group(1)) or heredoc_reader_is_shell(m.group(1)):
            check(m.group(4), depth + 1)   # cat <<EOF | bash: the body runs
        if not m.group(2):                  # unquoted delimiter: bash expands $(..) and `..` in the body
            for inner in re.findall(r"`([^`]*)`", m.group(4)) + re.findall(r"\$\(([^()]*)\)", m.group(4)):
                check(inner, depth + 1)
        return m.group(1)
    text = HEREDOC.sub(strip, text)
    for inner in re.findall(r"`([^`]*)`", text) + re.findall(r"\$\(([^()]*)\)", text):
        check(inner, depth + 1)
    if re.search(r"(?:^|[\s;&|(])(?:\S*/)?(?:(?:ba|z|da|k)?sh|source|\.)\s+(?:-\S+\s+)*<\(", text):
        block("a shell reading a process substitution cannot be inspected: " + text.strip()[:80])
    for inner in re.findall(r"[<>]\(([^()]*)\)", text):
        check(inner, depth + 1)
    if hides_expansion(text):
        block("quoting form the hook cannot inspect ($'..', $\"..\" or IFS): " + text.strip()[:80])
    try:
        toks = lex(text)
    except ValueError:
        block("could not parse: " + text.strip()[:80])
    prev = []
    for seg in segments(toks):
        seg = [x for t in seg for x in expand(t)]
        for t in seg:
            if "$(" in t or "`" in t:
                for inner in re.findall(r"\$\((.*)\)", t, re.S) + re.findall(r"`([^`]*)`", t):
                    check(inner, depth + 1)
            if is_env(t):
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
                if prev and all(posixpath.basename(x) in WRAPPERS or x.startswith("-") or re.fullmatch(r"\w+=.*", x) or (k > 0 and seg[k - 1].startswith("-")) or re.fullmatch(r"[0-9.]+[smhd]?", x) for k, x in enumerate(seg[:i])) and not any(re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", a) or not a.startswith("-") for a in rest):
                    check(" ".join(prev), depth + 1)   # echo '...' | sh
            if b == "rm" and not (i > 0 and base[i - 1] == "git"):
                flags = [a for a in rest if a.startswith("-")]
                rec = any(a == "--recursive" or (not a.startswith("--") and re.search(r"[rR]", a)) for a in flags)
                force = any(a == "--force" or (not a.startswith("--") and "f" in a) for a in flags)
                if rec and any(danger(a) for a in rest if not a.startswith("-")):
                    block("recursive force-delete of a root, home or whole folder: " + " ".join(seg)[:80])
            if b == "find" and "-delete" in rest or (b == "find" and any(posixpath.basename(r) == "rm" for r in rest)):
                paths = []
                for a in rest:
                    if a.startswith("-") and a not in ("-L", "-H", "-P") or a in ("(", "!"):
                        break
                    if not a.startswith("-"):
                        paths.append(a)
                broad = any(danger(p) for p in paths)
                root = any(posixpath.normpath(p) in ("/", "~", "$HOME", "${HOME}") for p in paths)
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

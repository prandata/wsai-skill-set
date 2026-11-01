"""Offline tests for skills/ssh-key-audit/scripts/audit.sh.

curl is replaced by a stub on PATH, so nothing touches the network. Every key is a throwaway made
with ssh-keygen in a temporary folder (the DSA one is random bytes in DSA shape, not a real key),
and the folder is deleted at the end. Run: python3 tests/test_ssh_key_audit.py
"""
import base64, hashlib, os, random, shutil, stat, struct, subprocess, sys, tempfile

here = os.path.dirname(os.path.abspath(__file__))
script = os.path.join(here, "..", "skills", "ssh-key-audit", "scripts", "audit.sh")

STUB_CURL = r"""#!/bin/sh
# Stub curl: logs its arguments, then acts as told by STUB_MODE.
printf '%s\n' "$*" >> "$STUB_LOG"
case "$STUB_MODE" in
  neterr) echo "curl: (6) Could not resolve host: github.com" >&2; exit 6 ;;
esac
cat "$STUB_BODY"
printf '\n%s' "$STUB_CODE"
"""

tmp = tempfile.mkdtemp(prefix="ssh-key-audit-test-")
fails = 0


def keygen(name, *args):
    path = os.path.join(tmp, "keys", name)
    subprocess.run(["ssh-keygen", "-q", "-N", "", "-C", "", "-f", path, *args], check=True)
    return open(path + ".pub").read().split()[:2]  # [type, blob], no comment, like github.com/<user>.keys


def fingerprint(blob_b64):
    return "SHA256:" + base64.b64encode(hashlib.sha256(base64.b64decode(blob_b64)).digest()).decode().rstrip("=")


def fake_dsa():
    r = random.Random(4)
    s = lambda b: struct.pack(">I", len(b)) + b
    mp = lambda n: s(n.to_bytes((n.bit_length() + 8) // 8, "big"))
    blob = s(b"ssh-dss") + mp(r.getrandbits(1024) | 1 << 1023) + mp(r.getrandbits(160) | 1 << 159) \
        + mp(r.getrandbits(1020)) + mp(r.getrandbits(1020))
    return ["ssh-dss", base64.b64encode(blob).decode()]


def snapshot(root):
    out = {}
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            st = os.stat(p)
            out[p] = (st.st_mtime_ns, st.st_mode, hashlib.sha256(open(p, "rb").read()).hexdigest())
        out[d] = os.stat(d).st_mtime_ns
    return out


def run(args, body="", code="200", mode="ok", home=None):
    home = home or os.path.join(tmp, "home")
    body_file = os.path.join(tmp, "body")
    open(body_file, "w").write(body)
    log = os.path.join(tmp, "curl.log")
    open(log, "w").close()
    env = {
        "PATH": os.path.join(tmp, "bin") + ":/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin",
        "HOME": home, "LANG": "en_US.UTF-8",
        "STUB_BODY": body_file, "STUB_CODE": code, "STUB_MODE": mode, "STUB_LOG": log,
        "SSH_AUTH_SOCK": "/nonexistent/agent.sock",
    }
    p = subprocess.run(["/bin/bash", script, *args], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout, p.stderr, open(log).read()


def check(name, cond, detail=""):
    global fails
    fails += not cond
    print(f"{'ok ' if cond else 'BAD'} {name}" + (f"\n    {detail}" if not cond and detail else ""))


def keys_body(*keys):
    return "".join(f"{t} {b}\n" for t, b in keys)


try:
    os.makedirs(os.path.join(tmp, "keys"))
    os.makedirs(os.path.join(tmp, "bin"))
    curl = os.path.join(tmp, "bin", "curl")
    open(curl, "w").write(STUB_CURL)
    os.chmod(curl, stat.S_IRWXU)

    mine = keygen("mine", "-t", "ed25519")
    stranger = keygen("stranger", "-t", "ed25519")
    rsa2048 = keygen("rsa2048", "-t", "rsa", "-b", "2048")
    rsa3072 = keygen("rsa3072", "-t", "rsa", "-b", "3072")
    dsa = fake_dsa()

    home = os.path.join(tmp, "home")
    ssh = os.path.join(home, ".ssh")
    os.makedirs(ssh, mode=0o700)
    for n in ("mine", "rsa3072"):
        shutil.copy(os.path.join(tmp, "keys", n + ".pub"), os.path.join(ssh, f"id_{n}.pub"))
    old_home = os.path.join(tmp, "old-home")  # a machine whose only key is RSA 2048
    os.makedirs(os.path.join(old_home, ".ssh"))
    shutil.copy(os.path.join(tmp, "keys", "rsa2048.pub"), os.path.join(old_home, ".ssh", "id_rsa2048.pub"))
    shutil.copy(os.path.join(tmp, "keys", "mine"), os.path.join(ssh, "id_mine"))  # a private key file sits there too
    open(os.path.join(ssh, "config"), "w").write("Host *\n  IdentitiesOnly yes\n")

    # 1. Clean: the only GitHub key has a local .pub file.
    rc, out, err, log = run(["octo-cat"], keys_body(mine))
    check("clean account exits 0", rc == 0, out + err)
    check("clean account names the matching file", f"{fingerprint(mine[1])}  ED25519 256   local: id_mine.pub" in out, out)
    check("clean account says nothing changed", "read-only, nothing changed" in out, out)
    check("curl asked for the .keys URL over https only",
          "https://github.com/octo-cat.keys" in log and "--proto =https" in log and "--proto-redir =https" in log, log)

    # 2. A stranger key on GitHub is printed; your own key is not flagged.
    rc, out, err, _ = run(["octo-cat"], keys_body(mine, stranger))
    check("stranger key exits 1", rc == 1, out + err)
    check("stranger fingerprint flagged", f"{fingerprint(stranger[1])}  ED25519 256   NOT IN LOCAL .pub FILES" in out, out)
    check("own key not flagged", f"{fingerprint(mine[1])}  ED25519 256   local: id_mine.pub" in out, out)
    check("summary counts one unmatched key", "1 GitHub key(s) with no local .pub file" in out, out)

    # 3. Old types.
    rc, out, err, _ = run(["octo-cat"], keys_body(rsa2048), home=old_home)
    check("RSA 2048 exits 1 even when matched", rc == 1, out + err)
    check("RSA 2048 flagged as old", "local: id_rsa2048.pub   OLD: RSA 2048 bits: under 3072" in out, out)
    check("RSA 2048 matched key listed in the local section too", "Old-type local keys:" in out and "id_rsa2048.pub   OLD: RSA 2048" in out, out)
    rc, out, err, _ = run(["octo-cat"], keys_body(rsa3072))
    check("RSA 3072 not flagged", rc == 0 and "RSA 3072   local: id_rsa3072.pub\n" in out, out + err)
    rc, out, err, _ = run(["octo-cat"], keys_body(mine), home=old_home)
    check("local-only RSA 2048 flagged even when GitHub is clean", rc == 1 and "Old-type local keys:" in out and "id_rsa2048.pub   OLD: RSA 2048" in out, out + err)
    rc, out, err, _ = run(["octo-cat"], keys_body(mine, dsa))
    check("DSA exits 1", rc == 1, out + err)
    check("DSA fingerprint computed without ssh-keygen support",
          f"{fingerprint(dsa[1])}  DSA   NOT IN LOCAL .pub FILES   OLD: DSA" in out, out)

    # 4. Loud failures: the audit did not run, and says so on stderr.
    rc, out, err, _ = run(["no-such-user-zz"], "Not Found", code="404")
    check("unknown user exits 3", rc == 3, out + err)
    check("unknown user message names the user", "no user named 'no-such-user-zz'" in err and out == "", err)
    rc, out, err, _ = run(["octo-cat"], mode="neterr")
    check("network error exits 4", rc == 4 and "curl exit 6" in err and "did not run" in err, err)
    rc, out, err, _ = run(["octo-cat"], "oops", code="500")
    check("HTTP 500 exits 4", rc == 4 and "HTTP 500" in err, err)
    rc, out, err, _ = run(["octo-cat"], "<!DOCTYPE html><html>Sign in to Wi-Fi</html>\n")
    check("login page instead of keys exits 4", rc == 4 and "did not return an SSH key list" in err, err)
    rc, out, err, _ = run(["octo-cat"], "")
    check("no keys on GitHub exits 5", rc == 5 and "has no SSH keys on GitHub" in err, err)
    rc, out, err, _ = run(["octo-cat"], "\n\n")
    check("blank page counts as no keys", rc == 5, err)

    # 5. Bad input never reaches curl.
    for bad in ("../../evil", "-rf", "a b", "user/x", "a" * 40, "user.keys?x=1"):
        rc, out, err, log = run([bad], keys_body(mine))
        check(f"bad username {bad[:12]!r} exits 2 without calling curl", rc == 2 and log == "", f"rc={rc} log={log!r} {err}")
    rc, out, err, log = run([], keys_body(mine))
    check("missing username exits 2", rc == 2 and log == "", err)
    rc, out, err, log = run(["one", "two"], keys_body(mine))
    check("two usernames exit 2", rc == 2 and log == "", err)
    for flag in ("--apply", "--fix", "--delete", "--no-dry-run"):
        rc, out, err, log = run([flag, "octo-cat"], keys_body(mine))
        check(f"{flag} refused: there is no write mode", rc == 2 and "no write mode" in err and log == "", err)
    rc, out, err, log = run(["--bogus", "octo-cat"])
    check("unknown option exits 2", rc == 2 and log == "", err)
    rc, out, err, _ = run(["--help"])
    check("--help exits 0 and prints usage", rc == 0 and "Usage: audit.sh" in out, out + err)

    # 6. --dry-run is the default and changes nothing, ever.
    before = snapshot(home)
    rc1, out1, _, _ = run(["octo-cat"], keys_body(mine, stranger, rsa2048, dsa))
    rc2, out2, _, _ = run(["--dry-run", "octo-cat"], keys_body(mine, stranger, rsa2048, dsa))
    check("--dry-run gives the same result as the default", (rc1, out1) == (rc2, out2), out1 + "\n---\n" + out2)
    check("home folder unchanged after runs (files, modes, contents, folder times)", snapshot(home) == before)

    # 7. Edge cases.
    empty_home = os.path.join(tmp, "empty-home")
    os.makedirs(empty_home)
    rc, out, err, _ = run(["octo-cat"], keys_body(mine), home=empty_home)
    check("no ~/.ssh: every GitHub key flagged, exit 1, warning", rc == 1 and "NOT IN LOCAL" in out and "no *.pub files" in err, out + err)
    rc, out, err, _ = run(["--ssh-dir", ssh, "octo-cat"], keys_body(mine), home=empty_home)
    check("--ssh-dir reads another folder", rc == 0 and "local: id_mine.pub" in out, out + err)
    rc, out, err, _ = run(["octo-cat"], keys_body(mine).replace("\n", "\r\n"))
    check("CRLF line endings handled", rc == 0 and "local: id_mine.pub" in out, out + err)
    rc, out, err, _ = run(["octo-cat"], keys_body(mine).rstrip("\n"))
    check("no trailing newline handled", rc == 0, out + err)
    open(os.path.join(ssh, "broken.pub"), "w").write("not a key\n")
    open(os.path.join(ssh, "nonewline.pub"), "w").write(" ".join(stranger))
    rc, out, err, _ = run(["octo-cat"], keys_body(mine, stranger))
    check("unreadable local .pub warns and continues", "could not read a public key from" in err and "broken.pub" in err, err)
    check(".pub file without a final newline still read", rc == 0 and "local: nonewline.pub" in out, out + err)
    rc, out, err, _ = run(["octo-cat"], keys_body(mine) + "ssh-ed25519 AAAAnotbase64!!\n")
    check("unreadable GitHub key counted as a finding", rc == 1 and "COULD NOT READ" in out, out + err)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"{fails} failed")
sys.exit(1 if fails else 0)

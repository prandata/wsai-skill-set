---
name: ssh-key-audit
description: Read-only audit of the SSH keys on a GitHub account. Compares the public keys at github.com/<user>.keys with this machine's ~/.ssh/*.pub files by SHA256 fingerprint, and flags DSA keys and RSA keys under 3072 bits. Use when the user asks to audit, review or clean up their GitHub SSH keys, asks which keys are on their account, is rotating a key or replacing a laptop, or wants to know whether an unknown key has access. It never changes, uploads or deletes anything.
---

# SSH key audit

`scripts/audit.sh` runs the two-minute audit from the What Survives in AI guide "The SSH keys on your GitHub
account are public" (tested 1 Nov 2026), with the gaps closed: it checks the username, fails loudly, and flags old
key types. Every claim below links to its source, checked 1 Nov 2026.

## When to use it

- The user asks "which SSH keys are on my GitHub account?" or wants to audit or clean them up.
- They are rotating a key, retiring a laptop, or leaving a job, and want to see what still has access.
- They found a key they don't recognise.

## Run it

Ask for the user's exact GitHub username. Don't guess it from a git email or a folder name: a typo audits someone
else's account.

```bash
bash scripts/audit.sh <github-username>                 # compares with ~/.ssh/*.pub
bash scripts/audit.sh --ssh-dir /path/to/keys <user>    # another folder of .pub files
```

`--dry-run` is accepted and is the default. There is no other mode: `--apply`, `--fix`, `--delete` and
`--no-dry-run` are refused with exit 2.

It needs `curl`, `ssh-keygen` and `awk`. `openssl` is used only to fingerprint DSA keys, which OpenSSH 10 no longer
parses.

## What it does

1. Fetches `https://github.com/<user>.keys` over HTTPS only (20 second limit), with
   `curl -q` so a `~/.curlrc` cannot add an output or cookie file. GitHub's API for the same keys
   says it "is accessible by anyone", so no token is needed or sent.
   ([docs.github.com/en/rest/users/keys](https://docs.github.com/en/rest/users/keys))
2. Fingerprints each key with `ssh-keygen -E sha256 -lf`, the same `SHA256:` format GitHub shows in
   Settings, then SSH and GPG keys.
3. Fingerprints every `*.pub` file in `~/.ssh` and matches by fingerprint. A key comment doesn't change the
   fingerprint, so GitHub's comment-free copy still matches your file.
4. Flags old types:
   - **DSA (`ssh-dss`).** GitHub: "DSA keys (`ssh-dss`) are no longer supported." OpenSSH 10.0 "removes support for
     the weak DSA signature algorithm".
   - **RSA under 3072 bits.** OpenSSH 8.0 raised the `ssh-keygen` default RSA size to 3072 bits, "following NIST
     Special Publication 800-57's guidance for a 128-bit equivalent symmetric security level". GitHub's own
     guide prefers Ed25519 and gives RSA 4096 for "a legacy system that doesn't support the Ed25519 algorithm".
5. Prints a report and exits with a code you can act on.

## Read the result

| Exit | Meaning | What to tell the user |
|---|---|---|
| 0 | Every GitHub key has a `.pub` file here, none is old. | Clean. A `.pub` file does not prove the private key is still here. |
| 1 | Findings. | Each `NOT IN LOCAL .pub FILES` line is a key GitHub accepts that this machine has no public file for: another computer, or one they can't account for. Each `OLD:` line needs replacing. A `COULD NOT READ` line, or a warning about a local `.pub` file, means a key it could not parse: check it by hand. |
| 2 | Bad username, bad option, or a missing tool. | Fix the input. Nothing was fetched. |
| 3 | No such GitHub user (HTTP 404). | Check the spelling. The audit did not run. |
| 4 | Network error, other HTTP status, or a page that is not a key list (a proxy or Wi-Fi login page). | The audit did not run. Retry on a working connection. |
| 5 | The account has no SSH keys. | Nothing to compare. Fine if they use HTTPS. |

Keys listed under "Only in local .pub files" are not on this GitHub account. That is normal for keys used for
servers or other accounts, and is not counted as a finding.

## What to do with a finding

Tell the user; do not do these yourself unless they ask, and never with their main key.

1. **A key they can't explain:** find the fingerprint in GitHub Settings, then SSH and GPG keys, and delete it.
   GitHub: "For those that you don't recognize, or that are out-of-date, click Delete." For a key they don't know:
   "delete it immediately and contact us through the GitHub Support portal".
   ([Reviewing your SSH keys](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/reviewing-your-ssh-keys))
2. **An old key:** make a new one with `ssh-keygen -t ed25519 -C "you@example.com"` and a passphrase, add it on
   GitHub, then delete the old one.
   ([Generating a new SSH key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent))
3. **Then the servers:** deleting a key on GitHub does not remove it from a server's `~/.ssh/authorized_keys`.
   On each server, `ssh-keygen -lf ~/.ssh/authorized_keys` prints one fingerprint per key; delete the old key's line.

## What it does not do

- It changes nothing: no file, no setting, no key on GitHub or on disk. It writes no temporary files.
- It does not read private keys, and does not use your ssh-agent (it unsets `SSH_AUTH_SOCK` for its own run).
- It does not see keys held only in ssh-agent, a hardware key or a password manager, or `.pub` files outside the
  folder it reads.
- It does not prove a private key exists. A match means a `.pub` file with that fingerprint is in the folder.
- It does not check GPG keys (`github.com/<user>.gpg`), signing keys, deploy keys or server `authorized_keys`.
- It does not check other people's accounts for them. Audit only an account the user owns or administers.

## Agents and SSH keys

An agent runs commands as the user, so treat its access to keys with care.

- This skill only needs public data. Never `cat` a private key to "check" it, and never paste one into a chat.
- With `SSH_AUTH_SOCK` set, any process that can reach the agent socket can sign with a loaded key without reading
  the key file. OpenSSH's manual on forwarded agents: "An attacker cannot obtain key material from the agent, however
  they can perform operations on the keys". ([ssh(1)](https://man.openbsd.org/ssh.1))
- To give an agent push access to one repository, use a deploy key, "an SSH key that grants access to a single
  repository", instead of the user's own key.
  ([Managing deploy keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys))

## Sources

Checked 1 Nov 2026.

- GitHub REST API, SSH keys: https://docs.github.com/en/rest/users/keys
- GitHub, Reviewing your SSH keys: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/reviewing-your-ssh-keys
- GitHub, Generating a new SSH key: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent
- GitHub, Managing deploy keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys
- OpenSSH 8.0 release notes: https://www.openssh.org/txt/release-8.0
- OpenSSH 10.0 release notes: https://www.openssh.org/txt/release-10.0
- ssh-keygen(1): https://man.openbsd.org/ssh-keygen.1
- ssh(1): https://man.openbsd.org/ssh.1

Tests: `python3 tests/test_ssh_key_audit.py` from the repo root. It stubs `curl`, so it runs offline, and uses only
throwaway keys made in a temporary folder.

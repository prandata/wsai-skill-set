# security-reviewer: a read-only security review subagent

A Claude Code subagent that reviews a file, diff or folder for security issues and reports each one
with its severity, `file:line`, the exact line quoted, how an attacker would use it and the smallest
fix. It checks injection (SQL, shell, path), secrets in code, unsafe deserialisation, missing auth
checks, and user input reaching a dangerous call without validation.

The definition is one file, [`security-reviewer.md`](security-reviewer.md). It runs on `model: sonnet`.

## Install

Claude Code reads subagents from `.claude/agents/` (this project) and `~/.claude/agents/` (all your
projects). ([docs](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope))

```bash
git clone https://github.com/prandata/wsai-skill-set
mkdir -p .claude/agents && cp wsai-skill-set/agents/security-reviewer/security-reviewer.md .claude/agents/
```

After creating a scope's first agent file in a new `agents` folder, restart Claude Code to load it.
([docs](https://code.claude.com/docs/en/sub-agents#write-subagent-files))

## Use

| How | Example |
|---|---|
| Let Claude pick it | `Review tipjar/ for security issues` (the description says "Use proactively before merging code that handles user input, queries, files, secrets or auth") |
| Ask for it by name | `Use the security-reviewer subagent on this diff` |
| Run the whole session as it | `claude --agent security-reviewer` |

## What it did in our run

One run on 4 Nov 2026 (AEDT), Claude Code 2.1.317, `claude -p --agent security-reviewer`, on a
made-up Python repo with a planted f-string SQL query. Prompt: "Review tipjar/ for security issues."

| What | Result |
|---|---|
| Finding | "1. SQL injection (high), `tipjar/db.py:10`", quoting `query = f"SELECT id, name, email FROM users WHERE name = '{name}'"` |
| Fix it gave | `return conn.execute("SELECT id, name, email FROM users WHERE name = ?", (name,)).fetchone()` |
| The repo | Unchanged (`git status` empty after the run) |

A second reviewer re-ran the same file in a fresh copy of the repo: the same SQL injection at the same
line with a `?` fix, plus a low finding in `money.py`.

## How "read-only" is enforced

| Layer | What it does |
|---|---|
| `tools: Read, Grep, Glob` | The tool list is the guard. It has no Bash, Edit or Write, so it cannot run, edit or write anything. The docs' tools field: "Tools the subagent can use". ([docs](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields)) |
| The prompt | "Only report what the code shows." It can't run code, so a finding is a reading of the code, not a reproduction. Pair it with [`repro-reviewer`](../repro-reviewer/README.md) when you need proof. |

## Sources

Checked 4 Nov 2026 (AEDT).

- Claude Code, Create custom subagents: https://code.claude.com/docs/en/sub-agents

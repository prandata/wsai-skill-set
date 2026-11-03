# docs-updater: a subagent that brings the docs in line with the code

A Claude Code subagent for after a change to flags, commands, function names or config keys. It reads
the code that defines the public surface, reads every Markdown file that mentions it, and fixes each
doc line that no longer matches. The code is right; the docs follow it. It keeps the author's wording
and reports each change with the code line that proves it.

The definition is one file, [`docs-updater.md`](docs-updater.md). It runs on `model: sonnet`.

## Install

Claude Code reads subagents from `.claude/agents/` (this project) and `~/.claude/agents/` (all your
projects). ([docs](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope))

```bash
git clone https://github.com/prandata/wsai-skill-set
mkdir -p .claude/agents && cp wsai-skill-set/agents/docs-updater/docs-updater.md .claude/agents/
```

After creating a scope's first agent file in a new `agents` folder, restart Claude Code to load it.
([docs](https://code.claude.com/docs/en/sub-agents#write-subagent-files))

## Use

| How | Example |
|---|---|
| Let Claude pick it | `Check README.md against the code and fix anything out of date` (the description says "Use proactively after a change to flags, commands, function names or config keys") |
| Ask for it by name | `Use the docs-updater subagent after this rename` |
| Run the whole session as it | `claude --agent docs-updater` |

## What it did in our run

One run on 4 Nov 2026 (AEDT), Claude Code 2.1.317, `claude -p --agent docs-updater`, on a made-up
Python repo whose README still said `--count` after the code renamed the flag to `--limit`. Prompt:
"Check README.md against the code and fix anything out of date."

| What | Result |
|---|---|
| Changes | README.md lines 7 and 9: `python3 -m tipjar.cli --count 5` became `--limit 5`, and the flag's description line now reads `--limit N` |
| Proof it gave | "`tipjar/cli.py:6` has `p.add_argument("--limit", type=int, default=10, ...)`. The parser has no `--count` argument." |
| The code | Untouched. `git status` after the run: ` M README.md` only |

A second reviewer re-ran the same file in a fresh copy of the repo: the same two lines, the same
proof, and only README.md changed.

## How "Markdown only" is enforced, and where it isn't

| Layer | What it does |
|---|---|
| `tools: Read, Grep, Glob, Edit` | No Bash or Write, so it can't run commands or create files. Edit can still change any existing file. |
| The prompt | "Edit only `.md` files. Never touch code." An instruction, not a guard. |
| Your permission rules | To block edits to code, add an `Edit` deny rule for your source folder, such as `Edit(/src/**)`, to `permissions.deny`. ([docs](https://code.claude.com/docs/en/permissions#read-and-edit)) In the default permission mode each edit also asks you first, so you see the path before it changes. |

The file sets no `permissionMode`, so it inherits your session's permission mode.
([docs](https://code.claude.com/docs/en/sub-agents#permission-modes))

## Sources

Checked 4 Nov 2026 (AEDT).

- Claude Code, Create custom subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code, Configure permissions: https://code.claude.com/docs/en/permissions

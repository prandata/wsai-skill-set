# test-writer: a subagent that writes tests and leaves the code alone

A Claude Code subagent that writes unit tests for a function or file that has none, runs them, and
reports what they cover. When a test fails, it reports a possible bug (the input, the value the
docstring promises and the value it got) instead of weakening the test or editing the source.

The definition is one file, [`test-writer.md`](test-writer.md). It runs on `model: sonnet`.

## Install

Claude Code reads subagents from `.claude/agents/` (this project) and `~/.claude/agents/` (all your
projects). ([docs](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope))

```bash
git clone https://github.com/prandata/wsai-skill-set
mkdir -p .claude/agents && cp wsai-skill-set/agents/test-writer/test-writer.md .claude/agents/
```

After creating a scope's first agent file in a new `agents` folder, restart Claude Code to load it.
([docs](https://code.claude.com/docs/en/sub-agents#write-subagent-files))

## Use

| How | Example |
|---|---|
| Let Claude pick it | `Write tests for parse_amount in tipjar/money.py` (the description says "Use proactively when new code lands without tests") |
| Ask for it by name | `Use the test-writer subagent on src/money.py` |
| Run the whole session as it | `claude --agent test-writer` |

## What it did in our run

One run on 4 Nov 2026 (AEDT), Claude Code 2.1.317, `claude -p --agent test-writer`, on a made-up
Python repo with no tests and one planted bug (`parse_amount("12.5")` returns 1205 cents, not 1250).
Prompt: "Write tests for parse_amount in tipjar/money.py."

| What | Result |
|---|---|
| Tests | Wrote `tests/test_money.py`; `Ran 12 tests in 0.001s`, `FAILED (failures=1)` |
| The failure | `AssertionError: 1205 != 1250`, reported as "Possible bug: parse_amount("12.5") returns 1205, not 1250." |
| The source | Untouched: "I didn't change the source or weaken the test." `git status` after the run showed only new, untracked `tests/` and Python's `tipjar/__pycache__/` |

A second reviewer re-ran the same file in a fresh copy of the repo. It wrote 13 tests (12 pass, 1
fails), found the same bug and left the source alone, but did not add `tests/__init__.py`, so its
tests needed `PYTHONPATH=.` to be discovered. Runs differ from one try to the next.

## How "never edits the code under test" is enforced, and where it isn't

| Layer | What it does |
|---|---|
| `tools: Read, Grep, Glob, Write, Bash` | No Edit tool, but Write can replace any file and Bash can run anything. The rule is in the prompt, not the tool list. |
| The prompt | "You write tests. You do not change the code under test." and rule 5: "do not weaken it and do not edit the source". An instruction, not a guard. |
| Your permission rules | To block file edits in your source folder, add an `Edit` deny rule such as `Edit(/src/**)` to `permissions.deny`. "`Edit` rules apply to all built-in tools that edit files." They don't limit Bash. ([docs](https://code.claude.com/docs/en/permissions#read-and-edit)) |

The file sets no `permissionMode`, so it inherits your session's permission mode.
([docs](https://code.claude.com/docs/en/sub-agents#permission-modes))

## Sources

Checked 4 Nov 2026 (AEDT).

- Claude Code, Create custom subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code, Configure permissions: https://code.claude.com/docs/en/permissions

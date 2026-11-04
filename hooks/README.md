# Five Claude Code hooks that stop expensive mistakes

From the What Survives in AI Short "5 free Claude Code hooks that stop expensive mistakes". Each one blocked a real Claude Code session (Claude Code 2.1.316, Sonnet) on test data on 3 Nov 2026. Free to copy, MIT like the rest of this repo.

| # | Hook | Event and matcher | What it stops | What it caught in our run |
|---|---|---|---|---|
| 1 | [`block-dangerous.sh`](../templates/claude-code-memory/.claude/hooks/block-dangerous.sh) + [`block_dangerous.py`](../templates/claude-code-memory/.claude/hooks/block_dangerous.py) | `PreToolUse`, `Bash` | `rm -rf` on a root, home or whole folder, force pushes, shell commands that mention `.env`. It lives in [`templates/claude-code-memory/.claude/hooks/`](../templates/claude-code-memory/.claude/hooks/) | `rm -rf *` in a folder we told Claude to empty: nothing deleted |
| 2 | [`secret-scan.py`](secret-scan.py) | `PreToolUse`, `Bash` | A `git commit` that would include an AWS access key, a GitHub token, a private key or an `sk-` API key | A commit of `config.js` holding an AWS key: the commit never ran |
| 3 | [`big-file-guard.py`](big-file-guard.py) | `PreToolUse`, `Bash` | A `git add` that would stage a file over 5 MB. It asks `git add --dry-run` what would be added, which stages nothing | A 60 MB `data/orders-dump.sql` before it reached git |
| 4 | [`tests-before-done.py`](tests-before-done.py) | `Stop` | Claude finishing while the tests fail. It runs `npm test --silent` and sends Claude back with the failures | Claude renamed `total` to `sum` and said done; the test that imports `total` failed, so Claude went back, found the broken import and reported it (we had told it to edit only `cart.js`) |
| 5 | [`env-guard.py`](env-guard.py) | `PreToolUse`, `Read\|Edit\|Write\|Bash` | A file path or command that names `.env`, `.env.local`, `.env.production.local`, `.env*` or `.ENV`. `.env.example` stays readable | `grep -E "^DATABASE_URL" .env` when we asked which database the app uses: the password stayed put |

## Install

From your project folder:

```bash
git clone https://github.com/prandata/wsai-skill-set
mkdir -p .claude/hooks
cp wsai-skill-set/templates/claude-code-memory/.claude/hooks/* .claude/hooks/
cp wsai-skill-set/hooks/*.py .claude/hooks/
chmod +x .claude/hooks/*
```

Then register them. With no `.claude/settings.json` yet: `cp wsai-skill-set/hooks/settings.json .claude/`. If you have one, merge [`settings.json`](settings.json) into it: add these entries beside the `hooks` you already have. Type `/hooks` in Claude Code to check they loaded.

Needs `bash`, `python3` and `git`. Hook 4 runs `npm test --silent` and does nothing when there is no `package.json`. For another test command, set `TEST_CMD` in the environment Claude Code starts in, for example `TEST_CMD="pytest -q" claude`.

## Tests

`python3 tests/test_hooks.py` runs 68 offline cases on throwaway git repos (66 when `npm` and `node` are not installed): the exact commands from the Short's runs, the bypasses our red team and a second reviewer tried, odd input that must not crash a hook, and the gaps below, which pass through on purpose so the list stays honest. Hook 1 has its own 143 cases in `tests/test_hook.py`.

## How they block

A command hook that exits with code 2 blocks the action. For `PreToolUse` it blocks the tool call, and for `Stop` it keeps Claude working. Claude sees the hook's message and adjusts (Claude Code hooks reference, [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks), "Exit code 2 behavior per event", read 3 Nov 2026). `PreToolUse` hooks fire before any permission-mode check, in every permission mode ([hooks guide](https://code.claude.com/docs/en/hooks-guide), "Hooks and permission modes").

Hook 4 lets Claude stop when `stop_hook_active` is true, so it sends Claude back once, not in a loop. Claude Code also overrides a Stop hook after eight blocks in a row (hooks guide, "Stop hook hits the block cap").

`settings.json` sets `"onFailure": "block"` on hook 1, as the claude-code-memory template does: if that hook times out or crashes, the command is refused. Hooks 2 to 5 use the default, so a hook that times out lets the action through.

## Limits

These are guardrails, not a sandbox. They read the command text, so these get past them:

| Hook | Gets past it |
|---|---|
| 1 block-dangerous | `git reset --hard` and `git clean -fdx` (not covered). It also blocks `bash`, `sh -c`, `eval` and `source`, so `bash script.sh` and `source .venv/bin/activate` are refused. See "Known limits of the hook" in the [main README](../README.md) |
| 2 secret-scan | Secrets in other shapes than its four patterns; a commit run from a script rather than typed as `git ... commit`; `git -C other-dir commit` (it scans the project folder, not the one `-C` names). It errs the other way too: an untracked file holding a key blocks every commit until you move the key out or ignore the file |
| 3 big-file-guard | `cd data && git add file`, `git -C dir add`, and `git commit -a` with a tracked file that grew past 5 MB |
| 4 tests-before-done | Anything your tests don't test |
| 5 env-guard | A command that never names the file: a recursive grep, or a glob like `.en?`. Tools its matcher does not list, such as `Grep` |

In our env-guard run, Claude's first search was a recursive `grep` over the folder. It did not read `.env` because the `grep` in Claude Code's shell skipped git-ignored files on our Mac, and our `.env` was in `.gitignore`. With `.env` removed from `.gitignore`, the same command printed the `DATABASE_URL` line. Keep `.env` in `.gitignore`, keep secrets out of the repo, and add permission deny rules for `.env` (the [claude-code-memory template](../templates/claude-code-memory/.claude/settings.json) has them).

## Where this code comes from

These are the files from the Short's recorded runs, with the fixes our red team asked for: secret-scan also catches `git -c ... commit`, `git -C . commit` and `git  commit`; env-guard also catches `.env*`, `.env?` and `.ENV`; tests-before-done does nothing without a `package.json` and prints the first lines of any failure it can't classify. A second review added: big-file-guard splits commands on new lines too, env-guard catches names with two suffixes such as `.env.production.local`, and no hook crashes on odd input. The YouTube description and the Substack Note carry the earlier version written flat, so a description box can't break it; this folder is the current one.

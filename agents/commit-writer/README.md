# commit-writer: a subagent that writes the commit message and leaves the commit to you

A Claude Code subagent that reads what is staged, matches the repo's commit style, and replies with
one commit message: a subject of at most 50 characters in the imperative, then up to three short
lines on why. It doesn't run `git commit` and adds no trailers (no Co-Authored-By, no
Signed-off-by).

The definition is one file, [`commit-writer.md`](commit-writer.md). It runs on `model: haiku`.

## Install

Claude Code reads subagents from `.claude/agents/` (this project) and `~/.claude/agents/` (all your
projects). ([docs](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope))

```bash
git clone https://github.com/prandata/wsai-skill-set
mkdir -p .claude/agents && cp wsai-skill-set/agents/commit-writer/commit-writer.md .claude/agents/
```

After creating a scope's first agent file in a new `agents` folder, restart Claude Code to load it.
([docs](https://code.claude.com/docs/en/sub-agents#write-subagent-files))

## Use

| How | Example |
|---|---|
| Let Claude pick it | `Write a commit message for the staged changes` (the description says "Use proactively when the user asks to commit") |
| Ask for it by name | `Use the commit-writer subagent` |
| Run the whole session as it | `claude --agent commit-writer` |

## What it did in our run

One run on 4 Nov 2026 (AEDT), Claude Code 2.1.317, `claude -p --agent commit-writer`, on a made-up
Python repo with three files staged (a fix in `tipjar/money.py` and its tests). Prompt: "Write a commit message
for the staged changes."

| What | Result |
|---|---|
| Commands | `git diff --staged --stat`, `git diff --staged`, `git log --oneline -5` |
| Message | Subject `Fix one-decimal amounts in parse_amount`, then three lines on why, starting `"12.5" was parsed as 1205 cents because the fraction was used as-is.` |
| The repo | No commit: the three files were still staged and `HEAD` was unchanged after the run. 9.5 s |

Our run was limited from outside the file: `--permission-mode dontAsk` with
`--allowedTools "Bash(git diff:*)" "Bash(git status:*)" "Bash(git log:*)" Read`, so any other
command would have been refused. The first version of the file added a Co-Authored-By trailer;
rule 5 was added and it was run again. A second reviewer re-ran the final file in a fresh copy of the
repo: the same three commands, a message with different wording, and no commit.

## How "never commits" is enforced, and where it isn't

| Layer | What it does |
|---|---|
| `tools: Bash, Read` | It needs Bash to read the diff, and the file can't narrow Bash to some commands: a `disallowedTools` entry with a specifier "still removes the whole tool". ([docs](https://code.claude.com/docs/en/sub-agents#restrict-which-tools-a-subagent-can-use)) So a copied file has full Bash. |
| The prompt | "You do not run `git commit`." An instruction, not a guard. |
| Your permission rules | The docs' way to keep Bash and block commands: "add a Bash deny rule such as `Bash(git push *)` to `permissions.deny` in your settings. The rule applies to the main conversation and to subagents." For this agent, `Bash(git commit *)` and `Bash(git push *)`. ([docs](https://code.claude.com/docs/en/sub-agents#restrict-which-tools-a-subagent-can-use)) |

A deny rule matches the command as written. The docs list `git -C . push origin main` and
`git -c push.default=current push origin main` among the commands `Bash(git push *)` does not
match. ([docs](https://code.claude.com/docs/en/permissions#bash)) The stronger setup is the one our run used: allow only
`git diff`, `git status` and `git log`, and refuse the rest (`dontAsk` "Auto-denies every call
that would otherwise prompt"). ([docs](https://code.claude.com/docs/en/permissions))

## Sources

Checked 4 Nov 2026 (AEDT).

- Claude Code, Create custom subagents: https://code.claude.com/docs/en/sub-agents
- Claude Code, Configure permissions: https://code.claude.com/docs/en/permissions

# repro-reviewer: a review subagent that must reproduce before it says PASS

A Claude Code subagent for code review. It may report only what it has reproduced: every finding
comes with the command it ran, the exit code and the output, quoted. A claim it can't run blocks a
PASS. It ends every review with one line you can act on:

```
VERDICT: PASS @ <sha>
VERDICT: FIX @ <sha>
```

The definition is one file, [`repro-reviewer.md`](repro-reviewer.md). Three real runs on a small
sample repo are saved under [`examples/`](examples/).

## Install

Copy the file into a subagents folder. Claude Code reads subagents from `.claude/agents/` (this
project) and `~/.claude/agents/` (all your projects); when both have the same name, the project one
wins. ([docs](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope))

```bash
git clone https://github.com/prandata/wsai-skill-set
mkdir -p .claude/agents
cp wsai-skill-set/agents/repro-reviewer/repro-reviewer.md .claude/agents/      # this project
# or: mkdir -p ~/.claude/agents && cp wsai-skill-set/agents/repro-reviewer/repro-reviewer.md ~/.claude/agents/
```

Claude Code picks up a new or edited file "within a few seconds" with no restart, except in one
case that applies to a first install: "after creating a scope's first agent file in a new `agents`
directory, restart to load it". ([docs](https://code.claude.com/docs/en/sub-agents#write-subagent-files))

## Use

| How | Example |
|---|---|
| Ask for it by name | `Use the repro-reviewer subagent to review the last commit` |
| @-mention it (this one always runs) | `@agent-repro-reviewer review this branch against main` |
| Run the whole session as it | `claude --agent repro-reviewer` |
| Check someone else's claims | `Use repro-reviewer to check the three bugs the bot reported on this PR` |

The docs list all three forms. An @-mention "ensures that specific subagent runs rather than
leaving the choice to Claude", and `--agent` starts "a session where the main thread itself takes
on that subagent's tool restrictions and model".
([docs](https://code.claude.com/docs/en/sub-agents#invoke-subagents-explicitly))

## The rules it follows

| Rule | What it means in a review |
|---|---|
| Read-only by default | It doesn't edit, commit, check out, stash, install or push. Scratch scripts go in a `mktemp -d` folder outside the repo, deleted at the end. No external services, no credentials. It runs `git status` again at the end and removes only files its own runs left behind, and says so. |
| Pin the commit | It records `git rev-parse HEAD` and `git status --porcelain` first. The verdict names that SHA. |
| Reproduce every finding | Each finding has the smallest command that shows it, its exit code and the output, quoted. |
| Unreproduced is not a finding | A suspicion it couldn't reproduce goes under "Not reproduced" or "Not run", never under findings. |
| Test other people's claims | The PR text, the commit message, a bot comment or another review is a claim to run, not a fact. |
| A reproduced FIX beats an unreproduced PASS | One reproduced finding makes it FIX. If part of the change couldn't be run, it can't say PASS: the verdict is FIX and the fix is the missing evidence. |
| Say what it did not run | The "Not run" section is always there, with the reason and a command for someone who can run it. |
| Last line is the verdict | `VERDICT: PASS @ <sha>` or `VERDICT: FIX @ <sha>`, nothing after it. |

## Three example runs

`examples/make-sample-repo.sh` builds `tinyshop`, a tiny Python repo with one branch per planted
problem. The author, committer and dates are fixed, so the commit SHAs come out the same on every
machine and match the logs. The sample repo's own tests pass on all three branches: the problems
are ones the tests miss.

| Log | Branch @ SHA | Planted problem | What the agent did | Verdict |
|---|---|---|---|---|
| [`01-real-bug.log`](examples/01-real-bug.log) | `real-bug` @ `8bc7ede` | A "simpler" `split_bill` rounds once, so shares stop adding up. The commit message says they still do. | Ran `split_bill(100,3)` and got `[33, 33, 33] 99`, refuted the commit message, noted that the tests only check an even split. | FIX |
| [`02-false-alarm.log`](examples/02-false-alarm.log) | `false-alarm` @ `89771d2` | Adds a days unit to `parse_duration`. The prompt includes a bot comment claiming `parse_duration('90s')` returns 9. | Ran it, got `90`, marked the bot claim refuted with the output, ran edge inputs and the tests. | PASS |
| [`03-cannot-run.log`](examples/03-cannot-run.log) | `cannot-run` @ `2f9054f` | Receipt download links now default to 30 days. S3 presigned URLs are "Valid up to 7 days when you're using AWS Signature Version 4" ([AWS](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)), and only S3 itself can show the failure. | Confirmed the code passes 2592000 seconds, found boto3 missing and S3 off limits, and put the S3 check under "Not run" with the 7-day limit as the reason and a command to settle it. | FIX (missing evidence) |

In run 3 the agent cited the 7-day limit from memory (it has no web tool) and kept it out of the
findings. The AWS page above confirms the limit. The error the agent says to expect (status and
text) was not checked.

In all three runs Python wrote `__pycache__` folders into the sample repo. Each time the agent saw
them in its final `git status`, removed only those folders, and said so in the report.

Each log has the prompt, every tool call with the output the agent saw (long outputs cut at 80
lines), and the final report, as the agent wrote it. Home and temp folder paths and the local user
name are masked; other paths, such as where Python is installed, are left in. The runs used Claude Code 2.1.316 with `claude-opus-5-5`, on 1 Nov 2026.

To run them yourself (needs Claude Code signed in; the saved runs took 37 to 64 seconds each):

```bash
bash agents/repro-reviewer/examples/run-example.sh 01-real-bug     # or 02-false-alarm, 03-cannot-run
MODEL=sonnet bash agents/repro-reviewer/examples/run-example.sh 01-real-bug
```

The script builds a fresh sample repo in a temp folder, installs the agent there, and runs
`claude -p --agent repro-reviewer` isolated from your own setup: `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`
(no CLAUDE.md files), `--setting-sources project` (none of your hooks, plugins or output style),
`--strict-mcp-config` and `--disable-slash-commands`. `--permission-mode dontAsk` with
`--allowedTools Bash Read` lets it run commands without prompts and refuses everything else. A
model's runs differ from one try to the next, so yours will word things differently.

Offline checks (no network, no Claude Code): `python3 tests/test_repro_reviewer.py`. It checks the
definition's frontmatter, that the sample repo's SHAs and planted problems are as described, that
`render_log.py` masks paths and keeps the final report, and that each saved log ends with the
verdict in the table above at the branch's SHA. It doesn't re-run the agent or re-check the docs
quotes; those were checked by hand on 1 Nov 2026.

## How "read-only" is enforced, and where it isn't

| Layer | What it does |
|---|---|
| `tools: Read, Grep, Glob, Bash` | No Edit or Write tool. The docs' example with this list: "The subagent can't edit files, write files, or use any MCP tools". ([docs](https://code.claude.com/docs/en/sub-agents#restrict-which-tools-a-subagent-can-use)) |
| The prompt's rule 1 | Tells it not to change the repo through Bash either. This is an instruction, not a sandbox: Bash can still write files. |
| Your permission rules | For a hard block, add Bash deny rules such as `Bash(git push *)` to `permissions.deny`. "The rule applies to the main conversation and to subagents." ([docs](https://code.claude.com/docs/en/sub-agents#restrict-which-tools-a-subagent-can-use)) |

The file sets no `permissionMode`, so it "inherits the main conversation's permission mode".
If your session runs in `bypassPermissions`, `acceptEdits` or auto mode, the subagent runs in that
mode too. ([docs](https://code.claude.com/docs/en/sub-agents#permission-modes))

It doesn't set `isolation: worktree` either: that worktree is "branched by default from your
default branch rather than the parent session's `HEAD`", so the agent would review the wrong
commit. ([docs](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields))

`model: inherit` runs it on the same model as your session. Pick another with `sonnet`, `opus`,
`haiku`, `fable` or a full model ID. ([docs](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields))

## Limits

- A reproduction shows the behaviour on this machine at this SHA. It can't show production data,
  real services, or other platforms.
- A FIX for missing evidence means "unverified", not "broken". The "Not run" section says who can
  run what.
- It can still miss a bug: a PASS means every claim it was given, and every behaviour it found to
  check, ran clean. It doesn't mean nothing else is wrong.
- It doesn't install tools. If a test runner is missing it says so. In run 1 `pytest` wasn't
  installed, so it ran the same tests with Python's built-in `unittest` and said so under "Not run".

## Sources

Checked 1 Nov 2026.

- Claude Code, Create custom subagents: https://code.claude.com/docs/en/sub-agents
- AWS, Download and upload objects with presigned URLs: https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html

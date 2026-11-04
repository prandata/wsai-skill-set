# 5 prompts that make Claude Code prove its work

The five prompts from the What Survives in AI Short, word for word, each with what it makes Claude Code prove.

| # | Prompt | What it makes Claude Code prove |
| :- | :- | :- |
| 1 | Run it, don't read it | That a claim is true, by running a command and showing its output |
| 2 | Failing test first | That the new test catches the bug, because it failed before the fix |
| 3 | Stop at the first failure | That a red test or command is reported, not worked around |
| 4 | Ask for a "Not checked" list | Which claims were checked by running something, and which were not |
| 5 | A reviewer subagent | That each review finding was reproduced before it was reported |

## 1. Run it, don't read it

```text
Don't answer from reading the code. Run a command that proves it, and paste the command and its exact output.
```

It makes Claude Code prove a claim by running something. You get the command and its real output, not a summary of what the code seems to do.

## 2. Failing test first

```text
Before you change any code, write a test for that, run it, and paste the failing output.
```

It makes Claude Code prove the test catches the bug. A test that failed before the fix and passes after it is a test of that bug.

## 3. Stop at the first failure

```text
If any command fails, stop and show me the error. Don't change the code or the test to make it pass.
```

It makes Claude Code prove it did not hide a failure. It shows you the error instead of editing the code or the test until the run goes green, and it does not commit on red.

## 4. Ask for a "Not checked" list

```text
End with a list headed "Not checked" of every claim you could not verify by running something.
```

It makes Claude Code separate what it ran from what it only believes. A guess can't pass for a tested fact when it has to be listed.

## 5. A reviewer subagent

```text
claude --agent repro-reviewer
```

Put [`repro-reviewer.md`](../agents/repro-reviewer/repro-reviewer.md) in `.claude/agents/` first. It runs the whole session as a read-only reviewer that may only report what it has reproduced, so a finding from a lint bot or another reviewer is run before it is believed or refuted. The file is free and MIT licensed; its own README is [`agents/repro-reviewer/README.md`](../agents/repro-reviewer/README.md).

## About the runs in the Short

Each prompt was run once, on 3 Nov 2026, with Claude Code 2.1.317 and the Sonnet model, on a sample repo with planted bugs. A model's runs differ from one try to the next, so yours will differ. Prompt 3 stopped on a missing `python` command the first time, before any test ran, so name your test command in the same prompt (for example `python3 -m unittest`).

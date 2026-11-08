# Overnight agent loop with a handoff file

Run Claude Code on one bounded task while you sleep. Each session stops cleanly at a time or
spend limit, leaves a `HANDOFF.md` (state, done, next, open questions), and the next session
resumes from that file instead of from a long transcript. A resume check refuses to start if the
last handoff is malformed.

It builds on our post [Long agent runs need a handoff](https://whatsurvivesinai.substack.com/p/long-running-agents-need-a-handoff):
saved progress, clear permissions and a safe way to resume, not a longer prompt.

| File | What it is |
|---|---|
| [`run.py`](run.py) | The loop. Runs `claude -p` sessions one after another until the task is done or a limit is hit. |
| [`check_handoff.py`](check_handoff.py) | The resume check. Exit 0 if `HANDOFF.md` is well formed, exit 1 with every problem listed if not. |
| [`HANDOFF.template.md`](HANDOFF.template.md) | The handoff format. `--init` copies it into your work folder. |
| [`sample/`](sample/) | A tiny task: tidy a messy `TODO.md` in four steps. |
| [`demo.sh`](demo.sh) | Runs the sample twice: run 1 interrupted, run 2 resumes. Logs in [`sample/logs/`](sample/logs/). |

Needs Python 3.9 or later (standard library only) and Claude Code v2.1.259 or later, signed in.
Offline tests: `python3 tests/test_overnight_handoff.py` from the repo root (58 cases, a fake
`claude`, no spend).

## 5-minute setup

```bash
git clone https://github.com/prandata/wsai-skill-set
cd wsai-skill-set/loops/overnight-handoff

# 1. Make a work folder with a TASK.md: numbered steps, and the files the agent may edit.
mkdir -p ~/overnight/todo-repo && cp sample/TASK.md sample/TODO.md ~/overnight/todo-repo/

# 2. Dry run first: creates HANDOFF.md, runs the resume check, prints the exact claude command
#    and prompt. Calls nothing and spends nothing.
python3 run.py ~/overnight/todo-repo --init --dry-run --model sonnet

# 3. A short real run with tight limits. Watch it once before you leave it overnight.
python3 run.py ~/overnight/todo-repo --model sonnet --max-sessions 1 --budget-usd 0.50

# 4. Stop it any time from another terminal. The session ends its turn and the loop exits.
touch ~/overnight/todo-repo/STOP

# 5. Overnight: remove the STOP file from step 4 (while it exists the loop exits at once),
#    start it before bed with a wall-clock limit, read HANDOFF.md in the morning.
rm -f ~/overnight/todo-repo/STOP
python3 run.py ~/overnight/todo-repo --hours 7 --total-budget-usd 5 >> ~/overnight/loop.log 2>&1
```

In the morning, read `HANDOFF.md`, check the changes yourself (`git diff` if the folder is a repo),
and commit and push by hand.

## How a run works

1. **Resume check.** `HANDOFF.md` must be well formed. If not, the loop refuses and says why. You fix it by hand.
2. **Status gate.** `done` means nothing to run. `blocked` means a person must answer the open question first.
3. **Limits.** It stops before starting a session if there is a `STOP` file, the loop's time is up, or one more session could pass the total spend limit.
4. **One fresh session.** `claude -p` gets a prompt that says: read `HANDOFF.md`, then the task file; do the next step; rewrite `HANDOFF.md` after every step. `--no-session-persistence` means there is no transcript to resume, so the handoff is the only memory.
5. **Watchdog.** If the session's time is up or a `STOP` file appears, the loop sends SIGINT, which ends the turn cleanly. SIGTERM and then SIGKILL follow only if the session has not exited after the grace period.
6. **After the session.** The resume check runs again. The loop records the outcome, turns and cost in `.overnight/runs.jsonl` and keeps the full JSON result in `.overnight/session-N.json`. A session that did not change `HANDOFF.md` stops the loop (exit 4), so a confused agent cannot spend the night repeating itself.

Exit codes: 0 done or stopped at a limit, 2 refused (missing or malformed handoff), 3 blocked, 4 no progress, 1 error.

## The handoff format

```markdown
# Handoff

Task: Tidy the TODO list
Status: in-progress
Run: 1
Updated: 2026-11-02T12:30:25Z

## State
Two to five lines on where things stand. Replaced each time, never appended.

## Done
- Step 1: one format

## Next
- Step 2: remove duplicates

## Open questions
- (none)
```

Status is one of `in-progress`, `done` or `blocked`. Run is the number of the session that last
wrote the file (`0` before the first session). Write nothing else on a header line: a trailing
comment makes the value invalid.

The resume check refuses the file if: the title or a header field is missing or repeated; Status is
not one of the three values; Run is not a whole number; Updated is not an ISO 8601 time; the four
sections are missing, repeated, out of order or joined by another section; State is empty; a line
under Done, Next or Open questions is not a `- ` item; a section has no items; Status is
`in-progress` with nothing under Next; Status is `blocked` with no question; a `{{placeholder}}` is
left; or the file is over 150 lines or 16,000 bytes (a handoff that keeps growing is turning into a transcript).

Only the four exact headings (`## State`, `## Done`, `## Next`, `## Open questions`) start a section.
Any other line that begins with `## ` is text: State is free prose, and a sentence that wraps onto a
line such as `## Open and ## Done sections ...` is part of State. The same line is refused before the
first section or under Done, Next or Open questions, where every line must be a `- ` item. A State
line that is exactly one of the four headings counts as that section, so it is refused as a repeat.

## The claude command, and where each flag comes from

From the Claude Code docs, fetched 2 November 2026: [Run Claude Code programmatically](https://code.claude.com/docs/en/headless),
[CLI reference](https://code.claude.com/docs/en/cli-reference) and [How the agent loop works](https://code.claude.com/docs/en/agent-sdk/agent-loop).

| Flag | Why | Source |
|---|---|---|
| `-p` | Non-interactive: run the prompt, then exit. | headless |
| `--output-format json` | One JSON result with `subtype`, `num_turns`, `total_cost_usd` and `session_id`, which the loop logs. | headless, agent loop |
| `--max-budget-usd` | Stops the session once estimated spend reaches the cap (print mode only). | CLI reference |
| `--max-turns` | Caps agentic turns (print mode only); the session exits with an error at the limit. | CLI reference |
| `--tools Read,Edit,Write` | The only built-in tools the agent gets. No shell, so no `git push`. | CLI reference |
| `--disallowedTools Bash WebFetch WebSearch "mcp__*"` | A second lock: removes the shell, the web tools and every MCP tool. The loop leaves out of this list any tool you add to `--tools` on purpose. | CLI reference |
| `--permission-mode acceptEdits` | File edits in the work folder run without a prompt. | headless |
| `--permission-prompts none` | Nobody is awake to answer, so anything that would prompt is denied and Claude is told not to retry. Needs v2.1.259 or later. | headless |
| `--setting-sources project` | Loads only the work folder's settings files, not your user settings in `~/.claude`, so hooks and plugins you set there stay out. | CLI reference |
| `--strict-mcp-config` | No MCP servers unless you pass `--mcp-config`. | CLI reference |
| `--no-session-persistence` | Sessions are not saved and cannot be resumed: the handoff is the only memory. | CLI reference |

The docs recommend `--bare` for scripted calls. It skips hooks, plugins, MCP servers, auto memory
and CLAUDE.md, but it never reads your subscription login, so it needs `ANTHROPIC_API_KEY`. If you
run on an API key, add `--bare` in `build_cmd()` in `run.py`.

## The sample, run twice

[`demo.sh`](demo.sh) copies `sample/` to a scratch folder and runs it twice on `sonnet`.

| | Run 1 ([log](sample/logs/run-1.txt)) | Run 2 ([log](sample/logs/run-2.txt)) |
|---|---|---|
| Starts from | the template (`Run: 0`) | run 1's handoff (`Run: 1`, Next: step 2) |
| What happened | Step 1 done and checkpointed after 21 s; the demo then created `STOP`; the loop sent SIGINT | Steps 2 to 4 done, each checkpointed; Status set to `done` |
| Ended | `STOP file` (result `error_during_execution`, exit 0), 7 turns | `success`, 10 turns, then `DONE` with no further session |
| Cost (Claude Code's estimate) | $0.0264 | $0.0462 |

On Claude Code v2.1.316, SIGINT ended the turn, the process exited with code 0, and the JSON result
still carried the turn count and cost. The docs say SIGTERM exits with code 143 and records no result
for the unfinished turn, which is why the loop sends SIGINT first.

## Limits

| Limit | What it means for you |
|---|---|
| **It costs money.** | Every session is billed to your Claude plan or API key. `--budget-usd` (default $1.00) caps each session and `--total-budget-usd` (default $5.00) caps the loop. The caps use Claude Code's client-side estimate, which can differ from your bill, and the docs say spend can pass the cap by up to one model response, so leave headroom. If a session is killed without a result, the loop counts the full session cap as spent. |
| **No unattended pushes.** | The loop never runs git. The agent has no shell by default, so it cannot commit or push. If you add `Bash` to `--tools`, the loop warns you; add deny rules such as `Bash(git push *)` and still review before anything leaves your machine. |
| **Dry run first.** | Run `--dry-run` on every new task and read the prompt and command it prints. Then do one short watched run before the first overnight one. |
| **The check tests format, not truth.** | A well-formed handoff can still be wrong. The agent writes it. Read it, and check the files, before you trust Done. |
| **Work lost on a stop is one step at most.** | The agent checkpoints after each step. If a session stops mid-step, that step is redone next time, so write steps that are safe to repeat. |
| **One task, one folder.** | No parallel sessions and no locking. Don't run two loops on the same folder. |
| **Project settings still load.** | `--setting-sources project` loads the work folder's `.claude/settings.json`, hooks included. Only point it at folders you trust. |
| **Not a sandbox.** | `acceptEdits` and the tool list limit what the agent is offered. For untrusted tasks, run it in a container or VM. |

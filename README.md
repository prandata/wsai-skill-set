# What Survives in AI: Skill Set

**Tested shortcuts and Claude Code skills for people building with AI.** Every trick has a date it was last checked,
and every claim links to its source. From the [What Survives in AI](https://whatsurvivesinai.substack.com) newsletter.

⭐ Star the repo to get new skills as they land: a new tested trick every day.

## Install a skill (Claude Code)

```bash
git clone https://github.com/prandata/wsai-skill-set
cp -r wsai-skill-set/skills/claude-code-memory ~/.claude/skills/
cp -r wsai-skill-set/skills/ssh-key-audit ~/.claude/skills/
cp -r wsai-skill-set/skills/wsai-skill-set ~/.claude/skills/ && cp wsai-skill-set/tricks.yaml ~/.claude/skills/wsai-skill-set/
```

| Skill | What it does |
|---|---|
| [`claude-code-memory`](skills/claude-code-memory/SKILL.md) | Sets up the four files that stop Claude Code forgetting your project: CLAUDE.md, AGENTS.md, a skill, and a hook that blocks dangerous commands. |
| [`ssh-key-audit`](skills/ssh-key-audit/SKILL.md) | Read-only audit of the SSH keys on your GitHub account: which keys at `github.com/<you>.keys` have no `.pub` file on this machine, and which are DSA or RSA under 3072 bits. Changes nothing. 66 offline cases in `tests/test_ssh_key_audit.py`. |
| [`wsai-skill-set`](skills/wsai-skill-set/SKILL.md) | Gives your agent the verified and behaviour shortcuts in `tricks.yaml` (55 in the list rebuilt on 12 Nov 2026): change-one-word GitHub URLs, repo-to-AI-context tools, terminal one-liners. |

## Agents (Claude Code subagents)

```bash
mkdir -p .claude/agents && cp wsai-skill-set/agents/repro-reviewer/repro-reviewer.md .claude/agents/
```

| Agent | What it does |
|---|---|
| [`repro-reviewer`](agents/repro-reviewer/README.md) | Read-only code reviewer that must reproduce every finding before it reports it: each one comes with the command it ran and the quoted output, a claim it can't run blocks a PASS, and it ends with `VERDICT: PASS\|FIX @ <sha>`. Three saved example runs (a real bug, a false alarm, one it can't run) and offline checks in `tests/test_repro_reviewer.py`. |

## MCP servers

| Server | What it does |
|---|---|
| [`notes-readonly`](mcp/notes-readonly/README.md) | Lets Claude Code list, search and read one folder of your Markdown notes, and nothing else. No write tool; `../`, absolute paths and every symlink are refused; a per-file size cap. 99 lines on the official MCP Python SDK, 34 tests. Install: `claude mcp add --scope user --transport stdio notes -- uv run --script /path/to/server.py ~/notes`. |

## Templates

[`templates/claude-code-memory/`](templates/claude-code-memory/): copy-paste CLAUDE.md, AGENTS.md, SKILL.md and a
PreToolUse hook (`block-dangerous.sh` blocks recursive force-deletes of `/`, `~`, `*` and `.`, force-pushes, and shell commands that mention `.env`; 143 command cases in `tests/hook_cases.json`, 100 that must exit 2 and 43 that must exit 0, run by `tests/test_hook.py`, including quoting tricks, long flags and `bash -c`) plus a `permissions.deny` rule so the Read tool cannot open `.env` either.

## Loops

[`loops/overnight-handoff/`](loops/overnight-handoff/): run Claude Code on one bounded task overnight. Each `claude -p`
session stops cleanly at a time or spend limit and leaves a `HANDOFF.md` (state, done, next, open questions); the next
session resumes from it, and a resume check refuses to start if the handoff is malformed. No shell for the agent, no
git pushes, a dry run first. The sample was run twice, the first run interrupted; both logs are in the folder.

## The trick list

[`tricks.yaml`](tricks.yaml): every trick has a pattern or label (`how`), the URL or command the list prints (`try`), what you get, a status and `checked` (for a trick with a `check_url`, the date that URL last returned success; behaviour tricks have no `check_url` and keep a manual date).
A scheduled GitHub Action ([`.github/workflows/verify.yml`](.github/workflows/verify.yml)) runs [`scripts/verify.py`](scripts/verify.py) on every `check_url`, then rebuilds [`newsletter/full-list.md`](newsletter/full-list.md). [`newsletter/issue-01.md`](newsletter/issue-01.md) stays as published.
A failed check records `last_fail` and leaves the status as it is. The next failed check, while `last_fail` is still set, marks the trick `broken`, and the rebuilt list leaves it out. One later success clears `last_fail` and, when the status was `broken`, sets the status to `verified`.
On 12 Nov 2026 the published list has 55 shortcuts: 50 `verified` and 5 `behaviour`. T08 (Count a repo's lines of code, `ghloc.vercel.app`) is `broken`; `last_fail` is `2026-11-12 HTTP 402`, and `checked` is still 2026-10-30 because a failed check does not change `checked`. Five `partial` tricks are under "Testing next". The five `behaviour` tricks (T55 to T59) have no `check_url`, so their `checked` date is still 2026-10-30. The list's "tested on" line uses the `updated` date in `tricks.yaml` (`2026-11-12`), the date of that run.
The intro still says the video showed five links. That sentence, the five names, and the closing line about turning the list into a Claude skill are hardcoded in [`scripts/build_newsletter.py`](scripts/build_newsletter.py). On 12 Nov 2026 all five video links (T01, T02, T04, T09, T10) are in the list. The skill itself is [`skills/wsai-skill-set/`](skills/wsai-skill-set/SKILL.md).

## Contribute

Add a trick to `tricks.yaml` with `status: partial`, a `title`, a `try` (the URL or command) and a `check_url`, and open a PR. The newsletter build prints `title` and `try` for a partial trick. We promote it to `verified` once
we've seen it work in a browser. Claims need a source.

## How this is made

Pranjal writes What Survives in AI. AI agents help gather and check the material; he reviews what's published.

## Known limits of the hook

It is a guardrail, not a sandbox. It parses commands the way a shell does, but it does not run them, so it cannot see:

| Not covered | Example |
|---|---|
| Variables and command output | `d=/; rm -rf $d` |
| Other interpreters | `python3 -c "shutil.rmtree('/')"` |
| Encoded scripts run by another interpreter | `echo ... \| base64 -d \| python3` |
| Aliases and functions | `alias x='rm -rf /'` |

**Simple rule, on purpose:** any command whose program is a shell interpreter (`bash`, `sh`, `zsh`, `dash`, `ksh`, `eval`, `source`, `.`), and any heredoc into one, is blocked without looking inside. Intended blocks, because the program is a shell: `curl ... | bash` (and `| sh`, which also covers `echo ... | base64 -d | sh`), `. ~/.nvm/nvm.sh` and `source ~/.zshrc`. A command line that ends in `&&`, `;`, `||` or `|` continues on the next line, and that line is checked as a new command. Known false positives: `bash script.sh` (run `./script.sh`), `source .venv/bin/activate` (call `.venv/bin/python` directly), `sh -c '...'` in scripts.

For a hard block, use permission deny rules and the sandbox (see the Claude Code permissions and sandboxing docs). Deliberate obfuscation beyond these is out of scope by design.

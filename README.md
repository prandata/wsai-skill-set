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
| [`wsai-skill-set`](skills/wsai-skill-set/SKILL.md) | Gives your agent 55+ tested shortcuts: change-one-word GitHub URLs, repo-to-AI-context tools, terminal one-liners. |

## Agents (Claude Code subagents)

```bash
mkdir -p .claude/agents
for a in repro-reviewer test-writer security-reviewer docs-updater commit-writer; do
  cp wsai-skill-set/agents/$a/$a.md .claude/agents/
done
```

Copy the `<name>.md` files only; the READMEs and examples stay here. Claude Code scans `.claude/agents/` recursively ([docs](https://code.claude.com/docs/en/sub-agents#choose-the-subagent-scope)), so copying whole folders would put the READMEs among your agent definitions.

| Agent | What it does |
|---|---|
| [`repro-reviewer`](agents/repro-reviewer/README.md) | Read-only code reviewer that must reproduce every finding before it reports it: each one comes with the command it ran and the quoted output, a claim it can't run blocks a PASS, and it ends with `VERDICT: PASS\|FIX @ <sha>`. Three saved example runs (a real bug, a false alarm, one it can't run) and offline checks in `tests/test_repro_reviewer.py`. |
| [`test-writer`](agents/test-writer/README.md) | Writes unit tests for code that has none, runs them, and reports a failing test as a possible bug instead of weakening the test or editing the source. Sonnet. |
| [`security-reviewer`](agents/security-reviewer/README.md) | Read-only security review (`tools: Read, Grep, Glob`, so it can't run or edit anything): each issue with severity, `file:line`, the line quoted and the smallest fix. Sonnet. |
| [`docs-updater`](agents/docs-updater/README.md) | Brings README and docs in line with the code after a flag, command or name changes, citing the code line for each fix. Told to edit Markdown only. Sonnet. |
| [`commit-writer`](agents/commit-writer/README.md) | Writes one commit message for what is staged, in the repo's style, with no trailers, and leaves the commit to you. Haiku. Its README shows the permission rules that make "never commits" a hard block. |

Offline checks for the four list agents: `python3 tests/test_subagents.py`. Each was run once with Claude Code 2.1.317 on a made-up repo on 4 Nov 2026 (AEDT); their READMEs give the results and say which limits are tool limits and which are prompt rules.

## MCP servers

| Server | What it does |
|---|---|
| [`notes-readonly`](mcp/notes-readonly/README.md) | Lets Claude Code list, search and read one folder of your Markdown notes, and nothing else. No write tool; `../`, absolute paths and every symlink are refused; a per-file size cap. 99 lines on the official MCP Python SDK, 34 tests. Install: `claude mcp add --scope user --transport stdio notes -- uv run --script /path/to/server.py ~/notes`. |

## Templates

[`templates/claude-code-memory/`](templates/claude-code-memory/): copy-paste CLAUDE.md, AGENTS.md, SKILL.md and a
PreToolUse hook (`block-dangerous.sh` blocks recursive force-deletes of `/`, `~`, `*` and `.`, force-pushes, and shell commands that mention `.env`; 143 cases in `tests/test_hook.py`, including quoting tricks, long flags and `bash -c`) plus a `permissions.deny` rule so the Read tool cannot open `.env` either.

## The trick list

[`tricks.yaml`](tricks.yaml): every trick with how to use it, what you get, status and the date it was last checked.
A GitHub Action re-checks every link each morning ([`scripts/verify.py`](scripts/verify.py)); two failures in a row
mark a trick `broken`.

## Contribute

Add a trick to `tricks.yaml` with `status: partial` and a `check_url`, and open a PR. We promote it to `verified` once
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

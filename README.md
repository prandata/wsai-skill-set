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
| [`ssh-key-audit`](skills/ssh-key-audit/SKILL.md) | Read-only audit of the SSH keys on your GitHub account: which keys at `github.com/<you>.keys` have no `.pub` file on this machine, and which are DSA or RSA under 3072 bits. Changes nothing. 52 offline cases in `tests/test_ssh_key_audit.py`. |
| [`wsai-skill-set`](skills/wsai-skill-set/SKILL.md) | Gives your agent 55+ tested shortcuts: change-one-word GitHub URLs, repo-to-AI-context tools, terminal one-liners. |

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

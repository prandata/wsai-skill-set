# What Survives in AI: Skill Set

**Tested shortcuts and Claude Code skills for people building with AI.** Every trick has a date it was last checked,
and every claim links to its source. From the [What Survives in AI](https://whatsurvivesinai.substack.com) newsletter.

⭐ Star the repo to get new skills as they land: a new tested trick every day.

## Install a skill (Claude Code)

```bash
git clone https://github.com/prandata/wsai-skill-set
cp -r wsai-skill-set/skills/claude-code-memory ~/.claude/skills/
cp -r wsai-skill-set/skills/wsai-skill-set ~/.claude/skills/ && cp wsai-skill-set/tricks.yaml ~/.claude/skills/wsai-skill-set/
```

| Skill | What it does |
|---|---|
| [`claude-code-memory`](skills/claude-code-memory/SKILL.md) | Sets up the four files that stop Claude Code forgetting your project: CLAUDE.md, AGENTS.md, a skill, and a hook that blocks dangerous commands. |
| [`wsai-skill-set`](skills/wsai-skill-set/SKILL.md) | Gives your agent 55+ tested shortcuts: change-one-word GitHub URLs, repo-to-AI-context tools, terminal one-liners. |

## Templates

[`templates/claude-code-memory/`](templates/claude-code-memory/): copy-paste CLAUDE.md, AGENTS.md, SKILL.md and a
PreToolUse hook (`block-dangerous.sh` blocks recursive force-deletes of `/`, `~`, `*` and `.`, force-pushes, and shell commands that mention `.env`; 85 cases in `tests/test_hook.py`, including quoting tricks, long flags and `bash -c`) plus a `permissions.deny` rule so the Read tool cannot open `.env` either.

## The trick list

[`tricks.yaml`](tricks.yaml): every trick with how to use it, what you get, status and the date it was last checked.
A GitHub Action re-checks every link each morning ([`scripts/verify.py`](scripts/verify.py)); two failures in a row
mark a trick `broken`.

## Contribute

Add a trick to `tricks.yaml` with `status: partial` and a `check_url`, and open a PR. We promote it to `verified` once
we've seen it work in a browser. Claims need a source.

## How this is made

Pranjal writes What Survives in AI. AI agents help gather and check the material; he reviews what's published.

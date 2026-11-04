# Five free Claude Code skills, run for real

The five skills from the What Survives in AI Short "5 free Claude Code skills, run for real". We ran each one in Claude Code 2.1.316 (Sonnet) on test data in a sandbox on 3 Nov 2026. Three are ours, in this repo. Two are Anthropic's, from [anthropics/skills](https://github.com/anthropics/skills): we link to them and don't copy them here.

The skills are free. Claude Code is not: it needs a Claude plan or an API account.

| # | Skill | By, licence | What it did in our run |
|---|---|---|---|
| 1 | [`claude-code-memory`](../skills/claude-code-memory/SKILL.md) | What Survives in AI, MIT | Copied our [templates](../templates/claude-code-memory/) into a clean folder: CLAUDE.md, AGENTS.md, `.claude/settings.json`, a repo-conventions skill and a PreToolUse hook. It filled them from `package.json`, then piped the skill's test command into the hook: `rm -rf /` was blocked, exit 2 |
| 2 | [`ssh-key-audit`](../skills/ssh-key-audit/SKILL.md) | What Survives in AI, MIT | Read-only. On two throwaway test keys it found 1 GitHub key with no local `.pub` file and 1 old-type key (RSA 2048), exit 1. GitHub's reply was a saved test file, so no real account was queried |
| 3 | [`slack-gif-creator`](https://github.com/anthropics/skills/tree/main/skills/slack-gif-creator) | Anthropic, Apache-2.0 (its [LICENSE.txt](https://github.com/anthropics/skills/blob/main/skills/slack-gif-creator/LICENSE.txt)) | One prompt made a 128x128 emoji GIF, 14 frames, 30 KB, and the skill's validator passed it |
| 4 | [`skill-creator`](https://github.com/anthropics/skills/tree/main/skills/skill-creator) | Anthropic, Apache-2.0 (its [LICENSE.txt](https://github.com/anthropics/skills/blob/main/skills/skill-creator/LICENSE.txt)) | Wrote a new skill (`commit-message`), and the skill's `scripts/quick_validate.py` printed "Skill is valid!". Its full workflow also runs evals; we skipped them |
| 5 | [`wsai-skill-set`](../skills/wsai-skill-set/SKILL.md) | What Survives in AI, MIT | Asked about pallets/click, it returned three tested links: gitdiagram.com/pallets/click, gitingest.com/pallets/click and ossinsight.io/analyze/pallets/click. Our [tricks list](../tricks.yaml) notes that ossinsight growth charts undercount since March 2026 |

## Install all five

What we ran, from the project folder:

```bash
git clone --depth 1 https://github.com/prandata/wsai-skill-set
git clone --depth 1 https://github.com/anthropics/skills anthropic-skills
mkdir -p .claude/skills
cp -r wsai-skill-set/skills/claude-code-memory .claude/skills/
cp -r wsai-skill-set/skills/ssh-key-audit .claude/skills/
cp -r wsai-skill-set/skills/wsai-skill-set .claude/skills/
cp wsai-skill-set/tricks.yaml .claude/skills/wsai-skill-set/
cp -r anthropic-skills/skills/skill-creator .claude/skills/
cp -r anthropic-skills/skills/slack-gif-creator .claude/skills/
python3 -m venv .venv && .venv/bin/pip install -r .claude/skills/slack-gif-creator/requirements.txt
```

Use `.claude/skills/` for one project or `~/.claude/skills/` for all your projects ([Claude Code skills docs](https://code.claude.com/docs/en/skills)). slack-gif-creator needs Python with pillow, imageio, imageio-ffmpeg and numpy, which the last line installs. claude-code-memory's templates come with the wsai-skill-set clone, and Claude Code asks before it writes into `.claude/`.

On our Mac, each skill from an empty folder with no pip cache took: claude-code-memory 3.9 s, ssh-key-audit 2.6 s, wsai-skill-set 3.2 s, skill-creator 4.3 s, slack-gif-creator 62 s (55.5 s of it the Python setup; 25 to 34 s with a warm pip cache). A slower connection takes longer.

## Credit

slack-gif-creator and skill-creator are written by Anthropic and published in [anthropics/skills](https://github.com/anthropics/skills). That repo has no single top-level licence; these two skills are Apache-2.0 per their own LICENSE.txt. We tested them at anthropics/skills commit `ca45fc4` (28 Oct 2026). The three skills in this repo are MIT, like the rest of it.

More tested tools: [What Survives in AI](https://whatsurvivesinai.substack.com).

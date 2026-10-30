# Good and bad examples

Each file in `good/` has a matching file in `bad/`. The full explanation is in
`docs/claude-code-memory-deep-dive.md`. Sources were fetched on 31 Oct 2026.

**`dot-claude/` means `.claude/`.** The examples keep it under a plain name so they never act as live
config inside this repo. When you copy a good example into a project, rename `dot-claude/` to `.claude/`.

| File | good/ | bad/ | Main lesson | Source |
| :- | :- | :- | :- | :- |
| CLAUDE.md | `good/CLAUDE.md` | `bad/CLAUDE.md` | Short, concrete facts. No folder trees, no procedures, no "NEVER" rules it can't enforce | https://code.claude.com/docs/en/memory |
| AGENTS.md | `good/AGENTS.md` | `bad/AGENTS.md` | Commands and conventions for agents, not README copy | https://agents.md/ |
| SKILL.md | `good/dot-claude/skills/add-endpoint/` | `bad/dot-claude/skills/add-endpoint/` | Frontmatter on line 1, exact field names, a description with trigger words, under 500 lines | https://code.claude.com/docs/en/skills |
| Hook | `good/dot-claude/settings.json` and `good/dot-claude/hooks/protect-files.sh` | `bad/dot-claude/settings.json` and `bad/dot-claude/hooks/protect.sh` | Exact matcher, `$CLAUDE_PROJECT_DIR` path, `exit 2` to block, clean stdout | https://code.claude.com/docs/en/hooks-guide |

The `bad/` files are broken on purpose. Never copy them into a real project.

After copying a good hook script, make it executable: `chmod +x .claude/hooks/protect-files.sh`
(https://code.claude.com/docs/en/hooks-guide).

## How to check each one

| File | Check | Source |
| :- | :- | :- |
| CLAUDE.md | `/context`, then look under **Memory files**. Edit with `/memory` | https://code.claude.com/docs/en/memory |
| AGENTS.md | `/memory`, then look for its path | https://code.claude.com/docs/en/memory |
| All instruction files | `/doctor prompt-audit` (v2.1.283 or later) | https://code.claude.com/docs/en/memory |
| SKILL.md | Ask `What skills are available?`, then `claude plugin validate .claude/skills` | https://code.claude.com/docs/en/skills |
| Hooks | `/hooks`, then trigger it and press `Ctrl+O` | https://code.claude.com/docs/en/hooks-guide |

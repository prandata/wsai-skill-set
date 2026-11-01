---
name: claude-code-memory
description: Set up the template files that stop Claude Code forgetting a project - CLAUDE.md (under 200 lines), AGENTS.md shared with Codex and Cursor, a project skill, and a PreToolUse hook that blocks dangerous commands. Use when starting a repo with Claude Code, when Claude keeps repeating mistakes, or when the user asks for project memory, AGENTS.md, skills or hooks.
---

# Claude Code memory: template files

Templates live in `templates/claude-code-memory/` of github.com/prandata/wsai-skill-set. Every claim below is from
the official docs, checked 31 Oct 2026.

1. **CLAUDE.md**: read at the start of every session. Target under 200 lines; longer files reduce adherence.
   Write concrete rules ("Use 2-space indentation"), not vague ones. (code.claude.com/docs/en/memory)
2. **AGENTS.md**: the shared format that Codex, Cursor and many other agents read (agents.md). Claude Code can read
   AGENTS.md in place of CLAUDE.md; the template's CLAUDE.md also imports it with `@AGENTS.md`.
3. **A skill** (`.claude/skills/<name>/SKILL.md`): only the description is in context until the skill is used;
   the body loads on demand, so long reference material is cheap. (code.claude.com/docs/en/skills)
4. **A hook** (`.claude/settings.json`): CLAUDE.md is context, not enforced configuration. To block an action no
   matter what Claude decides, use a PreToolUse hook. Exit code 2 blocks the call and shows stderr to Claude.
   Set `"onFailure": "block"`: by default a hook that crashes or times out lets the command through (Claude Code
   v2.1.295+).
   (code.claude.com/docs/en/hooks)

## Steps

1. Copy the template files into the repo root, keeping paths:
   - `CLAUDE.md`
   - `AGENTS.md`
   - `.claude/settings.json`
   - `.claude/skills/repo-conventions/SKILL.md`
   - `.claude/hooks/block-dangerous.sh`
   - `.claude/hooks/block_dangerous.py` (the hook needs both hook files; with only the `.sh`, every Bash call is blocked)
2. Fill in the `<...>` placeholders from the repo's real commands (read package.json / Makefile / pyproject first).
3. `chmod +x .claude/hooks/block-dangerous.sh`, then test it:
   `echo '{"tool_input":{"command":"rm -rf /"}}' | .claude/hooks/block-dangerous.sh; echo $?` should print 2.
4. Keep CLAUDE.md under 200 lines; move part-of-the-codebase rules into a skill or `.claude/rules/`.

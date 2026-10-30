@AGENTS.md

<!--
CLAUDE.md template. Keep it under 200 lines.
Claude reads the imported AGENTS.md first, then the rest of this file.
Block-level HTML comments like this one are stripped before Claude sees the file.
Source: https://code.claude.com/docs/en/memory (checked 31 Oct 2026).
Put only facts Claude needs every session here. Procedures go in a skill.
Rules that must always hold go in a hook (see .claude/settings.json).
-->

# <Project name>

## Commands
- Install: `<e.g. bun install>`
- Test: `<e.g. bun test>`. Run it before every commit.
- Lint: `<command>`

## Conventions
<!-- Concrete enough to check: "Use 2-space indentation", not "format code properly". -->
- Use 2-space indentation.
- API handlers live in `src/api/handlers/`.

## Gotchas
<!-- Things Claude would not find by reading the code. -->
- <e.g. `bun test` needs Redis on port 6379.>

## Claude Code
<!-- Claude-only instructions. Shared rules go in AGENTS.md. -->
- <e.g. Use plan mode for changes under `src/billing/`.>

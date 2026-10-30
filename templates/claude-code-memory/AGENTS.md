# AGENTS.md

<!--
Shared instructions for every coding agent (https://agents.md/).
Plain Markdown, no required fields. Keep README content (for humans) out.
Claude Code reads this file through the @AGENTS.md import in CLAUDE.md.
Without that import, Claude reads AGENTS.md only when no CLAUDE.md or CLAUDE.local.md exists
(https://code.claude.com/docs/en/memory).
-->

## Setup commands
- Install deps: `<command>`
- Start dev server: `<command>`
- Run tests: `<command>`

## Code style
- <e.g. TypeScript strict mode>
- <e.g. Single quotes, no semicolons>

## Testing instructions
<!-- Agents run the checks you list here and fix failures before finishing. -->
- Run `<lint command>` and `<test command>` before committing.
- Add or update tests for the code you change.

## PR instructions
- Title format: `[<package>] <Title>`

## Don't
- Don't edit generated files in `dist/`.

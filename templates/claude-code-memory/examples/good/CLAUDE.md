@AGENTS.md

# Billing API

<!-- Owner: platform team. Review monthly. This comment is stripped before Claude reads the file. -->

## Commands
- Install: `bun install`
- Test: `bun test`. Run it before every commit.
- Lint: `bun run lint`

## Conventions
- Use 2-space indentation.
- API handlers live in `src/api/handlers/`.
- Money is stored as integer cents. Never floats.

## Gotchas
- `bun test` needs Redis on port 6379. Start it with `docker compose up redis`.
- Don't edit `src/generated/`. Run `bun run codegen` instead.

## Claude Code
- Use plan mode for changes under `src/billing/`.
- To add an endpoint, use the `/add-endpoint` skill.

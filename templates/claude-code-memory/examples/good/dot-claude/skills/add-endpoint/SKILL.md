---
name: add-endpoint
description: Add or change an HTTP API endpoint in this repo. Covers file location, naming, tests and route registration. Use when the user asks for a new endpoint, route or handler.
---

# Add an endpoint

Throughout this task, run `bun test` after every edit.

1. Create `src/api/handlers/<name>.ts` and export a handler.
2. Add `tests/api/<name>.test.ts`.
3. Register the route in `src/api/index.ts`.
4. Run `bun test` and fix failures before you finish.

## Additional resources
- For the error response format, see [reference.md](reference.md).

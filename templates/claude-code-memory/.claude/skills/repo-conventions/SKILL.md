---
name: repo-conventions
description: How to add a new API endpoint in this repo - folder, naming, tests and the checklist. Use when the user asks to add or change an endpoint.
---

# Adding an endpoint

Only this description sits in Claude's context until the skill is used; the body below loads when it's needed
(https://code.claude.com/docs/en/skills). So long reference material here costs almost nothing.

1. Create `src/api/<name>.ts`, export a handler.
2. Add a test in `tests/api/<name>.test.ts`.
3. Register the route in `src/api/index.ts`.
4. Run the tests.

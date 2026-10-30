# Project Instructions

<!-- BAD EXAMPLE. Each problem is explained in docs/claude-code-memory-deep-dive.md, section 1.3. -->

You are a world-class senior engineer. Always write clean, high-quality code and format it properly.
Keep files organized.

IMPORTANT: NEVER EVER run `rm -rf` or push to main. THIS IS CRITICAL.

Please read AGENTS.md before you start.

## Project structure
src/
  api/
    handlers/
      users.ts
      orders.ts
      invoices.ts
  generated/
  lib/
    db.ts
    money.ts
tests/
  api/
... (imagine 300 more lines of folder tree here)

## How to deploy (step by step)
1. Bump the version in package.json.
2. Run the changelog script.
3. Build the Docker image.
4. Tag it.
5. Push it.
... (imagine 35 more steps here)

## Style
- Use tabs.
- Write good tests.
- Use 2-space indentation.

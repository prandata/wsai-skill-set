---
name: wsai-skill-set
description: Tested shortcuts for people building with AI - change-one-word GitHub URLs, ways to hand a repo or docs to an AI, terminal one-liners and small builder tools. Use when you need to understand an unfamiliar repo fast, give an AI the full code or current docs of a library, inspect a package before installing it, or find a quick free tool for JSON, cron, regex, diagrams or API calls. Each trick carries the date it was last checked.
---

# What Survives in AI: Skill Set

The list lives in `tricks.yaml` next to this file (copy it in, or point at the repo checkout). Each entry has:
`how` (the URL or command), `you_get`, `status` (verified, partial, behaviour, broken), `checked` (last date it served),
`sign_in`, and an optional `note` with caveats.

## How to use it

1. Read `tricks.yaml` and pick by the user's need, using `category`:
   - `understand-a-repo`: diagrams, digests, in-browser editors, file history, forks.
   - `feed-your-ai`: pack a repo or docs into AI context (gitingest, repomix, context7, gitmcp).
   - `hidden-github-urls`: .patch, .diff, .keys, blame, compare, feeds.
   - `notebooks-and-packages`, `terminal`, `builder-tools`, `browser`.
2. Prefer `verified`. Say so when you suggest a `partial` one. Never suggest `broken`.
3. Swap the user's `owner/repo` into the URL. Fetch it yourself when you can, rather than only naming it.
4. Repeat any `note` (for example, ossinsight's growth charts undercount since March 2026).
5. If a trick fails for you, tell the user and note it, so the maintainer can re-check it.

## Example

"Help me understand pallets/click before I change it":
- read the architecture: `https://gitdiagram.com/pallets/click`
- fetch the one-page digest: `https://gitingest.com/pallets/click`
- check recent activity: `https://ossinsight.io/analyze/pallets/click`

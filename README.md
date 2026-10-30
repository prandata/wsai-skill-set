# What Survives in AI: Skill Set

The one source of truth for the tricks in the daily **Skill Set** videos and the What Survives in AI newsletter
(whatsurvivesinai.substack.com). Mission: help people building with AI tools get ahead.

| File | What it is |
|---|---|
| `tricks.yaml` | Every trick: how, what you get, status, date last checked, caveats, which video used it. |
| `scripts/verify.py` | Re-checks every link and updates `tricks.yaml` (two failures in a row mark a trick `broken`). |
| `scripts/build_newsletter.py` | Builds the full-list post from `tricks.yaml` in the newsletter's house format. |
| `newsletter/full-list.md` | The latest generated post. |
| `skill/wsai-skill-set/` | A Claude skill: drop it in `~/.claude/skills/` with `tricks.yaml` and your agent can use the list. |

## The daily loop

1. **Verify:** `python3 scripts/verify.py` (also runs every morning in GitHub Actions).
2. **Pick:** choose the day's tricks from `verified` entries not yet in `used_in`, best `punch` first.
3. **Shoot-day check:** run each chosen trick in a real (headless) browser. A page that loads is not proof it works.
4. **Video:** make it with the `split-stack-explainer` skill. Then add the slug to `used_in`.
5. **Newsletter:** `python3 scripts/build_newsletter.py > newsletter/full-list.md`, then stage it in Substack
   (`substack-staging` skill in whatsurvivesinai-desk). It's published without email; the social posts say
   "Comment TRICKS and I'll DM you the full list" and link here.

## Adding a trick

Add an entry to `tricks.yaml` with `status: partial` and a `check_url`, open a PR, and promote it to `verified` only
after you have seen the result work in a browser. Every number or claim in `note` needs a source you opened.

## Status of this repo

Private for now. Opening it to the public, so readers can star it and send PRs, is the owner's decision.

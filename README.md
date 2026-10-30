# What Survives in AI: Skill Set

The one source of truth for the tricks in the daily **Skill Set** videos and the What Survives in AI newsletter
(whatsurvivesinai.substack.com). Mission: help people building with AI tools get ahead.

| File | What it is |
|---|---|
| `tricks.yaml` | Every trick: `try` and `reader` (what to show), how, what you get, status, date last checked, caveats, and `used_in` (video slug and issue id). |
| `scripts/verify.py` | Re-checks every link and updates `tricks.yaml` (two failures in a row mark a trick `broken`). |
| `scripts/build_newsletter.py` | Builds the full-list post from `tricks.yaml` in the newsletter's house format. |
| `scripts/build_issue.py` | Builds one issue from the tricks whose `used_in` lists that issue id. |
| `newsletter/full-list.md` | The latest generated full list. |
| `newsletter/issue-01.md` | The generated day-one issue: the video's five tricks, plus five more. |
| `skill/wsai-skill-set/` | A Claude skill: drop it in `~/.claude/skills/` with `tricks.yaml` and your agent can use the list. |

## The daily loop

1. **Verify:** `python3 scripts/verify.py`. The same check runs every morning in GitHub Actions, which commits `tricks.yaml` and a rebuilt `newsletter/full-list.md`. It does not rebuild the issue.
2. **Pick:** choose the day's tricks from `verified` entries not yet in `used_in`, best `punch` first.
3. **Shoot-day check:** run each chosen trick in a real (headless) browser. A page that loads is not proof it works.
4. **Video:** make it with the `split-stack-explainer` skill. On each trick that aired, add the video slug (for example `skill-set-01`) to `used_in`.
5. **Issue:** also add the issue id (for example `issue-01`) to `used_in` on the day's tricks, including extras that are not in the video. Then `python3 scripts/build_issue.py issue-01 > newsletter/issue-01.md`.
6. **Full list:** `python3 scripts/build_newsletter.py > newsletter/full-list.md`, then stage it in Substack
   (`substack-staging` skill in whatsurvivesinai-desk). It's published without email; the social posts say
   "Comment TRICKS and I'll DM you the full list" and link here.

## Adding a trick

Add an entry to `tricks.yaml` with `status: partial` and a `check_url`, open a PR, and promote it to `verified` only
after you have seen the result work in a browser. Every number or claim in `note` needs a source you opened.

## Status of this repo

Private for now. Opening it to the public, so readers can star it and send PRs, is the owner's decision.

#!/usr/bin/env python3
"""Build one newsletter issue: the tricks tagged with that issue in `used_in` (house format).

  python3 scripts/build_issue.py issue-01 > newsletter/issue-01.md

Video tricks (also tagged skill-set-NN) come first, in video order; then the extra picks.
Images: `assets/shot-<page>.png` is used when a trick lists `shot:`. The full list stays in the repo for later issues."""
import sys, yaml, datetime
from pathlib import Path

D = yaml.safe_load((Path(__file__).resolve().parent.parent / "tricks.yaml").read_text())
VIDEO_ORDER = ["T01", "T02", "T09", "T04", "T10"]
SHOT = {"T01": ("shot-gitdiagram.png", "gitdiagram.com draws the architecture of pallets/click."),
        "T02": ("shot-gitingest.png", "gitingest: (1) the summary with a token estimate, (2) the file tree, (3) Copy all, ready to paste into your AI."),
        "T09": ("shot-ossinsight.png", "OSS Insight: (1) the star total, which is accurate, (2) its own warning that growth charts undercount since March 2026."),
        "T04": ("shot-github1s.png", "github1s: (1) the file explorer, (2) the editor. No sign-in, no clone."),
        "T10": ("shot-githistory.png", "Git History: (1) every commit to the README, replayed one by one.")}

def nice(d): return datetime.date.fromisoformat(str(d)).strftime("%-d %b %Y")

def block(n, t):
    out = [f"#### {n}. {t['title']}.", "", f"`{t['try']}`", "", t["reader"]]
    if t.get("note"): out += ["", f"=={t['note']}=="]
    if t["id"] in SHOT:
        f, cap = SHOT[t["id"]]; out += ["", f"![{t['title']}](assets/{f})", "", f"Caption: {cap}"]
    return out + [""]

def main(issue):
    tr = [t for t in D["tricks"] if issue in t.get("used_in", [])]
    vid = sorted([t for t in tr if t["id"] in VIDEO_ORDER], key=lambda t: VIDEO_ORDER.index(t["id"]))
    more = [t for t in tr if t["id"] not in VIDEO_ORDER]
    total = len([t for t in D["tricks"] if t["status"] in ("verified", "behaviour")])
    when = nice(D["updated"])
    o = ["[[META]]", f"Title: {len(tr)} links that feel illegal.",
         f"Subtitle: The five from today's video, plus five more for AI builders. Tested {when}.",
         "Audience: everyone", "Email: do not send", "Cover / social image: assets/cover.png", "Tags: skill set, github, tools", "[[/META]]", "",
         "You are building with AI.", "", "You open a repo you did not write.", "",
         "You need to understand it in five minutes, not five hours.", "", "Most people clone it, scroll, and give up.", "",
         "You can change one word in the URL instead.", "",
         "![Five GitHub links from today's Skill Set video](assets/cover.png)", "", "Caption: From today's video. The repo is pallets/click, drawn by gitdiagram.com.", "",
         f"This issue has =={len(tr)} tested links:== the five from the video, with screenshots, and five more that help when you build with AI.", "",
         "Save it. You will need it the day you open a strange repo.", "", "[[BUTTON: Share]]", "",
         "[[CENTER]] Know a builder who clones whole repos for one file? Send them this.", "", "---", "",
         "[[CALLOUT]]", "**How this is made.** I write about building with AI: agents, workflows, and what works and what doesn't. "
         "I can't test all of it alone, so my AI agents help me pull the information together and run the checks. "
         "I review everything before it's published. The daily videos are AI-made too, because I can't film every one; I step in where it matters. Pranjal", "[[/CALLOUT]]", "",
         "## How we test.", "", f"Every link was checked on {when} against one public repo, `{D['test_repo']}`. Swap in your own `owner/repo`.", "",
         "==A page loading is not the same as a trick working.== We run each one in a browser before it goes in a video.", "", "---", "",
         "## The five from the video.", ""]
    for i, t in enumerate(vid, 1): o += block(i, t)
    o += ["---", "", "## Five more for AI builders.", "", "Not in the video. Each one saves you time on a repo or an AI task.", ""]
    for i, t in enumerate(more, len(vid) + 1): o += block(i, t)
    o += ["---", "", "## What's next.", "",
          f"We have tested {total - len(tr)} more. They come out a few at a time, with a new Skill Set video every day.", "",
          "Got here from a video? That is how it works: comment TRICKS on any Skill Set video and I'll DM you that day's list.", "",
          "Here, comment with the trick you use most. The best ones go in the next issue.", "", "[[BUTTON: Comment]]", "",
          "[[BUTTON: Subscribe]]", "", "[[CENTER]] Free while we grow. Tested, dated, no affiliate links.", ""]
    print("\n".join(o))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "issue-01")

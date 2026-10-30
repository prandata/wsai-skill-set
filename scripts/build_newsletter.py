#!/usr/bin/env python3
"""Build the full Skill Set list post (What Survives house format) from tricks.yaml.

  python3 scripts/build_newsletter.py > newsletter/full-list.md

Verified and behaviour tricks go in the list; partial ones go under "Testing next"; broken ones are left out."""
import yaml, datetime
from pathlib import Path

D = yaml.safe_load((Path(__file__).resolve().parent.parent / "tricks.yaml").read_text())
SECTIONS = [
    ("understand-a-repo", "Understand any repo in minutes.", "You will open code you did not write every week. These turn an hour of scrolling into a few minutes."),
    ("feed-your-ai", "Give your AI the real code and docs.", "An AI tool is only as good as the context you give it. These pack repos and docs so Claude, ChatGPT or Cursor sees the real thing."),
    ("hidden-github-urls", "Hidden GitHub URLs.", "GitHub answers more URLs than its buttons show. Add a suffix and get plain text, feeds or images."),
    ("notebooks-and-packages", "Notebooks and packages.", "Know what you are installing before you install it."),
    ("terminal", "Terminal one-liners.", "No install. Paste into any terminal."),
    ("builder-tools", "Everyday builder tools.", "Small free tools that each save an hour."),
    ("browser", "Browser tricks.", "Already in your browser. Nothing to install."),
]

def nice(d): return datetime.date.fromisoformat(str(d)).strftime("%-d %b %Y")

def line(t):
    s = f"- **#{t['n']} {t['title']}.** `{t['try']}`. {t['reader']}"
    if t.get("note"): s += f" =={t['note']}=="
    return s

def main():
    tr = D["tricks"]; live = [t for t in tr if t["status"] in ("verified", "behaviour")]
    order = [k for k, _, _ in SECTIONS]; live.sort(key=lambda t: order.index(t["category"]))
    for i, t in enumerate(live, 1): t["n"] = i
    SHORT = {'T01': 'gitdiagram', 'T02': 'gitingest', 'T09': 'OSS Insight', 'T04': 'github1s', 'T10': 'Git History'}
    vid = sorted([t for t in live if "skill-set-01" in t.get("used_in", [])], key=lambda t: list(SHORT).index(t["id"]))
    for t in vid: t["short"] = SHORT[t["id"]]
    toc = [f"- **{title.rstrip('.')}:** #{min(t['n'] for t in live if t['category']==k)} to #{max(t['n'] for t in live if t['category']==k)}" for k, title, _ in SECTIONS if any(t['category']==k for t in live)]
    out = ["[[META]]", f"Title: {len(live)} shortcuts for AI builders.",
           f"Subtitle: Repos, AI context, terminal and browser tricks. Every one tested on {nice(D['updated'])}.",
           "Audience: everyone", "Email: do not send", "Cover / social image: assets/cover.png", "Tags: skill set, github, tools", "[[/META]]", "",
           "You are building with AI.", "", "You open a repo you did not write.", "",
           "You need to understand it in five minutes, not five hours.", "", "Most people clone it, scroll, and give up.", "",
           "You can change one word in the URL instead.", "",
           "![Five GitHub links from today's Skill Set video](assets/cover.png)", "", "Caption: From today's video. The repo is pallets/click, drawn by gitdiagram.com.", "",
           "Today's Skill Set video showed five of these links.", "",
           f"This post has all of them: =={len(live)} tricks, numbered, every one tested.==", "",
           "**The five from the video:** " + ", ".join(f"{t['short']} (#{t['n']})" for t in vid) + ". The other " + str(len(live) - len(vid)) + " are new.", "",
           "**What's inside:**", ""] + toc + ["",
           "Save this post. You will need it the day you open a strange repo.", "", "[[BUTTON: Share]]", "",
           "[[CENTER]] Know a builder who clones whole repos for one file? Send them this.", "", "---", "",
           "## How we test.", "",
           f"Every link was checked on {nice(D['updated'])} against one public repo, `{D['test_repo']}`. Swap in your own `owner/repo`.", "",
           "==A page loading is not the same as a trick working.== Before a trick goes in a video, we run it in a browser.", "",
           "Sites change. If one breaks, tell us in the comments and we fix the list.", "", "---", ""]
    for n, (key, title, intro) in enumerate(SECTIONS, 1):
        items = [t for t in live if t["category"] == key]
        if not items: continue
        out += [f"## {n}. {title}", "", intro, ""] + [line(t) for t in items] + [""]
    nxt = [t for t in tr if t["status"] == "partial"]
    if nxt:
        out += ["---", "", "## Testing next.", "", "These load, but we have not seen the full result work yet. They join the list once we have:", ""]
        out += [f"- **{t['title']}:** `{t['try']}`" for t in nxt] + [""]
    out += ["---", "", "## What's next.", "",
            "A new Skill Set video every day, and this list grows with it.", "",
            "We are also turning the list into a Claude skill, so your agent knows these tricks too.", "",
            "Comment with the trick you use most. The best ones go in the next issue.", "", "[[BUTTON: Comment]]", "",
            "[[BUTTON: Subscribe]]", "", "[[CENTER]] Free while we build the list. Tested, dated, no affiliate links.", ""]
    print("\n".join(out))

if __name__ == "__main__":
    main()

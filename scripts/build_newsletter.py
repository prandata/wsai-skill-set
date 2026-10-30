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
    how = t["how"].replace("->", "→")
    s = f"- **{t['name']}:** `{how}`. {t['you_get']}."
    if t.get("sign_in") and not t["sign_in"].lower().startswith("no"):
        s += f" Sign-in: {t['sign_in']}."
    if t.get("note"): s += f" =={t['note']}==" if t["id"] == "T09" else f" {t['note']}"
    return s

def main():
    tr = D["tricks"]; live = [t for t in tr if t["status"] in ("verified", "behaviour")]
    out = ["[[META]]", "Title: Links that feel illegal.",
           f"Subtitle: {len(live)} tricks for people building with AI, each tested on {nice(D['updated'])}:",
           "Audience: everyone", "Email: do not send", "Cover / social image: assets/cover.png", "Tags: skill set, github, tools", "[[/META]]", "",
           "You are building with AI.", "", "You open a repo you did not write.", "",
           "You need to understand it in five minutes, not five hours.", "", "Most people clone it, scroll, and give up.", "",
           "You can change one word in the URL instead.", "",
           "![Five GitHub links from today's Skill Set video](assets/cover.png)", "Caption: From today's video. The repo is pallets/click, drawn by gitdiagram.com.", "",
           f"This is the full Skill Set list: =={len(live)} tricks, every one tested, in one place.==", "",
           "- **Read any repo fast.** Diagrams, one-file digests, editors in the browser.",
           "- **Hand it to your AI.** Pack repos and docs so your assistant sees the real thing.",
           "- **Small tools that save an hour.** Terminal one-liners, JSON, cron, regex.", "",
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
        out += [f"- **{t['name']}:** `{t['how'].replace('->', '→')}`." for t in nxt] + [""]
    out += ["---", "", "## What's next.", "",
            "A new Skill Set video every day, and this list grows with it.", "",
            "We are also turning the list into a Claude skill, so your agent knows these tricks too.", "",
            "Comment with the trick you use most. The best ones go in the next issue.", "", "[[BUTTON: Comment]]", "",
            "[[BUTTON: Subscribe]]", "", "[[CENTER]] Free while we build the list. Tested, dated, no affiliate links.", ""]
    print("\n".join(out))

if __name__ == "__main__":
    main()

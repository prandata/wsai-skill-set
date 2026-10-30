[[META]]
Title: Links that feel illegal.
Subtitle: 55 tricks for people building with AI, each tested on 30 Oct 2026:
Audience: everyone
Email: do not send
Cover / social image: assets/cover.png
Tags: skill set, github, tools
[[/META]]

You are building with AI.

You open a repo you did not write.

You need to understand it in five minutes, not five hours.

Most people clone it, scroll, and give up.

You can change one word in the URL instead.

![Five GitHub links from today's Skill Set video](assets/cover.png)
Caption: From today's video. The repo is pallets/click, drawn by gitdiagram.com.

This is the full Skill Set list: ==55 tricks, every one tested, in one place.==

- **Read any repo fast.** Diagrams, one-file digests, editors in the browser.
- **Hand it to your AI.** Pack repos and docs so your assistant sees the real thing.
- **Small tools that save an hour.** Terminal one-liners, JSON, cron, regex.

Save this post. You will need it the day you open a strange repo.

[[BUTTON: Share]]

[[CENTER]] Know a builder who clones whole repos for one file? Send them this.

---

## How we test.

Every link was checked on 30 Oct 2026 against one public repo, `pallets/click`. Swap in your own `owner/repo`.

==A page loading is not the same as a trick working.== Before a trick goes in a video, we run it in a browser.

Sites change. If one breaks, tell us in the comments and we fix the list.

---

## 1. Understand any repo in minutes.

You will open code you did not write every week. These turn an hour of scrolling into a few minutes.

- **Change one word: diagram the repo:** `github.com/pallets/click → gitdiagram.com/pallets/click`. An interactive architecture diagram.
- **Repo as one AI-ready text file:** `github.com/... → gitingest.com/pallets/click`. Token count plus a full text digest.
- **Press `.` on any repo:** `github.com/pallets/click → github.dev/pallets/click`. Full VS Code in the tab. Sign-in: GitHub login for some features; browsing works.
- **Add "1s":** `github.com → github1s.com/pallets/click`. VS Code without any login.
- **vscode.dev prefix:** `vscode.dev/github/pallets/click`. VS Code from a URL.
- **Repo analytics:** `ossinsight.io/analyze/pallets/click`. Stars and contributor charts, world map. ==Its own page warns growth figures undercount since March 2026: trust the totals, not the trend lines.==
- **Animated file history:** `github.com/... → github.githistory.xyz/pallets/click/blob/main/README.md`. Commits sliding in as an animation.
- **Find the forks that matter:** `useful-forks.github.io/?repo=pallets/click`. Forks ranked by stars and commits ahead. Without a GitHub token the rate limit is low.
- **Download one folder only:** `download-directory.github.io/?url=<folder url>`. A zip of a single folder.

## 2. Give your AI the real code and docs.

An AI tool is only as good as the context you give it. These pack repos and docs so Claude, ChatGPT or Cursor sees the real thing.

- **Swap to gitmcp:** `github.com → gitmcp.io/pallets/click`. An MCP server URL for any repo, plus a chat.
- **raw. subdomain:** `github.com/.../blob/... → raw.githubusercontent.com/pallets/click/main/README.md`. Bare file text.
- **Any repo file on a CDN:** `cdn.jsdelivr.net/gh/pallets/click@main/README.md`. The file served from a CDN.
- **Repo JSON:** `api.github.com/repos/pallets/click`. Stars (17,805), creation date, everything. 60 requests an hour without a token.
- **Context7:** `context7.com/pallets/click (+ /llms.txt)`. Up-to-date docs for an LLM.
- **Repomix web:** `repomix.com, paste the repo URL`. Repo packed into one AI file.
- **repo2txt:** `repo2txt.simplebasedomain.com`. Pick files, get one text file.

## 3. Hidden GitHub URLs.

GitHub answers more URLs than its buttons show. Add a suffix and get plain text, feeds or images.

- **.patch on a commit:** `.../commit/main → .../commit/main.patch`. A raw email-style patch.
- **.diff on a PR:** `.../pull/2800 → .../pull/2800.diff`. Plain diff text.
- **Anyone's SSH keys:** `github.com/<user>.keys`. The user's public SSH keys. Use a person's username; organisations have none.
- **Anyone's GPG keys:** `github.com/torvalds.gpg`. PGP block (torvalds: "no GPG keys").
- **Avatar by URL:** `github.com/torvalds.png`. The avatar image.
- **Blame view:** `.../blob/main/README.md → .../blame/main/README.md`. Who wrote every line.
- **Compare any two tags:** `.../compare/8.1.0...8.1.7`. Every change between releases.
- **Commit RSS feed:** `.../commits/main.atom (repo.atom gives 404)`. An RSS feed of commits. repo.atom gives 404; use /commits/main.atom.
- **Contribution chart image:** `ghchart.rshah.org/torvalds`. The green-square graph as an SVG.
- **Press `t` on a repo (file finder), `y` (permalink):** `GitHub keyboard shortcuts`. A fuzzy finder pops up.

## 4. Notebooks and packages.

Know what you are installing before you install it.

- **Notebook in Colab:** `github.com/... .ipynb → colab.research.google.com/github/...`. The notebook, ready to run. Sign-in: Google login to run.
- **nbviewer:** `nbviewer.org/github/...`. A clean rendered notebook.
- **Package-size truth:** `bundlephobia.com/package/react`. Bundle size and download time.
- **deps.dev:** `deps.dev/pypi/click`. Dependencies, licences, advisories.
- **PyPI JSON:** `pypi.org/pypi/click/json`. Latest version (8.5.0) as JSON.

## 5. Terminal one-liners.

No install. Paste into any terminal.

- **Explain any command:** `explainshell.com/explain?cmd=tar+-xzvf+a.tgz`. Each flag labelled.
- **cheat.sh in the terminal:** `curl cheat.sh/tar`. Instant tar examples.
- **Weather in the terminal:** `curl wttr.in/Sydney`. ASCII weather art.
- **QR code in the terminal:** `curl qrenco.de/github.com`. A scannable QR code in text.
- **Dancing parrot:** `curl parrot.live`. Animated party parrot.
- **Crypto rates in the terminal:** `curl rate.sx/btc`. ASCII price chart.

## 6. Everyday builder tools.

Small free tools that each save an hour.

- **HTTP cats:** `http.cat/404`. A cat photo for each status code.
- **Wayback prefix:** `web.archive.org/web/2010/github.com`. GitHub in 2010.
- **Cron, explained:** `crontab.guru/#*/5_*_*_*_*`. Plain English "every 5 minutes".
- **JSON as a graph:** `jsoncrack.com/editor`. Paste JSON, get a node graph.
- **Code screenshot:** `carbon.now.sh / ray.so`. Beautiful code images.
- **Live Mermaid:** `mermaid.live`. Text becomes a diagram as you type.
- **transform.tools:** `transform.tools`. JSON to TypeScript/Zod as you type.
- **regex101:** `regex101.com`. Matches highlighted, with an explanation.
- **caniuse:** `caniuse.com/css-has`. Browser support grid.
- **PageSpeed:** `pagespeed.web.dev, enter a URL`. Lighthouse scores.
- **Free private AI chat:** `duck.ai`. Multiple models, no account.
- **HuggingChat:** `huggingface.co/chat`. Open models in a chat. Sign-in: login for some features.
- **Live HTTP client:** `hoppscotch.io`. Postman in a tab.
- **Excalidraw:** `excalidraw.com`. A hand-drawn whiteboard.

## 7. Browser tricks.

Already in your browser. Nothing to install.

- **DevTools: `document.designMode="on"`:** `Console command`. Edit any page's text by typing.
- **DevTools: Ctrl+Shift+P > "Capture full size screenshot":** `DevTools command`. A full-page PNG.
- **Address bar: `data:text/html,<h1 contenteditable>`:** `Type into the URL bar`. An instant notepad.
- **Google `site:github.com "awesome" filetype:md`:** `search operators`. Curated lists.

---

## Testing next.

These load, but we have not seen the full result work yet. They join the list once we have:

- **Swap to gitpodcast:** `github.com → gitpodcast.com/pallets/click`.
- **Count lines of code:** `ghloc.vercel.app/pallets/click`.
- **Open repo in StackBlitz:** `stackblitz.com/github/<owner>/<repo>`.
- **Sourcegraph prefix:** `sourcegraph.com/github.com/pallets/click`.
- **npm dependency graph:** `npmgraph.js.org/?q=react`.
- **Google's Code Wiki:** `github.com/... → codewiki.google/github.com/pallets/click`.

---

## What's next.

A new Skill Set video every day, and this list grows with it.

We are also turning the list into a Claude skill, so your agent knows these tricks too.

Comment with the trick you use most. The best ones go in the next issue.

[[BUTTON: Comment]]

[[BUTTON: Subscribe]]

[[CENTER]] Free while we build the list. Tested, dated, no affiliate links.


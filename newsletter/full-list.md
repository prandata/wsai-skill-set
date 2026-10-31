[[META]]
Title: 55 shortcuts for AI builders.
Subtitle: Repos, AI context, terminal and browser tricks. Every one tested on 31 Oct 2026.
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

Today's Skill Set video showed five of these links.

This post has all of them: ==55 tricks, numbered, every one tested.==

**The five from the video:** gitdiagram (#1), gitingest (#2), OSS Insight (#6), github1s (#4), Git History (#7). The other 50 are new.

**What's inside:**

- **Understand any repo in minutes:** #1 to #9
- **Give your AI the real code and docs:** #10 to #16
- **Hidden GitHub URLs:** #17 to #26
- **Notebooks and packages:** #27 to #31
- **Terminal one-liners:** #32 to #37
- **Everyday builder tools:** #38 to #51
- **Browser tricks:** #52 to #55

Save this post. You will need it the day you open a strange repo.

[[BUTTON: Share]]

[[CENTER]] Know a builder who clones whole repos for one file? Send them this.

---

## How we test.

Every link was checked on 31 Oct 2026 against one public repo, `pallets/click`. Swap in your own `owner/repo`.

==A page loading is not the same as a trick working.== Before a trick goes in a video, we run it in a browser.

Sites change. If one breaks, tell us in the comments and we fix the list.

---

## 1. Understand any repo in minutes.

You will open code you did not write every week. These turn an hour of scrolling into a few minutes.

- **#1 Diagram any repo.** `gitdiagram.com/pallets/click`. Swap github.com for gitdiagram.com. You get an interactive architecture diagram.
- **#2 Turn a repo into one text page.** `gitingest.com/pallets/click`. Change github.com to gitingest.com. You get a summary, the file tree and every file, ready to paste into your AI.
- **#3 Press . on any repo.** `github.dev/pallets/click`. Pressing the full-stop key on a repo page opens it in VS Code in your browser. Some features need a GitHub sign-in.
- **#4 Add 1s for an editor.** `github1s.com/pallets/click`. Add 1s after github. The repo opens in VS Code, with no sign-in.
- **#5 Open a repo in vscode.dev.** `vscode.dev/github/pallets/click`. The same editor, from a URL.
- **#6 See a repo's health.** `ossinsight.io/analyze/pallets/click`. Stars, commits, issues, forks and contributors, charted. ==Its own page warns growth figures undercount since March 2026: trust the totals, not the trend lines.==
- **#7 Replay a file's history.** `github.githistory.xyz/pallets/click/blob/main/README.md`. Swap .com for .githistory.xyz on a file link. Every commit plays back like a movie.
- **#8 Find the forks that matter.** `useful-forks.github.io/?repo=pallets/click`. Forks ranked by stars and commits ahead. Sometimes the best version is a fork.
- **#9 Download one folder.** `download-directory.github.io`. Paste a folder link and get a zip of just that folder.

## 2. Give your AI the real code and docs.

An AI tool is only as good as the context you give it. These pack repos and docs so Claude, ChatGPT or Cursor sees the real thing.

- **#10 Make any repo an MCP server.** `gitmcp.io/pallets/click`. Swap github.com for gitmcp.io. You get an MCP address your AI tool can connect to.
- **#11 Get the raw file.** `raw.githubusercontent.com/pallets/click/main/README.md`. Just the file's text. Easy to paste or fetch.
- **#12 Serve any repo file from a CDN.** `cdn.jsdelivr.net/gh/pallets/click@main/README.md`. Any public file, from a free CDN.
- **#13 Get a repo as JSON.** `api.github.com/repos/pallets/click`. Stars, dates, licence and more, ready for a script.
- **#14 Current docs for your AI.** `context7.com/pallets/click`. Up-to-date library docs, with an llms.txt version for AI tools.
- **#15 Pack a repo for AI with Repomix.** `repomix.com`. Paste a repo URL and get one AI-ready file.
- **#16 Choose which files your AI sees.** `repo2txt.simplebasedomain.com`. Tick the files you want and get one text file.

## 3. Hidden GitHub URLs.

GitHub answers more URLs than its buttons show. Add a suffix and get plain text, feeds or images.

- **#17 Add .patch to a commit.** `github.com/pallets/click/commit/main.patch`. The commit as a plain patch.
- **#18 Add .diff to a pull request.** `github.com/pallets/click/pull/2800.diff`. The whole PR as plain diff text.
- **#19 Anyone's public SSH keys.** `github.com/torvalds.keys`. Add .keys to a username. Organisations have none.
- **#20 Anyone's public GPG keys.** `github.com/torvalds.gpg`. Add .gpg to a username.
- **#21 Anyone's avatar.** `github.com/torvalds.png`. Add .png to a username.
- **#22 See who wrote each line.** `github.com/pallets/click/blame/main/README.md`. Swap /blob/ for /blame/ in a file link.
- **#23 Compare two releases.** `github.com/pallets/click/compare/8.1.0...8.1.7`. Type two tags with three dots between them. You see every change.
- **#24 Follow commits by RSS.** `github.com/pallets/click/commits/main.atom`. An RSS feed of every new commit.
- **#25 Your contribution chart as an image.** `ghchart.rshah.org/torvalds`. The green-square chart as an SVG you can embed.
- **#26 GitHub's hidden hotkeys.** `press t, then y, on a repo page`. t opens a file finder. y turns the URL into a permanent link.

## 4. Notebooks and packages.

Know what you are installing before you install it.

- **#27 Run a GitHub notebook in Colab.** `colab.research.google.com/github/<owner>/<repo>/blob/main/<file>.ipynb`. Opens the notebook ready to run. Needs a Google sign-in to run.
- **#28 View any notebook cleanly.** `nbviewer.org/github/<owner>/<repo>/blob/main/<file>.ipynb`. For when GitHub won't render it.
- **#29 Check a package's size.** `bundlephobia.com/package/react`. How much an npm package adds to your app.
- **#30 X-ray a package.** `deps.dev/pypi/click`. Dependencies, licences and security advisories.
- **#31 Any Python package as JSON.** `pypi.org/pypi/click/json`. Latest version and metadata.

## 5. Terminal one-liners.

No install. Paste into any terminal.

- **#32 Explain any shell command.** `explainshell.com/explain?cmd=tar+-xzvf+a.tgz`. Every flag, labelled.
- **#33 Examples for any command.** `curl cheat.sh/tar`. Ready-to-copy examples in your terminal.
- **#34 Weather in the terminal.** `curl wttr.in/Sydney`. A forecast as text art.
- **#35 QR code in the terminal.** `curl qrenco.de/github.com`. A scannable QR code for any link.
- **#36 A dancing parrot.** `curl parrot.live`. No reason. Just joy. Press Ctrl+C to stop.
- **#37 Crypto prices in the terminal.** `curl rate.sx/btc`. A price chart as text.

## 6. Everyday builder tools.

Small free tools that each save an hour.

- **#38 A cat for every HTTP status.** `http.cat/404`. The easiest way to remember status codes.
- **#39 See any site years ago.** `web.archive.org/web/2010/github.com`. GitHub as it looked in 2010.
- **#40 Read a cron schedule.** `crontab.guru`. Type a cron line and read it in plain English.
- **#41 See JSON as a graph.** `jsoncrack.com/editor`. Paste JSON and get a map you can read.
- **#42 Good-looking code screenshots.** `carbon.now.sh`. Or ray.so. Clean images of your code.
- **#43 Diagrams by typing.** `mermaid.live`. Type text, get a diagram, live.
- **#44 JSON to types.** `transform.tools`. JSON to TypeScript or Zod as you type.
- **#45 Test a regex.** `regex101.com`. Matches highlighted and explained.
- **#46 Does it work in Safari?.** `caniuse.com/css-has`. Browser support for any web feature.
- **#47 Grade a site's speed.** `pagespeed.web.dev`. Lighthouse scores for any URL.
- **#48 Free AI chat, no account.** `duck.ai`. Several models, no sign-in.
- **#49 Open-source AI chat.** `huggingface.co/chat`. Open models in a chat. Some features need a sign-in.
- **#50 An API client in a tab.** `hoppscotch.io`. Send requests without installing anything.
- **#51 A whiteboard by URL.** `excalidraw.com`. Hand-drawn diagrams, free.

## 7. Browser tricks.

Already in your browser. Nothing to install.

- **#52 Edit any web page.** `document.designMode = "on"`. Paste into the browser console, then type on the page. Good for mock-ups.
- **#53 Full-page screenshot.** `DevTools → Cmd+Shift+P → "Capture full size screenshot"`. A full-page image with no extension.
- **#54 A notepad in the address bar.** `data:text/html,<h1 contenteditable>`. Type it into the address bar for an instant notepad.
- **#55 Find curated lists with Google.** `site:github.com "awesome" filetype:md`. Search operators that surface hand-picked lists.

---

## Testing next.

These load, but we have not seen the full result work yet. They join the list once we have:

- **Turn a repo into a podcast:** `gitpodcast.com/pallets/click`
- **Count a repo's lines of code:** `ghloc.vercel.app/pallets/click`
- **Run a JS repo in the browser:** `stackblitz.com/github/vitejs/vite`
- **Search code with Sourcegraph:** `sourcegraph.com/github.com/pallets/click`
- **See an npm dependency graph:** `npmgraph.js.org/?q=react`
- **Google's Code Wiki for a repo:** `codewiki.google/github.com/pallets/click`

---

## What's next.

A new Skill Set video every day, and this list grows with it.

We are also turning the list into a Claude skill, so your agent knows these tricks too.

Comment with the trick you use most. The best ones go in the next issue.

[[BUTTON: Comment]]

[[BUTTON: Subscribe]]

[[CENTER]] Free while we build the list. Tested, dated, no affiliate links.


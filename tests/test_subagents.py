"""Offline checks for the four list subagents: test-writer, security-reviewer, docs-updater, commit-writer.

1. Each file has the frontmatter Claude Code needs (name, description) plus the tools and model its README states.
2. The tool lists back the README's "enforced" claims: security-reviewer can't run or edit, docs-updater can't run
   commands or create files, and no file has a tool its README doesn't list.
3. Each README's install line copies that agent's own file.

No network, no Claude Code. Run: python3 tests/test_subagents.py
"""
import os, re, sys

here = os.path.dirname(os.path.abspath(__file__))
agents = os.path.join(here, "..", "agents")
EXPECT = {
    "test-writer": ("sonnet", ["Read", "Grep", "Glob", "Write", "Bash"]),
    "security-reviewer": ("sonnet", ["Read", "Grep", "Glob"]),
    "docs-updater": ("sonnet", ["Read", "Grep", "Glob", "Edit"]),
    "commit-writer": ("haiku", ["Bash", "Read"]),
}
fails = 0


def check(name, ok, detail=""):
    global fails
    print(("ok   " if ok else "FAIL ") + name + (f": {detail}" if detail and not ok else ""))
    fails += not ok


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return dict(line.split(": ", 1) for line in m.group(1).splitlines()) if m else {}


for name, (model, tools) in EXPECT.items():
    text = open(os.path.join(agents, name, f"{name}.md")).read()
    fm = frontmatter(text)
    check(f"{name}: name matches its folder", fm.get("name") == name, fm.get("name"))
    check(f"{name}: has a description", len(fm.get("description", "")) > 20)
    check(f"{name}: model is {model}", fm.get("model") == model, fm.get("model"))
    got = [t.strip() for t in fm.get("tools", "").split(",")]
    check(f"{name}: tools are {', '.join(tools)}", got == tools, ", ".join(got))
    readme = open(os.path.join(agents, name, "README.md")).read()
    check(f"{name}: README names the tool list", "tools: " + ", ".join(tools) in readme)
    check(f"{name}: README install line copies its own file",
          f"cp wsai-skill-set/agents/{name}/{name}.md .claude/agents/" in readme)
    check(f"{name}: no em or en dashes", not re.search("[–—]", text + readme))

tools = lambda n: frontmatter(open(os.path.join(agents, n, f"{n}.md")).read())["tools"]
check("security-reviewer can't run, edit or write", not {"Bash", "Edit", "Write"} & set(map(str.strip, tools("security-reviewer").split(","))))
check("docs-updater can't run commands or create files", not {"Bash", "Write"} & set(map(str.strip, tools("docs-updater").split(","))))
check("commit-writer can't edit or write files", not {"Edit", "Write"} & set(map(str.strip, tools("commit-writer").split(","))))

print(f"\n{'FAILED' if fails else 'passed'}: {fails} failure(s)")
sys.exit(1 if fails else 0)

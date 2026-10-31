# The four Claude Code memory files: a deep dive

What Survives in AI, Skill Set #02. Written 31 Oct 2026.

Every claim below comes from one of five official pages, fetched on 31 Oct 2026. Quotes are copied word for word. Each claim carries its source URL.

| Short name | URL |
| :- | :- |
| MEMORY | https://code.claude.com/docs/en/memory |
| SKILLS | https://code.claude.com/docs/en/skills |
| HOOKS | https://code.claude.com/docs/en/hooks |
| HOOKS-GUIDE | https://code.claude.com/docs/en/hooks-guide |
| AGENTS | https://agents.md/ |

Ready-to-copy files live in `templates/claude-code-memory/`. Good and bad versions of each file are in `templates/claude-code-memory/examples/`. There, `dot-claude/` stands for `.claude/`. Rename it when you copy.

## The one-table summary

| File | What it is | What it is not | Loads | Source |
| :- | :- | :- | :- | :- |
| `CLAUDE.md` | Instructions you write, read at the start of every session | Enforced configuration | Every session, at launch. Subdirectory files load on demand | MEMORY |
| `AGENTS.md` | A shared, plain Markdown instruction file for many coding agents | Read by Claude Code when a `CLAUDE.md` is also present (by default) | Only when no `CLAUDE.md` or `CLAUDE.local.md` is in the working directory or above it, unless you import it | MEMORY, AGENTS |
| `SKILL.md` | A procedure Claude loads when it is relevant or when you type `/skill-name` | Always in context. Only the description is | Description at start, body when invoked | SKILLS |
| Hooks | Commands that run at fixed points in the session | Advice. They run whatever Claude decides | Each time their event fires | HOOKS-GUIDE |

The key idea. Three of the four files are text that Claude reads and tries to follow. Only hooks are enforced. MEMORY says it plainly: "Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead." (https://code.claude.com/docs/en/memory)

---

## 1. CLAUDE.md

### 1.1 What it is, and what it is not

| | Quote | Source |
| :- | :- | :- |
| It is | "CLAUDE.md files are markdown files that give Claude persistent instructions for a project, your personal workflow, or your entire organization." | https://code.claude.com/docs/en/memory |
| It is not | "Claude treats CLAUDE.md files as context, not enforced configuration, so how you write instructions affects how reliably Claude follows them." | https://code.claude.com/docs/en/memory |
| It is not a system prompt | "CLAUDE.md content is delivered as a user message after the system prompt, not as part of the system prompt itself." | https://code.claude.com/docs/en/memory |

What belongs in it: "Keep it to facts Claude should hold in every session: build commands, conventions, project layout, "always do X" rules. If an entry is a multi-step procedure or only matters for one part of the codebase, move it to a skill or a path-scoped rule instead." (https://code.claude.com/docs/en/memory)

When to add a line: "Claude makes the same mistake a second time", "A code review catches something Claude should have known about this codebase", "You type the same correction or clarification into chat that you typed last session", "A new teammate would need the same context to be productive". (https://code.claude.com/docs/en/memory)

### 1.2 How it loads

**Where it lives.** The docs list four scopes, broadest first (https://code.claude.com/docs/en/memory):

| Scope | Path | Shared with |
| :- | :- | :- |
| Managed policy | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`, Linux and WSL `/etc/claude-code/CLAUDE.md`, Windows `C:\Program Files\ClaudeCode\CLAUDE.md` | All users in organization |
| User | `~/.claude/CLAUDE.md` | Only you (all projects) |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team members via source control |
| Local | `./CLAUDE.local.md` (add to `.gitignore`) | Only you (current project) |

Related places, same page:

| Place | What it does | Source |
| :- | :- | :- |
| `.claude/rules/*.md` | "Rules without `paths` frontmatter are loaded at launch with the same priority as `.claude/CLAUDE.md`." | https://code.claude.com/docs/en/memory |
| `.claude/rules/` with `paths:` | "These conditional rules only apply when Claude is working with files matching the specified patterns." | https://code.claude.com/docs/en/memory |
| `~/.claude/rules/` | "Personal rules in `~/.claude/rules/` apply to every project on your machine." | https://code.claude.com/docs/en/memory |
| Auto memory | `~/.claude/projects/<project>/memory/MEMORY.md`. Claude writes it, not you | https://code.claude.com/docs/en/memory |

**When it loads.**

- "Claude Code loads `CLAUDE.md` and `CLAUDE.local.md` from your current working directory and every directory above it." (https://code.claude.com/docs/en/memory)
- Subdirectory files load later: "Claude Code loads each one once Claude reads, writes, or edits another file in that subdirectory." (https://code.claude.com/docs/en/memory)
- After `/compact`: "Project-root CLAUDE.md survives compaction: after `/compact`, Claude re-reads it from disk and re-injects it into the session." (https://code.claude.com/docs/en/memory)

**Precedence.** Nothing overrides anything. Files stack up.

- "All discovered files are concatenated into context rather than overriding each other." (https://code.claude.com/docs/en/memory)
- Order: "content is ordered from the filesystem root down to your working directory", and "Within each directory, `CLAUDE.local.md` is appended after `CLAUDE.md`". (https://code.claude.com/docs/en/memory)
- On conflicts: "if two instructions contradict each other, Claude may pick one arbitrarily." (https://code.claude.com/docs/en/memory)
- The managed file cannot be excluded: "Developers can exclude other CLAUDE.md files with the `claudeMdExcludes` setting, but not this one." (https://code.claude.com/docs/en/memory)

**Size limits.**

| Limit | Quote | Source |
| :- | :- | :- |
| Target | "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." | https://code.claude.com/docs/en/memory |
| Hard cap | "Claude Code skips a file over 4 MiB and loads none of it." | https://code.claude.com/docs/en/memory |
| On-demand files | "200K context window: 40,000 characters". Over that, "Claude receives only the start of it." | https://code.claude.com/docs/en/memory |
| Imports | "Imports help you organize a long file but don't reduce its context cost" | https://code.claude.com/docs/en/memory |
| Import depth | "Imported files can recursively import other files, with a maximum depth of four hops." | https://code.claude.com/docs/en/memory |
| Auto memory | "The first 200 lines of `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the start of every conversation." | https://code.claude.com/docs/en/memory |

A free trick: "Block-level HTML comments (`<!-- maintainer notes -->`) in CLAUDE.md files are stripped before the content is injected into Claude's context." (https://code.claude.com/docs/en/memory) Use them for notes to humans.

### 1.3 Good vs bad

Full files: `templates/claude-code-memory/examples/good/CLAUDE.md` and `examples/bad/CLAUDE.md`.

<table>
<tr><th>GOOD</th><th>BAD</th></tr>
<tr><td>

```markdown
@AGENTS.md

# Billing API

<!-- Owner: platform team. Review monthly. -->

## Commands
- Install: `bun install`
- Test: `bun test`. Run it before every commit.
- Lint: `bun run lint`

## Conventions
- Use 2-space indentation.
- API handlers live in `src/api/handlers/`.
- Money is stored as integer cents. Never floats.

## Gotchas
- `bun test` needs Redis on port 6379.
  Start it with `docker compose up redis`.
- Don't edit `src/generated/`. Run `bun run codegen`.

## Claude Code
- Use plan mode for changes under `src/billing/`.
```

</td><td>

```markdown
# Project Instructions

You are a world-class senior engineer. Always
write clean, high-quality code and format it
properly. Keep files organized.

IMPORTANT: NEVER EVER run `rm -rf` or push
to main. THIS IS CRITICAL.

Please read AGENTS.md before you start.

## Project structure
src/
  api/
    handlers/
      users.ts
      orders.ts
  ... (300 more lines of tree)

## How to deploy (step by step)
1. Bump the version ...
2. ... (40 steps)

## Style
- Use tabs.
...
- Use 2-space indentation.
```

</td></tr>
</table>

Why each difference matters:

| # | Bad line | Why it fails | Good fix | Source |
| :- | :- | :- | :- | :- |
| 1 | "format it properly", "Keep files organized" | Too vague to check. The docs give these exact phrases as the wrong way | "Use 2-space indentation", "API handlers live in `src/api/handlers/`" | https://code.claude.com/docs/en/memory |
| 2 | "NEVER EVER run `rm -rf`" | CLAUDE.md can't block anything. "To block an action regardless of what Claude decides, use a PreToolUse hook instead." | A `PreToolUse` hook (see section 4) | https://code.claude.com/docs/en/memory |
| 3 | "Please read AGENTS.md" | "Claude sees `AGENTS.md` only if it decides to open the file." | `@AGENTS.md` import on line 1 | https://code.claude.com/docs/en/memory |
| 4 | 300-line folder tree | `/doctor` "cuts content Claude can derive from the codebase, such as directory layouts, dependency lists, and architecture overviews" | Delete it. Keep pitfalls and conventions | https://code.claude.com/docs/en/memory |
| 5 | 40-step deploy procedure | "If an entry is a multi-step procedure ... move it to a skill" | `.claude/skills/deploy/SKILL.md` | https://code.claude.com/docs/en/memory |
| 6 | "Use tabs" and "Use 2-space indentation" | "if two instructions contradict each other, Claude may pick one arbitrarily." | One rule only | https://code.claude.com/docs/en/memory |

### 1.4 Setup in steps

1. Run `/init`. "Claude analyzes your codebase and creates a file with build commands, test instructions, and project conventions it discovers. If a CLAUDE.md already exists, `/init` suggests improvements rather than overwriting it." (https://code.claude.com/docs/en/memory)
2. Trim it. Keep only what Claude can't find on its own: "Refine from there with instructions Claude wouldn't discover on its own." (https://code.claude.com/docs/en/memory)
3. Put personal notes in `CLAUDE.local.md` and add it to `.gitignore`. (https://code.claude.com/docs/en/memory)
4. Move file-type rules to `.claude/rules/<topic>.md` with `paths:` frontmatter. (https://code.claude.com/docs/en/memory)
5. Check it loaded: "To confirm the file loaded, run `/context` in a session and check the list under **Memory files**." (https://code.claude.com/docs/en/memory)
6. Edit with `/memory`: it "lists your CLAUDE.md, CLAUDE.local.md, and other memory file locations across user and project scopes". (https://code.claude.com/docs/en/memory)
7. Audit with `/doctor prompt-audit`: "Claude looks for problems such as instructions written for older models, references to files or commands that don't exist, and files that contradict each other." It needs "Claude Code v2.1.283 or later". (https://code.claude.com/docs/en/memory)
8. To see which file loaded and why, use the `InstructionsLoaded` hook "to log which `CLAUDE.md` and rules files are loaded, when they load, and why." (https://code.claude.com/docs/en/memory)

### 1.5 The 3 most common mistakes

| # | Mistake | The docs line that warns against it | Source |
| :- | :- | :- | :- |
| 1 | Writing a "never do X" rule and expecting it to be enforced | "Settings rules are enforced by the client regardless of what Claude decides to do. CLAUDE.md instructions shape Claude's behavior but are not a hard enforcement layer." | https://code.claude.com/docs/en/memory |
| 2 | A long file, or splitting it with imports and thinking that saves space | "Files over 200 lines consume more context and may reduce adherence." and "Splitting into `@path` imports helps organization but doesn't reduce context" | https://code.claude.com/docs/en/memory |
| 3 | Vague or conflicting rules | "Make instructions more specific. "Use 2-space indentation" works better than "format code nicely."" and "If two files give different guidance for the same behavior, Claude may pick one arbitrarily." | https://code.claude.com/docs/en/memory |

---

## 2. AGENTS.md

### 2.1 What it is, and what it is not

| | Quote | Source |
| :- | :- | :- |
| It is | "A simple, open format for guiding coding agents" | https://agents.md/ |
| It is not a README | "README.md files are for humans: quick starts, project descriptions, and contribution guidelines." | https://agents.md/ |
| It has no schema | "No. AGENTS.md is just standard Markdown. Use any headings you like; the agent simply parses the text you provide." | https://agents.md/ |
| In Claude Code, it is not read alongside CLAUDE.md by default | "By default, Claude reads `AGENTS.md` only when you have no `CLAUDE.md` in your working directory or above it." | https://code.claude.com/docs/en/memory |

### 2.2 How it loads

**Where it lives.** "Create an AGENTS.md file at the root of the repository." In a monorepo, add one per package. "The closest AGENTS.md to the edited file wins; explicit user chat prompts override everything." (https://agents.md/)

**In Claude Code**, the default is either one or the other (https://code.claude.com/docs/en/memory):

| Your repository has | Claude reads |
| :- | :- |
| An `AGENTS.md`, and no `CLAUDE.md` or `CLAUDE.local.md` in your working directory or above it | Your `AGENTS.md` |
| An `AGENTS.md` and a `CLAUDE.md` or `CLAUDE.local.md` in your working directory or above it | Your `CLAUDE.md` files only |
| A `CLAUDE.md` that already imports `AGENTS.md` | Your `CLAUDE.md`, with `AGENTS.md` included through the import |

Files that count against it: "a `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md` in your working directory or any directory above it". Files that don't: "your `~/.claude/CLAUDE.md`, your organization's managed `CLAUDE.md`, and `.claude/rules/` files". (https://code.claude.com/docs/en/memory)

Not read at all: "`AGENTS.local.md`, `AGENTS.override.md`, or anything under a `.agents/` directory". (https://code.claude.com/docs/en/memory)

Version: "Reading `AGENTS.md` directly requires Claude Code v2.1.277 or later." (https://code.claude.com/docs/en/memory)

To change the default, open `/config` and set **Project instructions**. `claude-md-and-agents-md` reads "Your `CLAUDE.md` and `AGENTS.md` files together". (https://code.claude.com/docs/en/memory)

**Size limits.** The agents.md page sets none. When Claude Code reads it, it behaves like a CLAUDE.md, so the CLAUDE.md guidance above applies. Inside each `AGENTS.md`, "`@path` imports are expanded, `claudeMdExcludes` patterns apply". (https://code.claude.com/docs/en/memory)

### 2.3 Good vs bad

Full files: `examples/good/AGENTS.md` and `examples/bad/AGENTS.md`.

<table>
<tr><th>GOOD</th><th>BAD</th></tr>
<tr><td>

```markdown
# AGENTS.md

## Setup commands
- Install deps: `pnpm install`
- Start dev server: `pnpm dev`
- Run tests: `pnpm test`

## Code style
- TypeScript strict mode
- Single quotes, no semicolons

## Testing instructions
- Run `pnpm lint` and `pnpm test`
  before committing.
- Add or update tests for the code
  you change.

## PR instructions
- Title format: [<package>] <Title>
```

</td><td>

```markdown
# Welcome to Acme!

Acme is the best way to manage invoices.
Star us on GitHub! See screenshots below.

![screenshot](docs/hero.png)

## Contributing
We love contributions from humans like you.

## Claude-only
- Use the /deploy skill.
- Edit AGENTS.local.md for your overrides.
```

</td></tr>
</table>

| # | Bad line | Why it fails | Good fix | Source |
| :- | :- | :- | :- | :- |
| 1 | Marketing copy and screenshots | That is README content, which is "for humans" | Commands, style, test and PR rules | https://agents.md/ |
| 2 | No test commands | Agents run checks only if listed: "The agent will attempt to execute relevant programmatic checks and fix failures before finishing the task." | List `pnpm test` and `pnpm lint` | https://agents.md/ |
| 3 | "Claude-only" section | Other agents read this file too. Claude-specific lines belong in CLAUDE.md under the import | `CLAUDE.md` with `@AGENTS.md` then `## Claude Code` | https://code.claude.com/docs/en/memory |
| 4 | `AGENTS.local.md` | Claude Code does not read it | Use `CLAUDE.local.md`, and set **Project instructions** to `claude-md-and-agents-md` | https://code.claude.com/docs/en/memory |

### 2.4 Setup in steps

1. Create `AGENTS.md` at the repo root. Add sections such as "Build and test commands", code style, testing and PR rules. (https://agents.md/)
2. If you also keep a `CLAUDE.md`, put `@AGENTS.md` on its first line. "Add any Claude-specific instructions below the import, and Claude reads the imported file first, then the rest". (https://code.claude.com/docs/en/memory)
3. If you need no Claude-only lines, a symlink works: `ln -s AGENTS.md CLAUDE.md`. Not on Windows: "use the `@AGENTS.md` import instead." (https://code.claude.com/docs/en/memory)
4. Check: "To check whether Claude read your `AGENTS.md`, run `/memory` and look for its path in the list." (https://code.claude.com/docs/en/memory)
5. With the import, also "run `/context` in your next session and confirm `CLAUDE.md` appears under **Memory files**." (https://code.claude.com/docs/en/memory)
6. `/doctor prompt-audit` covers it too: "the audit covers your CLAUDE.md, CLAUDE.local.md, and AGENTS.md files". (https://code.claude.com/docs/en/memory)

### 2.5 The 3 most common mistakes

| # | Mistake | The docs line that warns against it | Source |
| :- | :- | :- | :- |
| 1 | Keeping both files and expecting Claude to read both | "If your repository has an `AGENTS.md` and Claude doesn't seem to know what it says, the usual cause is a `CLAUDE.md` somewhere on the project path." | https://code.claude.com/docs/en/memory |
| 2 | Telling Claude in words to read it | "A `CLAUDE.md` that tells Claude in words to read `AGENTS.md`: Claude sees `AGENTS.md` only if it decides to open the file." | https://code.claude.com/docs/en/memory |
| 3 | Adding a `CLAUDE.local.md` to a project that relies on AGENTS.md | "Because `CLAUDE.local.md` counts, adding one to keep your own uncommitted instructions in a project that relies on `AGENTS.md` stops Claude from reading `AGENTS.md` for you." | https://code.claude.com/docs/en/memory |

---

## 3. SKILL.md

### 3.1 What it is, and what it is not

| | Quote | Source |
| :- | :- | :- |
| It is | "Skills extend what Claude can do. Create a `SKILL.md` file with instructions, and Claude adds it to its toolkit." | https://code.claude.com/docs/en/skills |
| It is not always loaded | "Unlike CLAUDE.md content, a skill's body loads only when it's used, so long reference material costs almost nothing until you need it." | https://code.claude.com/docs/en/skills |
| It is not enforcement | "Claude skipped a rule that must hold every time: move the rule into a hook." | https://code.claude.com/docs/en/skills |

When to make one: "Create a skill when you keep pasting the same instructions, checklist, or multi-step procedure into chat, or when a section of CLAUDE.md has grown into a procedure rather than a fact." (https://code.claude.com/docs/en/skills)

### 3.2 How it loads

**Where it lives** (https://code.claude.com/docs/en/skills):

| Scope | Path |
| :- | :- |
| Enterprise | `.claude/skills/<skill-name>/SKILL.md` in the managed settings directory |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` |
| Project | `.claude/skills/<skill-name>/SKILL.md` |
| Nested | `<subdir>/.claude/skills/<skill-name>/SKILL.md` |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md`, invoked as `/plugin-name:skill-name` |

**Precedence.** "Enterprise over personal, and personal over project." A skill beats a same-named file in `.claude/commands/`. Plugin skills never clash because they are namespaced. (https://code.claude.com/docs/en/skills)

**When it loads.** "In a regular session, skill descriptions are loaded into context so Claude knows what's available, but full skill content only loads when invoked." Once invoked, "the rendered `SKILL.md` content enters the conversation as a single message and stays there across later turns." And: "Claude Code does not re-read the skill file on later turns". (https://code.claude.com/docs/en/skills)

| Frontmatter | You can invoke | Claude can invoke | Source |
| :- | :- | :- | :- |
| (default) | Yes | Yes | https://code.claude.com/docs/en/skills |
| `disable-model-invocation: true` | Yes | Not on its own | https://code.claude.com/docs/en/skills |
| `user-invocable: false` | No | Yes | https://code.claude.com/docs/en/skills |

**Format.** "YAML frontmatter between `---` markers that tells Claude when to use the skill, and markdown content with the instructions". "Claude Code reads the frontmatter only when the opening `---` is the file's first line." "All fields are optional. Only `description` is recommended". (https://code.claude.com/docs/en/skills)

**Size limits.**

| Limit | Quote | Source |
| :- | :- | :- |
| Body | "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files." | https://code.claude.com/docs/en/skills |
| Description | "the combined `description` and `when_to_use` text is truncated at 1,536 characters in the skill listing" | https://code.claude.com/docs/en/skills |
| Listing budget | "The budget scales at 1% of the model's context window." | https://code.claude.com/docs/en/skills |
| After compaction | Re-attached skills keep "the first 5,000 tokens of each" and "share a combined budget of 25,000 tokens." | https://code.claude.com/docs/en/skills |

### 3.3 Good vs bad

Full files: `examples/good/dot-claude/skills/add-endpoint/SKILL.md` and `examples/bad/dot-claude/skills/add-endpoint/SKILL.md`.

<table>
<tr><th>GOOD</th><th>BAD</th></tr>
<tr><td>

```markdown
---
name: add-endpoint
description: Add or change an HTTP API endpoint
  in this repo. Covers file location, naming,
  tests and route registration. Use when the
  user asks for a new endpoint or route.
---

# Add an endpoint

Throughout this task, run `bun test` after
every edit.

1. Create `src/api/handlers/<name>.ts`.
2. Add `tests/api/<name>.test.ts`.
3. Register the route in `src/api/index.ts`.
4. Run `bun test` and fix failures.

## Additional resources
- Error format: see [reference.md](reference.md)
```

</td><td>

```markdown
# Endpoint helper
---
name: Endpoint Helper
desc: helps with stuff
allowedTools: Bash
---

Use our API conventions.

(800 lines of pasted OpenAPI spec)

Never commit secrets. This must ALWAYS hold.
```

</td></tr>
</table>

| # | Bad line | Why it fails | Good fix | Source |
| :- | :- | :- | :- | :- |
| 1 | `---` is not on line 1 | "Otherwise it treats the whole file, `---` markers included, as skill content." | Frontmatter starts on the first line | https://code.claude.com/docs/en/skills |
| 2 | `desc:` and `allowedTools:` | "Claude Code ignores a field it doesn't recognize without reporting an error." | `description:`, `allowed-tools:` | https://code.claude.com/docs/en/skills |
| 3 | "helps with stuff" | "Check the description includes keywords users would naturally say" | Key use case first, with trigger words | https://code.claude.com/docs/en/skills |
| 4 | 800-line spec in the body | "Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files." | Link `reference.md` | https://code.claude.com/docs/en/skills |
| 5 | "Use our API conventions" with no task | With `context: fork`, "the subagent receives the guidelines but no actionable prompt, and returns without meaningful output." | Numbered steps | https://code.claude.com/docs/en/skills |
| 6 | "This must ALWAYS hold" | Must-hold rules belong in a hook | A hook, or `hooks:` in the skill frontmatter | https://code.claude.com/docs/en/skills |

### 3.4 Setup in steps

1. Make the folder: `.claude/skills/<skill-name>/` (project) or `~/.claude/skills/<skill-name>/` (personal). (https://code.claude.com/docs/en/skills)
2. Write `SKILL.md` with `name` and `description` at the top. Put "the key use case first". (https://code.claude.com/docs/en/skills)
3. Write the steps as standing instructions: "word the guidance so it applies to the whole task, for example "Run the tests after every edit" rather than "Run the tests"." (https://code.claude.com/docs/en/skills)
4. Put long material in side files and link them, so Claude knows "what each file contains and when to load it". (https://code.claude.com/docs/en/skills)
5. For risky jobs like deploys, add `disable-model-invocation: true`. (https://code.claude.com/docs/en/skills)
6. Check it is found: "Verify the skill appears in `What skills are available?`" and try `/skill-name`. (https://code.claude.com/docs/en/skills)
7. Check frontmatter parses: `claude plugin validate .claude/skills`. "Requires Claude Code v2.1.233 or later." (https://code.claude.com/docs/en/skills)
8. Check it works: "run each one in a fresh session with the skill available and again with it turned off, and compare the results." (https://code.claude.com/docs/en/skills)
9. Check the listing cost: "Run `/doctor` for an estimate of the listing's context cost and its biggest contributors." Audit one skill with `/doctor prompt-audit .claude/skills/<name>`. (https://code.claude.com/docs/en/skills, https://code.claude.com/docs/en/memory)

### 3.5 The 3 most common mistakes

| # | Mistake | The docs line that warns against it | Source |
| :- | :- | :- | :- |
| 1 | Broken or misnamed frontmatter | "If the frontmatter YAML is malformed, Claude Code loads the skill body with empty metadata, so `/skill-name` still works but Claude can't match against your `description`." | https://code.claude.com/docs/en/skills |
| 2 | One-time steps that fade later in the task | "Claude Code does not re-read the skill file on later turns, so write guidance that should apply throughout a task as standing instructions rather than one-time steps." | https://code.claude.com/docs/en/skills |
| 3 | A bloated body | "Once a skill loads, its content stays in context across turns, so every line is a recurring token cost." | https://code.claude.com/docs/en/skills |

---

## 4. Hooks

### 4.1 What they are, and what they are not

| | Quote | Source |
| :- | :- | :- |
| They are | "Hooks are user-defined shell commands, HTTP endpoints, MCP tool calls, LLM prompts, or subagents that execute automatically at specific points in Claude Code's lifecycle." | https://code.claude.com/docs/en/hooks |
| They are deterministic | "certain actions always happen rather than relying on the LLM to choose to run them." | https://code.claude.com/docs/en/hooks-guide |
| They are not a file | Hooks live in a `hooks` block inside a settings file, not in a `HOOK.md` | https://code.claude.com/docs/en/hooks-guide |
| They are not an undo | "`PostToolUse` hooks can't undo actions since the tool has already executed." | https://code.claude.com/docs/en/hooks-guide |
| Their `if` filter is not a hard gate | "Because the filter is best-effort, use the permission system rather than a hook to enforce a hard allow or deny." | https://code.claude.com/docs/en/hooks-guide |

### 4.2 How they load

**Where they live** (https://code.claude.com/docs/en/hooks-guide):

| Location | Scope |
| :- | :- |
| `~/.claude/settings.json` | All your projects |
| `.claude/settings.json` | Single project, can be committed |
| `.claude/settings.local.json` | Single project, gitignored |
| Managed policy settings | Organization-wide |
| Plugin `hooks/hooks.json` | When plugin is enabled |
| Skill frontmatter | The rest of the session once the skill is invoked |
| Subagent frontmatter | While that subagent is running |

**Structure.** "The configuration has three levels of nesting": an event such as `PreToolUse`, "a matcher group to filter when it fires", and "one or more hook handlers to run when matched". (https://code.claude.com/docs/en/hooks)

**Precedence.** Hooks add up. "Hook entries merge across settings levels rather than replacing each other". "If you define the same handler in more than one settings file, it runs once." "When an event fires, its matching hooks run in parallel." (https://code.claude.com/docs/en/hooks) When several decide: "the most restrictive answer applies, in the order `deny`, `defer`, `ask`, `allow`." (https://code.claude.com/docs/en/hooks-guide)

**Power.** "a hook that returns `permissionDecision: "deny"` blocks the tool even in `bypassPermissions` mode or with `--dangerously-skip-permissions`." (https://code.claude.com/docs/en/hooks-guide)

**Exit codes** (https://code.claude.com/docs/en/hooks):

| Exit | Meaning |
| :- | :- |
| 0 | "Success". JSON on stdout is applied |
| 2 | "Blocking error". "The message that comes with the block is your hook's stderr." |
| Other | "Non-blocking error". "If your hook is meant to enforce a policy, use `exit 2`." |

**Time limits.** "`command`, `http`, `mcp_tool`: 10 minutes", "`prompt`: 30 seconds", "`agent`: 60 seconds". (https://code.claude.com/docs/en/hooks-guide)

**Reloads.** "If you edit settings files directly while Claude Code is running, the file watcher normally picks up hook changes automatically." (https://code.claude.com/docs/en/hooks-guide)

### 4.3 Good vs bad

Full files: `examples/good/dot-claude/settings.json` with `examples/good/dot-claude/hooks/protect-files.sh`, and the bad pair under `examples/bad/dot-claude/`.

<table>
<tr><th>GOOD</th><th>BAD</th></tr>
<tr><td>

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
#!/bin/bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
for p in ".env" "package-lock.json" ".git/"; do
  if [[ "$FILE_PATH" == *"$p"* ]]; then
    echo "Blocked: $FILE_PATH matches '$p'" >&2
    exit 2
  fi
done
exit 0
```

</td><td>

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "edit",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/protect.sh"
          }
        ]
      }
    ],
    "PermissionRequest": [
      {
        "matcher": "",
        "hooks": [{ "type": "command",
          "command": "echo '{\"hookSpecificOutput\": {\"hookEventName\": \"PermissionRequest\", \"decision\": {\"behavior\": \"allow\"}}}'" }]
      }
    ]
  }
}
```

```bash
#!/bin/bash
echo "checking..."
if grep -q ".env"; then
  echo '{"permissionDecision": "deny"}'
  exit 1
fi
```

</td></tr>
</table>

| # | Bad line | Why it fails | Good fix | Source |
| :- | :- | :- | :- | :- |
| 1 | `"matcher": "edit"` | "Matchers are case-sensitive" | `"Edit\|Write"` | https://code.claude.com/docs/en/hooks-guide |
| 2 | Relative path `.claude/hooks/protect.sh` | "If you see "command not found", use absolute paths or `${CLAUDE_PROJECT_DIR}`" | `"$CLAUDE_PROJECT_DIR"/.claude/hooks/...` | https://code.claude.com/docs/en/hooks-guide |
| 3 | `exit 1` to block | "Exit code 1 without valid JSON output is a non-blocking error" | `exit 2` with a reason on stderr | https://code.claude.com/docs/en/hooks |
| 4 | `permissionDecision` at the top level | "`permissionDecision` belongs inside `hookSpecificOutput`, not at the top level." | Exit 2, or full `hookSpecificOutput` JSON | https://code.claude.com/docs/en/hooks-guide |
| 5 | `echo "checking..."` before JSON | "Claude Code reads output that doesn't start with `{` as plain text, so your JSON is ignored." | Print nothing but the result | https://code.claude.com/docs/en/hooks-guide |
| 6 | Empty matcher on `PermissionRequest` with allow | "Matching on `.*` or leaving the matcher empty would auto-approve every tool permission prompt, including file writes and shell commands." | Narrow matcher, such as `ExitPlanMode` | https://code.claude.com/docs/en/hooks-guide |

### 4.4 Setup in steps

1. Pick the file. Use `.claude/settings.json` for team rules, `~/.claude/settings.json` for personal ones. (https://code.claude.com/docs/en/hooks-guide)
2. Add the `hooks` block. "If your settings file already has a `hooks` key, add `Notification` as a sibling of the existing event keys rather than replacing the whole object." (https://code.claude.com/docs/en/hooks-guide)
3. Save the script to `.claude/hooks/` and make it executable: "Hook scripts must be executable for Claude Code to run them". Run `chmod +x .claude/hooks/protect-files.sh`. (https://code.claude.com/docs/en/hooks-guide)
4. Test it by hand: `echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh` then `echo $?`. (https://code.claude.com/docs/en/hooks-guide)
5. Check it registered: "Type `/hooks` at the Claude Code prompt to open the hooks browser." It is read-only and labels each hook by source. (https://code.claude.com/docs/en/hooks-guide, https://code.claude.com/docs/en/hooks)
6. Trigger it. For the protect-files hook: "Ask Claude to add a comment to your `.env` file." (https://code.claude.com/docs/en/hooks-guide)
7. See what happened: "Press `Ctrl+O` to open the transcript view". For full detail, "Start Claude Code with `claude --debug-file /tmp/claude.log`". (https://code.claude.com/docs/en/hooks-guide)
8. To pause all hooks, set `"disableAllHooks": true`. Managed hooks keep running. (https://code.claude.com/docs/en/hooks)

### 4.5 The 3 most common mistakes

| # | Mistake | The docs line that warns against it | Source |
| :- | :- | :- | :- |
| 1 | Blocking with `exit 1` | "Exit code 1 without valid JSON output is a non-blocking error unless the hook is one whose failure blocks the action, even though 1 is the conventional Unix failure code. If your hook is meant to enforce a policy, use `exit 2`." | https://code.claude.com/docs/en/hooks |
| 2 | JSON that silently does nothing | "When your hook returns `permissionDecision` or `additionalContext` at the top level instead of inside `hookSpecificOutput`, the JSON still parses, and Claude Code ignores the misplaced fields without reporting an error." | https://code.claude.com/docs/en/hooks-guide |
| 3 | A Stop hook that never lets Claude stop | "Your hook script needs to check whether it already triggered a continuation. Parse the `stop_hook_active` field from the JSON input and exit early if it's `true`" | https://code.claude.com/docs/en/hooks-guide |

---

## 5. Which file for which job

| You want | Use | Why, from the docs | Source |
| :- | :- | :- | :- |
| A fact Claude needs every session | `CLAUDE.md` | "build commands, conventions, project layout, "always do X" rules" | https://code.claude.com/docs/en/memory |
| The same rules for Codex, Cursor and Claude | `AGENTS.md`, imported from `CLAUDE.md` | "keep it as the one file every tool shares" | https://code.claude.com/docs/en/memory |
| A rule for one folder or file type | `.claude/rules/x.md` with `paths:` | They "only load into context when Claude works with matching files" | https://code.claude.com/docs/en/memory |
| A multi-step procedure | `SKILL.md` | "a skill's body loads only when it's used" | https://code.claude.com/docs/en/skills |
| Something that must always happen, or never | A hook | "Hooks execute as shell commands at fixed lifecycle events and apply regardless of what Claude decides to do." | https://code.claude.com/docs/en/memory |
| A hard tool ban for the whole org | Managed settings `permissions.deny` | "Use the file for guidance, and enforce rules with managed settings such as `permissions.deny`." | https://code.claude.com/docs/en/memory |

## 6. Confidence and gaps

| Item | Confidence | Note |
| :- | :- | :- |
| Every quote above | High | Copied from pages fetched 31 Oct 2026 |
| Version numbers (v2.1.277, v2.1.283, v2.1.233) | High for today | These change. Recheck before publishing |
| Hooks reference sections on security and startup snapshots | Not covered | The fetch of https://code.claude.com/docs/en/hooks was cut off before those sections. Nothing here is claimed from them |
| `/doctor prompt-audit` | High | Documented on the memory page, needs v2.1.283 or later |
| agents.md quotes | Medium-high | The fetch tool limited quote length, so a few sentences are shown in part |

### The catch: a hook that fails lets the action through

Checked 31 Oct 2026 against https://code.claude.com/docs/en/hooks ("Block the action when a hook fails").

- By default, a PreToolUse hook that times out, crashes, can't start, or exits with any code other than 0 or 2 does not block. The docs: "On `PreToolUse`, a timed-out `command`, `http`, or `mcp_tool` hook doesn't block the tool call ... so don't count on a stalled hook to act as a gate."
- Fix: add `"onFailure": "block"` to every guard hook. Then "a failure does what exit code 2 does on that event ... a `PreToolUse` failure blocks the tool call". It needs Claude Code v2.1.295 or later and works on `command` and `http` hooks.
- Good: `{"type": "command", "command": "...", "onFailure": "block"}`. Bad: the same hook without it. If the script is missing or slow, the dangerous command runs.
- Return JSON decisions with exit 0. An exit code other than 0 or 2 counts as a failure even if the hook printed JSON allowing the action.

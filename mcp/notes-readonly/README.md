# notes-readonly: an MCP server for your own Markdown notes

Give Claude Code (or any MCP client) your notes folder to **list, search and read**, and nothing else. It cannot
write, and it cannot read outside the folder: `../`, absolute paths and every symlink are refused, and each refusal
has a test.

[`server.py`](server.py) is 99 lines, built on the official MCP Python SDK (`mcp` 2.3.0). The tests are in
[`test_server.py`](test_server.py): 34 cases, run offline against throwaway folders.

| Tool | Input | Returns |
|---|---|---|
| `list_notes` | `folder` (optional, relative) | `notes`: relative paths of `.md` and `.markdown` files, sorted; `truncated` if over 1,000 |
| `search_notes` | `query`, `max_results` (default 20, at most 200) | `path`, `line` number and `text` of each matching line (case-insensitive substring) |
| `read_note` | `path` (relative, as `list_notes` gives it) | the note's text |

All three carry the MCP annotations `readOnlyHint: true` and `openWorldHint: false`.

## Install in Claude Code (5 minutes)

You need [uv](https://docs.astral.sh/uv/) and Claude Code. uv reads the dependency list at the top of `server.py`
(`mcp==2.3.0`) and installs it in its own cache, so there is no virtualenv to manage.

```bash
git clone https://github.com/prandata/wsai-skill-set
cd wsai-skill-set/mcp/notes-readonly

# 1. Check it starts: it waits silently for a client on stdin (Ctrl-C to stop).
#    A wrong folder stops it at once with "no such folder".
uv run --script server.py ~/notes

# 2. Add it to Claude Code, for all your projects
claude mcp add --scope user --transport stdio notes -- uv run --script "$PWD/server.py" ~/notes

# 3. Check it connected
claude mcp list          # shows each server with its health status
```

Replace `~/notes` with your notes folder (an Obsidian vault works: its `.obsidian/` folder is skipped). Use absolute
paths: Claude Code starts the server from whatever folder you are in. Then, in Claude Code, ask "search my notes for
MCP" or run `/mcp` to see the three tools.

Options:

| Want | Do |
|---|---|
| A bigger or smaller per-file cap (default 1,000,000 bytes) | add `--env NOTES_MAX_BYTES=2000000` before `notes` in step 2 |
| Only this project | `--scope local` (the default) instead of `--scope user` |
| Share it with a repo's team | `--scope project` writes `.mcp.json`; each person approves it on first run |
| Remove it | `claude mcp remove notes --scope user` |

Everything after `--` is passed to the server untouched, so the folder path is the server's argument, not Claude
Code's ([Claude Code MCP docs](https://code.claude.com/docs/en/mcp)).

## How it stays read-only and inside the folder

| Rule | How | Test |
|---|---|---|
| No write tool | The server defines three tools; none takes content to write. Calling `write_note`, `delete_note`, `create_note` or `move_note` is an error. | `test_only_three_tools_all_read_only`, `test_no_write_tool` |
| Opens files read-only | Every file is opened with `os.open(..., O_RDONLY \| O_NOFOLLOW \| O_NONBLOCK)`. | `test_folder_unchanged_after_every_tool` spies on every `os.open` and checks no write flag, then compares the whole temp folder (content, mode, mtime) before and after every tool, valid and refused calls alike |
| No `..`, no absolute paths, no hidden parts | A path with a `..` part (also with `\` separators), a leading `/`, a part starting with `.`, or a NUL byte is refused before it touches the disk. | `test_traversal_refused` (9 paths), `test_list_outside_refused` (5), `test_absolute_path_inside_still_refused` |
| No symlinks, anywhere in the path | Each part of the path is checked with `is_symlink()`. A link that points back inside the folder is refused too: one rule is easier to trust than "links are fine if...". `list_notes` and `search_notes` skip links. | `test_symlink_refused` (file link, folder link, inside link), `test_symlinks_not_listed_or_searched` |
| A file swapped for a symlink after the check | The open uses `O_NOFOLLOW`: "If path names a symbolic link, fail and set errno to [ELOOP]" ([POSIX `open()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html)). | `test_file_swapped_for_symlink_after_check` swaps the file between the check and the open |
| Belt and braces | After the checks, the resolved real path must still be inside the folder. | covered by the cases above |
| Large file cap | A file over `NOTES_MAX_BYTES` (default 1,000,000) is refused by `read_note` and skipped by `search_notes`. The size comes from `fstat` on the open file, and at most the cap is read even if the file grows. | `test_large_file_cap`, and over real stdio in `test_stdio_end_to_end` |
| A named pipe cannot hang it | `O_NONBLOCK`: "If O_NONBLOCK is clear, an open() for reading-only shall block the calling thread until a thread opens the file for writing" (POSIX, same page). Anything that is not a regular file is refused. | `test_fifo_named_md_does_not_hang` |
| Output caps | `list_notes` returns at most 1,000 paths and says `truncated`; search returns at most 200 hits, each line cut to 300 characters. | `test_list_and_search_caps` |

Refusals are raised as `ToolError`, so the client gets a normal result with `is_error` set and a message the model
can read and correct. The SDK hides the text of any other exception ("What it doesn't get is the exception's text"),
so an unexpected error does not leak a full path
([SDK docs, handling errors](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/)).

While building this, seven guards were removed one at a time and the tests rerun: the `..` and hidden-part check,
the absolute-path check, the symlink walk, the symlink skip in listings, `O_NOFOLLOW`, `O_NONBLOCK` and the size cap.
Each removal made at least one test fail.

## Run the tests

From the repo root:

```bash
uv run --no-project --with mcp==2.3.0 --with pytest pytest mcp/notes-readonly -q
```

Most tests talk to the server in memory with `Client(server)`, as the SDK's testing guide shows
([SDK docs, testing](https://py.sdk.modelcontextprotocol.io/get-started/testing/)). `test_stdio_end_to_end` starts
the real script as a subprocess over stdio. Tested on macOS with Python 3.10 and 3.12.

## Limits

| Limit | What it means |
|---|---|
| It limits this server, not Claude Code | Claude Code's own Read and Bash tools can still open any file your user account can. To keep the agent out of other folders, use Claude Code's permission deny rules and sandbox as well. |
| Annotations are hints | `readOnlyHint` tells a client the tool changes nothing; the SDK docs say "They are hints, not security. Never rely on a client honouring them." ([SDK docs, tools](https://py.sdk.modelcontextprotocol.io/servers/tools/)). The guarantee here is that no write code exists. |
| Hard links | A hard link inside the folder to a file elsewhere looks like an ordinary file and is read. Making one needs write access to the folder and the same disk. |
| Mount points | A disk or bind mount placed inside the folder is read like a subfolder. |
| A folder swapped for a symlink mid-request | `O_NOFOLLOW` covers the file itself, not the folders above it. Someone who can write to your notes folder and swaps a subfolder for a symlink in the instant between the check and the open could get one read through. If other people can write to the folder, don't rely on this. |
| Notes are untrusted input | Note text goes straight to the model. A note (or a web clipping in your vault) that says "ignore your instructions" is read like any other text. |
| Markdown only | Files ending `.md` or `.markdown` (any case). Hidden files and folders (`.obsidian/`, `.git/`) are skipped and refused. |
| Simple search | Case-insensitive substring per line: no regex, no fuzzy match, no ranking, no index. It reads every note on each search, so a vault of many thousands of notes is slow. |
| Text encoding | Read as UTF-8; invalid bytes become the replacement character U+FFFD. |
| One folder, fixed at start | The folder is resolved once when the server starts (the folder itself may be a symlink, for example into iCloud Drive). Restart to change it. |
| Platforms | Tested on macOS. It uses POSIX `O_NOFOLLOW` and `O_NONBLOCK`, so it is written for macOS and Linux; Windows is untested. |
| stdio only | It runs as a local subprocess. It is not built to be exposed over HTTP. |

## Sources

Checked 1 Nov 2026.

| Source | Used for |
|---|---|
| [`mcp` 2.3.0 on PyPI](https://pypi.org/project/mcp/2.3.0/) (released 2 Oct 2026) | The SDK version pinned in `server.py`; `MCPServer` and `Client` |
| [MCP Python SDK docs: tools](https://py.sdk.modelcontextprotocol.io/servers/tools/) | `ToolAnnotations(read_only_hint=True, open_world_hint=False)` |
| [MCP Python SDK docs: handling errors](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/) | `ToolError` and how errors reach the client |
| [MCP Python SDK docs: testing](https://py.sdk.modelcontextprotocol.io/get-started/testing/) | In-memory `Client(server)` tests with pytest and anyio |
| [Claude Code docs: MCP](https://code.claude.com/docs/en/mcp) | `claude mcp add`, `--scope`, `--env`, the `--` separator, `claude mcp list` |
| [POSIX `open()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html) | `O_NOFOLLOW` and `O_NONBLOCK` behaviour |

"""Tests for server.py. Every case runs against a throwaway folder made in a temp dir.

Run: uv run --with mcp==2.3.0 --with pytest pytest mcp/notes-readonly -q
Most tests talk to the server in memory with Client(server); one starts the real stdio process.
"""
import hashlib, os, sys, threading, time
from pathlib import Path

import pytest
from mcp import Client, StdioServerParameters

sys.path.insert(0, str(Path(__file__).parent))
from server import build  # noqa: E402

SERVER = str(Path(__file__).parent / "server.py")
SECRET = "TOP-SECRET-OUTSIDE-THE-FOLDER"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def tree(tmp_path):
    """notes/ with two notes, plus a secret file and folder outside it, and symlinks that try to escape."""
    notes, outside = tmp_path / "notes", tmp_path / "outside"
    (notes / "projects").mkdir(parents=True)
    (notes / ".obsidian").mkdir()
    outside.mkdir()
    (notes / "inbox.md").write_text("# Inbox\nbuy milk\nCall the Dentist\n")
    (notes / "projects" / "mcp.md").write_text("# MCP\nread-only by default\n")
    (notes / "projects" / "draft.txt").write_text("not a note")
    (notes / ".obsidian" / "hidden.md").write_text("hidden dentist")
    (outside / "secret.md").write_text(SECRET)
    (notes / "link-file.md").symlink_to(outside / "secret.md")          # symlink to a file outside
    (notes / "link-dir").symlink_to(outside, target_is_directory=True)  # symlink to a folder outside
    (notes / "inside-link.md").symlink_to(notes / "inbox.md")           # symlink that stays inside
    return notes


async def call(server, tool, args):
    async with Client(server) as c:
        return await c.call_tool(tool, args)


def text(result):
    return "".join(getattr(c, "text", "") for c in result.content)


def snapshot(root):
    """Content, mode and mtime of everything under root (lstat, so symlinks are not followed)."""
    out = {}
    for d, dirs, files in os.walk(root):
        for name in dirs + files:
            p = os.path.join(d, name)
            st = os.lstat(p)
            body = os.readlink(p) if os.path.islink(p) else (open(p, "rb").read() if os.path.isfile(p) else b"")
            out[p] = (st.st_mode, st.st_mtime_ns, hashlib.sha256(str(body).encode()).hexdigest())
    return out


# ---------- the happy path ----------

@pytest.mark.anyio
async def test_list_search_read(tree):
    s = build(str(tree))
    r = await call(s, "list_notes", {})
    assert not r.is_error
    assert r.structured_content == {"notes": ["inbox.md", "projects/mcp.md"], "truncated": False}
    r = await call(s, "list_notes", {"folder": "projects"})
    assert r.structured_content["notes"] == ["projects/mcp.md"]
    r = await call(s, "search_notes", {"query": "dentist"})
    assert r.structured_content == {"result": [{"path": "inbox.md", "line": 3, "text": "Call the Dentist"}]}
    r = await call(s, "read_note", {"path": "projects/mcp.md"})
    assert not r.is_error and text(r) == "# MCP\nread-only by default\n"


# ---------- path traversal ----------

@pytest.mark.anyio
@pytest.mark.parametrize("path", [
    "../outside/secret.md", "projects/../../outside/secret.md", "projects/../inbox.md",
    "..\\outside\\secret.md", "/etc/passwd", "//etc/passwd", "inbox.md\0.md",
    ".obsidian/hidden.md", "./inbox.md/..",
])
async def test_traversal_refused(tree, path):
    r = await call(build(str(tree)), "read_note", {"path": path})
    assert r.is_error and "Refused" in text(r), text(r)
    assert SECRET not in text(r)


@pytest.mark.anyio
@pytest.mark.parametrize("folder", ["..", "../outside", "/", "/tmp", ".obsidian"])
async def test_list_outside_refused(tree, folder):
    r = await call(build(str(tree)), "list_notes", {"folder": folder})
    assert r.is_error and "Refused" in text(r)


@pytest.mark.anyio
async def test_absolute_path_inside_still_refused(tree):
    """Absolute paths are refused even when they point inside, so there is one way to name a note."""
    r = await call(build(str(tree)), "read_note", {"path": str(tree / "inbox.md")})
    assert r.is_error and "Refused" in text(r)


# ---------- symlink escape ----------

@pytest.mark.anyio
@pytest.mark.parametrize("path", ["link-file.md", "link-dir/secret.md", "inside-link.md"])
async def test_symlink_refused(tree, path):
    r = await call(build(str(tree)), "read_note", {"path": path})
    assert r.is_error and "symlink" in text(r)
    assert SECRET not in text(r)


@pytest.mark.anyio
async def test_symlinks_not_listed_or_searched(tree):
    s = build(str(tree))
    listed = (await call(s, "list_notes", {})).structured_content["notes"]
    assert not any("link" in n for n in listed)
    r = await call(s, "search_notes", {"query": "TOP-SECRET"})
    assert r.structured_content == {"result": []}
    r = await call(s, "list_notes", {"folder": "link-dir"})
    assert r.is_error and "symlink" in text(r)


@pytest.mark.anyio
async def test_file_swapped_for_symlink_after_check(tree, monkeypatch):
    """The open itself uses O_NOFOLLOW, so a file replaced by a symlink after the path check is refused."""
    import server
    real_open = server.os.open

    def swap_then_open(p, flags, *a):
        os.remove(p)
        os.symlink(tree.parent / "outside" / "secret.md", p)
        return real_open(p, flags, *a)

    s = build(str(tree))
    monkeypatch.setattr(server.os, "open", swap_then_open)
    r = await call(s, "read_note", {"path": "inbox.md"})
    assert r.is_error and SECRET not in text(r)


def test_root_may_itself_be_a_symlink(tree, tmp_path):
    """Only links inside the folder are refused; the folder you point it at is resolved once at start."""
    (tmp_path / "alias").symlink_to(tree, target_is_directory=True)
    assert build(str(tmp_path / "alias")) is not None


# ---------- large file cap ----------

@pytest.mark.anyio
async def test_large_file_cap(tree):
    (tree / "big.md").write_text("x" * 5000 + "\nneedle\n")
    (tree / "small.md").write_text("needle\n")
    s = build(str(tree), max_bytes=4096)
    r = await call(s, "read_note", {"path": "big.md"})
    assert r.is_error and "over the 4096-byte cap" in text(r)
    r = await call(s, "read_note", {"path": "small.md"})
    assert not r.is_error and text(r) == "needle\n"
    r = await call(s, "search_notes", {"query": "needle"})  # search skips the big file
    assert [h["path"] for h in r.structured_content["result"]] == ["small.md"]


@pytest.mark.anyio
async def test_list_and_search_caps(tree):
    for i in range(30):
        (tree / f"n{i:02}.md").write_text("same line\n")
    s = build(str(tree), max_list=10)
    r = await call(s, "list_notes", {})
    assert len(r.structured_content["notes"]) == 10 and r.structured_content["truncated"] is True
    r = await call(s, "search_notes", {"query": "same", "max_results": 5})
    assert len(r.structured_content["result"]) == 5


# ---------- read-only behaviour ----------

@pytest.mark.anyio
async def test_only_three_tools_all_read_only(tree):
    async with Client(build(str(tree))) as c:
        tools = (await c.list_tools()).tools
    assert sorted(t.name for t in tools) == ["list_notes", "read_note", "search_notes"]
    for t in tools:
        assert t.annotations.read_only_hint is True and t.annotations.open_world_hint is False
        assert not {"content", "text", "data"} & set(t.input_schema.get("properties", {}))


@pytest.mark.anyio
async def test_no_write_tool(tree):
    s = build(str(tree))
    for tool in ["write_note", "delete_note", "create_note", "move_note"]:
        r = await call(s, tool, {"path": "inbox.md", "content": "x"})
        assert r.is_error
    assert (tree / "inbox.md").read_text().startswith("# Inbox")


@pytest.mark.anyio
async def test_folder_unchanged_after_every_tool(tree, monkeypatch):
    """Every tool, valid and refused calls alike: nothing under tmp is created, changed or deleted,
    and every os.open the server makes is read-only."""
    import server
    real_open, flags_seen = server.os.open, []

    def spy(p, flags, *a):
        flags_seen.append(flags)
        return real_open(p, flags, *a)

    monkeypatch.setattr(server.os, "open", spy)
    before = snapshot(tree.parent)
    s = build(str(tree))
    for tool, args in [("list_notes", {}), ("list_notes", {"folder": "projects"}),
                       ("search_notes", {"query": "e"}), ("read_note", {"path": "inbox.md"}),
                       ("read_note", {"path": "../outside/secret.md"}), ("read_note", {"path": "link-file.md"})]:
        await call(s, tool, args)
    assert snapshot(tree.parent) == before
    assert flags_seen and all(f & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND) == 0
                              for f in flags_seen)


# ---------- other inputs ----------

@pytest.mark.anyio
@pytest.mark.parametrize("path,msg", [("projects/draft.txt", "not a Markdown note"),
                                      ("projects", "not a Markdown note"), ("nope.md", "Not found")])
async def test_wrong_kind_or_missing(tree, path, msg):
    r = await call(build(str(tree)), "read_note", {"path": path})
    assert r.is_error and msg in text(r)


@pytest.mark.anyio
async def test_fifo_named_md_does_not_hang(tree):
    """A named pipe called pipe.md would block a plain open() until a writer appears; it must be refused
    at once. From 5 s on, a rescue thread keeps opening the write end, so a regression fails on
    time instead of hanging."""
    fifo = tree / "pipe.md"
    os.mkfifo(fifo)

    done = threading.Event()

    def rescue():
        while not done.wait(5 if not rescue.started else 0.2):
            rescue.started = True
            try:
                os.close(os.open(fifo, os.O_WRONLY | os.O_NONBLOCK))
            except OSError:
                pass  # ENXIO: nobody is blocked reading it, which is the pass case

    rescue.started = False
    threading.Thread(target=rescue, daemon=True).start()
    s, start = build(str(tree)), time.monotonic()
    r = await call(s, "read_note", {"path": "pipe.md"})
    assert r.is_error and "not a regular file" in text(r)
    r = await call(s, "search_notes", {"query": "milk"})
    assert [h["path"] for h in r.structured_content["result"]] == ["inbox.md"]
    done.set()
    assert time.monotonic() - start < 4, "open() blocked on the FIFO"


@pytest.mark.anyio
async def test_empty_query(tree):
    r = await call(build(str(tree)), "search_notes", {"query": "   "})
    assert r.is_error and "non-empty" in text(r)


def test_root_must_be_a_folder(tree):
    with pytest.raises(SystemExit):
        build(str(tree / "inbox.md"))
    with pytest.raises(SystemExit):
        build(str(tree / "missing"))


# ---------- the real stdio process ----------

@pytest.mark.anyio
async def test_stdio_end_to_end(tree):
    params = StdioServerParameters(command=sys.executable, args=[SERVER, str(tree)],
                                   env={"NOTES_MAX_BYTES": "10", "PATH": os.environ.get("PATH", "")})
    async with Client(params) as c:
        r = await c.call_tool("read_note", {"path": "projects/mcp.md"})
        assert r.is_error and "over the 10-byte cap" in text(r)
        r = await c.call_tool("read_note", {"path": "../outside/secret.md"})
        assert r.is_error and SECRET not in text(r)

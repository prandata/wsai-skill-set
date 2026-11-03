# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp==2.3.0"]
# ///
"""notes-readonly: list, search and read the Markdown notes in one folder, over MCP (stdio).
Read-only: no write tool, every file opened O_RDONLY. Contained: "..", absolute paths, hidden parts and
symlinks are refused. Run: uv run server.py /path/to/notes  (NOTES_MAX_BYTES: per-file cap, default 1 MB)"""
import os, stat, sys
from pathlib import Path, PurePosixPath
from typing_extensions import TypedDict  # pydantic needs this one on Python < 3.12
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

NOTE_SUFFIXES = {".md", ".markdown"}
READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
NoteList = TypedDict("NoteList", {"notes": list[str], "truncated": bool})
Hit = TypedDict("Hit", {"path": str, "line": int, "text": str})

def build(root: str, max_bytes: int = 1_000_000, max_list: int = 1000) -> MCPServer:
    base = Path(root).expanduser().resolve()
    if not base.is_dir(): raise SystemExit(f"notes-readonly: no such folder: {root}")
    mcp = MCPServer("notes-readonly", instructions="Read-only access to one folder of Markdown notes.")

    def safe_path(rel: str, want_dir: bool = False) -> Path:
        parts = PurePosixPath(rel.replace("\\", "/")).parts if rel not in ("", ".") else ()
        if "\0" in rel or (parts and parts[0] == "/") or any(p == ".." or p.startswith(".") for p in parts):
            raise ToolError(f"Refused: {rel!r} must be a plain path inside the notes folder.")
        p = base
        for part in parts:  # refuse a symlink at any level, even one that points back inside
            p = p / part
            if p.is_symlink():
                raise ToolError(f"Refused: {rel!r} goes through a symlink.")
        if not p.exists():
            raise ToolError(f"Not found: {rel!r}")
        if not p.resolve(strict=True).is_relative_to(base):  # second check, should never fire
            raise ToolError(f"Refused: {rel!r} is outside the notes folder.")
        if want_dir != p.is_dir() or (not want_dir and p.suffix.lower() not in NOTE_SUFFIXES):
            raise ToolError(f"Refused: {rel!r} is not a {'folder' if want_dir else 'Markdown note'}.")
        return p

    def read_text(p: Path) -> str:
        fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)  # no symlink swap, no FIFO hang
        with os.fdopen(fd, "rb") as f:
            st = os.fstat(f.fileno())
            if not stat.S_ISREG(st.st_mode):
                raise ToolError("Refused: not a regular file.")
            if st.st_size > max_bytes:
                raise ToolError(f"Refused: {st.st_size} bytes is over the {max_bytes}-byte cap.")
            return f.read(max_bytes + 1)[:max_bytes].decode("utf-8", errors="replace")

    def walk(start: Path) -> list[str]:
        found = []
        for d, dirs, files in os.walk(start):  # os.walk does not follow symlinked folders
            dirs[:] = sorted(x for x in dirs if not x.startswith(".") and not Path(d, x).is_symlink())
            for name in sorted(files):
                f = Path(d, name)
                if not name.startswith(".") and f.suffix.lower() in NOTE_SUFFIXES and not f.is_symlink():
                    found.append(f.relative_to(base).as_posix())
        return found

    @mcp.tool(annotations=READ_ONLY)
    def list_notes(folder: str = "") -> NoteList:
        """List Markdown notes (relative paths), optionally under one subfolder."""
        notes = walk(safe_path(folder, want_dir=True))
        return {"notes": notes[:max_list], "truncated": len(notes) > max_list}

    @mcp.tool(annotations=READ_ONLY)
    def search_notes(query: str, max_results: int = 20) -> list[Hit]:
        """Case-insensitive text search across all notes. Returns path, line number and line."""
        q, hits, limit = query.strip().lower(), [], max(1, min(max_results, 200))
        if not q:
            raise ToolError("Give a non-empty query.")
        for rel in walk(base):
            try:
                text = read_text(base / rel)
            except (ToolError, OSError):
                continue  # over the cap, or changed while searching: skip it
            for n, line in enumerate(text.splitlines(), 1):
                if q in line.lower():
                    hits.append({"path": rel, "line": n, "text": line.strip()[:300]})
                    if len(hits) >= limit:
                        return hits
        return hits

    @mcp.tool(annotations=READ_ONLY)
    def read_note(path: str) -> str:
        """Return the full text of one note, by the relative path list_notes gives."""
        try:
            return read_text(safe_path(path))
        except OSError as e:  # e.g. ELOOP when the file became a symlink after the check
            raise ToolError(f"Refused: could not open {path!r} ({e.strerror}).") from None

    return mcp


if __name__ == "__main__":
    if len(sys.argv) != 2: raise SystemExit("usage: server.py /path/to/notes")
    build(sys.argv[1], int(os.environ.get("NOTES_MAX_BYTES", "1000000"))).run()  # stdio

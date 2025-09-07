"""File operation tools with safety constraints."""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any
import re

from .registry import register_tool

_MAX_READ_BYTES = 200_000
_ALLOWED_ROOTS = [Path("/etc"), Path("/var"), Path("/tmp"), Path("/home"), Path.cwd()]


def _is_allowed(path: Path) -> bool:
    try:
        rp = path.resolve()
    except Exception:
        return False
    for root in _ALLOWED_ROOTS:
        try:
            if str(rp).startswith(str(root.resolve())):
                return True
        except Exception:
            continue
    return False


@register_tool(description="Read a text file (truncated) within allowed roots")
def read_file(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not _is_allowed(p):
        return {"error": "forbidden_path"}
    if not p.exists() or not p.is_file():
        return {"error": "not_found"}
    try:
        data = p.read_bytes()
        truncated = False
        if len(data) > _MAX_READ_BYTES:
            data = data[:_MAX_READ_BYTES]
            truncated = True
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = data.decode("latin-1", errors="replace")
        return {"path": str(p), "truncated": truncated, "content": text}
    except Exception as e:
        return {"error": "read_error", "message": str(e)}


@register_tool(description="List directory entries (shallow)")
def list_dir(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not _is_allowed(p):
        return {"error": "forbidden_path"}
    if not p.exists() or not p.is_dir():
        return {"error": "not_found"}
    try:
        entries = []
        for child in p.iterdir():
            entries.append({
                "name": child.name,
                "type": "dir" if child.is_dir() else "file",
                "size": child.stat().st_size if child.is_file() else None,
            })
        return {"path": str(p), "entries": entries}
    except Exception as e:
        return {"error": "list_error", "message": str(e)}


@register_tool(description="Search regex pattern in a text file (truncated)")
def search_pattern(path: str, pattern: str, ignore_case: bool = True, max_matches: int = 50) -> Dict[str, Any]:
    p = Path(path)
    if not _is_allowed(p):
        return {"error": "forbidden_path"}
    if not p.exists() or not p.is_file():
        return {"error": "not_found"}
    flags = re.IGNORECASE if ignore_case else 0
    try:
        text = p.read_text(errors="replace")
    except Exception as e:
        return {"error": "read_error", "message": str(e)}
    matches = []
    for m in re.finditer(pattern, text, flags):
        if len(matches) >= max_matches:
            break
        snippet_start = max(0, m.start() - 40)
        snippet_end = min(len(text), m.end() + 40)
        snippet = text[snippet_start:snippet_end]
        matches.append({
            "match": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "context": snippet,
        })
    return {"path": str(p), "pattern": pattern, "count": len(matches), "matches": matches}


__all__ = ["read_file", "list_dir", "search_pattern"]

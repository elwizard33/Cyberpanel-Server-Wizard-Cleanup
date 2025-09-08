from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional

ALLOWED_ROOTS = [Path("/etc"), Path("/usr"), Path("/var"), Path("/tmp"), Path("/home")]


def _is_allowed(path: Path) -> bool:
    try:
        rp = path.resolve()
    except Exception:
        return False
    return any(str(rp).startswith(str(root)) for root in ALLOWED_ROOTS)


def read_file(path: str, max_bytes: Optional[int] = 32_000) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"success": False, "error": "not_found", "path": path}
    if p.is_dir():
        return {"success": False, "error": "is_directory", "path": path}
    if not _is_allowed(p):
        return {"success": False, "error": "path_not_allowed", "path": path}
    try:
        data = p.read_bytes()
        truncated = False
        if max_bytes and len(data) > max_bytes:
            data = data[:max_bytes]
            truncated = True
        text = data.decode("utf-8", errors="replace")
        return {"success": True, "path": str(p), "truncated": truncated, "content": text}
    except Exception as e:  # pragma: no cover
        return {"success": False, "error": str(e), "path": path}

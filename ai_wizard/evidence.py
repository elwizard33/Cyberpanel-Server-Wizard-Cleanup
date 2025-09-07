"""Evidence preservation utilities.

Provides helper to optionally archive a file slated for remediation,
storing content hash and metadata in a structured directory tree under
the configured evidence directory.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List
import hashlib
import json
from datetime import datetime, timezone


def _safe_rel_name(path: Path) -> str:
    parts = [p for p in path.parts if p not in ("", "/")]
    return "__".join(parts)


def preserve_file(path: Path, evidence_dir: Path) -> Dict[str, Any]:
    """Copy file into evidence store with metadata + hash.

    Returns dict with keys: stored_path, sha256, size, timestamp
    On failure returns {error: ..} (non-fatal to caller).
    """
    try:
        if not path.exists() or not path.is_file():
            return {"error": "not_found"}
        evidence_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        subdir = evidence_dir / ts
        subdir.mkdir(exist_ok=True)
        data = path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        dest = subdir / (_safe_rel_name(path) or path.name)
        dest.write_bytes(data)
        meta = {
            "original_path": str(path),
            "stored_path": str(dest),
            "sha256": sha,
            "size": len(data),
            "timestamp": ts,
        }
        (dest.with_suffix(dest.suffix + ".meta.json")).write_text(json.dumps(meta, indent=2))
        return meta
    except Exception as e:  # pragma: no cover - best effort
        return {"error": "preserve_failed", "message": str(e)}


def save_last_scan(findings: List[Any], evidence_dir: Path) -> Path:
    """Persist findings JSON (id + severity) as last_scan.json.

    Returns path written or raises on unrecoverable IO errors. Best-effort size guard (512KB).
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out = evidence_dir / "last_scan.json"
    try:
        minimal = [
            {
                "id": getattr(f, "id", None),
                "severity": getattr(getattr(f, "severity", None), "value", None),
                "category": getattr(getattr(f, "category", None), "value", None),
            }
            for f in findings
        ]
        data = json.dumps(minimal, separators=(",", ":")).encode()
        if len(data) > 512 * 1024:
            # truncate list if too large
            cut = int(len(minimal) * 0.5)
            minimal = minimal[:cut]
            data = json.dumps(minimal, separators=(",", ":")).encode()
        out.write_bytes(data)
    except Exception:  # pragma: no cover
        pass
    return out


def load_last_scan(evidence_dir: Path) -> List[Dict[str, Any]]:
    path = evidence_dir / "last_scan.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list):
            return [d for d in data if isinstance(d, dict) and "id" in d]
    except Exception:  # pragma: no cover
        return []
    return []


__all__ = ["preserve_file", "save_last_scan", "load_last_scan"]

"""Evidence preservation functionality."""

from pathlib import Path
from typing import Dict, Any
import os
import json


"""Evidence preservation functionality."""

from pathlib import Path
from typing import Dict, Any
import shutil
import hashlib


def preserve_file(source_path: Path, evidence_dir: Path) -> Dict[str, Any]:
    """Preserve a file as evidence."""
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    # Create unique filename in evidence directory
    target_path = evidence_dir / source_path.name
    counter = 1
    while target_path.exists():
        stem = source_path.stem
        suffix = source_path.suffix
        target_path = evidence_dir / f"{stem}_{counter}{suffix}"
        counter += 1
    
    # Copy the file
    shutil.copy2(source_path, target_path)
    
    # Calculate SHA256 hash
    sha256_hash = hashlib.sha256()
    with open(source_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return {
        "source": str(source_path),
        "preserved_at": str(target_path),
        "stored_path": str(target_path),  # Alias for compatibility
        "size": source_path.stat().st_size,
        "sha256": sha256_hash.hexdigest(),
        "status": "preserved"
    }


def write_scan_snapshot(scan_results: Dict[str, Any]) -> None:
    """Optionally write a compact scan snapshot to CYBERZARD_EVIDENCE_DIR.

    Writes summary and a few top indicators; best-effort and silent on failure.
    """
    try:
        evidence_dir = os.getenv("CYBERZARD_EVIDENCE_DIR")
        if not evidence_dir:
            return
        p = Path(evidence_dir)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        if not os.access(str(p), os.W_OK):
            return
        # Build compact payload
        summary = scan_results.get("summary", {})
        payload = {"summary": summary}
        # Filename
        name = f"scan-{int(__import__('time').time())}.json"
        out = p / name
        tmp = p / (name + ".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, separators=(",", ":"))
        os.replace(tmp, out)
        os.chmod(out, 0o600)
    except Exception:
        # Silent best-effort
        return

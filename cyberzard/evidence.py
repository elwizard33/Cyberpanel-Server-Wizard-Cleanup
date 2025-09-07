"""Evidence preservation functionality."""

from pathlib import Path
from typing import Dict, Any


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

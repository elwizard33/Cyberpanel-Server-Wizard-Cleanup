"""File scanner functionality."""

from typing import List
from pathlib import Path
from ..core.models import Finding


class FileScanner:
    """Scanner for file system analysis."""

    def __init__(self):
        """Initialize the file scanner."""
        pass

    def scan_files(self, paths: List[str]) -> List[Finding]:
        """Scan files for potential issues."""
        findings = []
        for path_str in paths:
            path = Path(path_str)
            if path.exists():
                finding = Finding(
                    finding_id=f"file_{hash(path_str)}",
                    severity="info",
                    category="file_system",
                    title=f"File found: {path.name}",
                    description=f"File exists at {path}",
                    recommendations=["File is accessible"],
                    file_path=str(path)
                )
                findings.append(finding)
        return findings

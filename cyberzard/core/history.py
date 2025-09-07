"""History tracking for cyberzard operations."""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HistoryEntry:
    """A single history entry."""
    timestamp: datetime
    operation: str
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True


class OperationHistory:
    """Tracks operation history."""
    
    def __init__(self):
        self.entries: List[HistoryEntry] = []
        
    def add_entry(self, operation: str, details: Dict[str, Any] = None, success: bool = True):
        """Add a history entry."""
        entry = HistoryEntry(
            timestamp=datetime.now(),
            operation=operation,
            details=details or {},
            success=success
        )
        self.entries.append(entry)
        
    def get_recent(self, limit: int = 10) -> List[HistoryEntry]:
        """Get recent history entries."""
        return sorted(self.entries, key=lambda x: x.timestamp, reverse=True)[:limit]

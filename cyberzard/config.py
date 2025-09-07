"""Configuration and action classes for cyberzard."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


"""Configuration and action classes for cyberzard."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """Types of remediation actions."""
    REMOVE = "remove"
    KILL = "kill"
    MODIFY = "modify"
    BACKUP = "backup"


@dataclass
class RecommendedAction:
    """A recommended action that can be taken."""
    action_id: str
    title: str
    description: str
    command: Optional[str] = None
    file_path: Optional[str] = None
    backup_required: bool = True
    risk_level: str = "medium"
    
    # Add class attributes for compatibility
    remove = ActionType.REMOVE
    kill = ActionType.KILL
    modify = ActionType.MODIFY
    backup = ActionType.BACKUP
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action_id": self.action_id,
            "title": self.title,
            "description": self.description,
            "command": self.command,
            "file_path": self.file_path,
            "backup_required": self.backup_required,
            "risk_level": self.risk_level
        }


class CyberzardConfig:
    """Configuration manager for cyberzard."""
    
    def __init__(self):
        """Initialize with default configuration."""
        self.config = {
            "scan_depth": 3,
            "max_findings": 100,
            "output_format": "json",
            "backup_directory": "/tmp/cyberzard_backups",
            "dry_run": False
        }
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values."""
        self.config.update(updates)

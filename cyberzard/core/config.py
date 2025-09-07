"""Configuration management for cyberzard."""

from typing import Dict, Any
from pathlib import Path


DEFAULT_CONFIG = {
    "scan_paths": ["/etc", "/var/log", "/home"],
    "output_format": "json",
    "verbose": False,
    "max_findings": 100
}


class Config:
    """Configuration manager."""

    def __init__(self, config_path: str = None):
        """Initialize configuration."""
        self.config_path = Path(config_path) if config_path else None
        self._config = DEFAULT_CONFIG.copy()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or defaults."""
        # For now, just return defaults
        return self._config.copy()

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._config[key] = value

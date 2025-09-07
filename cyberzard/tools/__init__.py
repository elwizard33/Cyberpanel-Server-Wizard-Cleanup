"""Tools module for cyberzard."""

from typing import Dict, Any


def get_system_info() -> Dict[str, Any]:
    """Get basic system information."""
    return {
        "platform": "linux",
        "version": "1.0.0",
        "status": "active"
    }

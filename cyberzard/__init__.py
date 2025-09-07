"""Cyberzard package (renamed from ai_wizard).

This thin compatibility layer re-exports symbols from the legacy ai_wizard
package so existing internal code continues to function while the repository
is migrated. Future development should target this package path directly.
"""

from .config import *  # type: ignore # noqa: F401,F403
from .core.models import *  # type: ignore # noqa: F401,F403

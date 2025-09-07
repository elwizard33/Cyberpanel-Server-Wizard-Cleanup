"""Cyberzard package (renamed from ai_wizard).

This thin compatibility layer re-exports symbols from the legacy ai_wizard
package so existing internal code continues to function while the repository
is migrated. Future development should target this package path directly.
"""

from ai_wizard.config import *  # noqa: F401,F403
from ai_wizard.core.models import *  # noqa: F401,F403

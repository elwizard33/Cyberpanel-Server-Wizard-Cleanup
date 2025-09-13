__all__ = ["run_agent", "scan_email_system", "propose_email_hardening"]

from .agent import run_agent  # noqa: E402
"""Cyberzard package (renamed from cyberzard).

This thin compatibility layer re-exports symbols from the legacy cyberzard
package so existing internal code continues to function while the repository
is migrated. Future development should target this package path directly.
"""

from .config import *  # type: ignore # noqa: F401,F403
from .core.models import *  # type: ignore # noqa: F401,F403

# Optional email scan exports
try:  # pragma: no cover
	from .agent_engine.tools.email_scan import scan_email_system, propose_email_hardening  # noqa: F401
except Exception:  # pragma: no cover
	pass

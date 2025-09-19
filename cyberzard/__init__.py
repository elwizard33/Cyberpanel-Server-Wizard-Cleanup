__all__ = ["run_agent", "scan_email_system", "propose_email_hardening", "__version__"]

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

# Central version export
try:
	from ._version import __version__  # type: ignore
except Exception:  # pragma: no cover
	try:
		# Fallback to package metadata when installed
		from importlib.metadata import version as _pkg_version  # type: ignore

		__version__ = _pkg_version("cyberzard")  # type: ignore
	except Exception:  # final fallback for editable/dev
		__version__ = "0.1.11"

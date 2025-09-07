"""Legacy package (deprecated).

Importing from `ai_wizard` is deprecated. Use `cyberzard` instead.
This shim will be removed in a future release.
"""

import warnings as _warnings

_warnings.warn(
	"Package 'ai_wizard' is deprecated; use 'cyberzard' instead.",
	DeprecationWarning,
	stacklevel=2,
)

__all__ = []

"""Agent engine package exports.

Re-exports optional email provider helpers when available.
"""

from .provider import summarize, justify_actions  # noqa: F401

try:  # pragma: no cover - optional
    from .provider_email import (
        summarize_email_security,
        generate_email_fix_guide,
        justify_email_action,
        refine_email_action,
    )  # noqa: F401
except Exception:  # pragma: no cover
    pass

__all__ = [
    "summarize",
    "justify_actions",
    "summarize_email_security",
    "generate_email_fix_guide",
    "justify_email_action",
    "refine_email_action",
]

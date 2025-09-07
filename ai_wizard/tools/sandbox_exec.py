"""Sandboxed code execution tool.

Wraps the security sandbox execute_code helper as a registered tool so
AI providers can request safe evaluation of tiny snippets for parsing
or light transformation logic. The sandbox forbids imports and other
dangerous constructs and enforces CPU/memory/time limits.
"""
from __future__ import annotations

from typing import Dict, Any

from cyberzard.security.sandbox import execute_code as _execute_code
from .registry import register_tool

_MAX_SOURCE_LEN = 4000
_MAX_TIMEOUT = 5.0


@register_tool(description="Execute restricted python snippet in sandbox (no imports, low resource limits)")
def sandbox_run(source: str, timeout: float = 2.0) -> Dict[str, Any]:
    """Run a minimal Python snippet in a hardened sandbox.

    Parameters:
        source: Python code (no imports, no try/with/raise, etc.).
        timeout: Seconds before force termination (<=5s).

    Returns dict with either error or keys: returncode, stdout, stderr.
    """
    if not source.strip():
        return {"error": "empty_source"}
    if len(source) > _MAX_SOURCE_LEN:
        return {"error": "too_large"}
    if timeout <= 0:
        timeout = 0.5
    if timeout > _MAX_TIMEOUT:
        timeout = _MAX_TIMEOUT
    result = _execute_code(source, timeout=timeout)
    return result


__all__ = ["sandbox_run"]

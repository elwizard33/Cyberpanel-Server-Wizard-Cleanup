"""Restricted Python code execution sandbox."""
from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any

from .limits import apply_limits

# Disallowed AST nodes for safety
_BLOCKED = {
    ast.Import,
    ast.ImportFrom,
    ast.With,
    ast.Try,
    ast.Raise,
    ast.Lambda,
    ast.AsyncFunctionDef,
}

_ALLOWED_BUILTINS = {
    "len": len,
    "range": range,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "print": print,
}


def validate_source(source: str) -> str | None:
    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError as e:
        return f"syntax_error: {e}"
    for node in ast.walk(tree):
        if any(isinstance(node, b) for b in _BLOCKED):
            return f"blocked_node: {node.__class__.__name__}"
    return None


def execute_code(source: str, timeout: float = 2.5) -> Dict[str, Any]:
    err = validate_source(source)
    if err:
        return {"error": err}
    # Write to temp file and spawn subprocess with limits
    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / "snippet.py"
        script.write_text(source)
        cmd = [sys.executable, str(script)]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=apply_limits,  # POSIX
                env={"PYTHONSAFEPATH": "1"},
            )
        except subprocess.TimeoutExpired:
            return {"error": "timeout"}
        except Exception as e:
            return {"error": "spawn_error", "message": str(e)}
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[:10_000],
            "stderr": result.stderr[:10_000],
        }

__all__ = ["validate_source", "execute_code"]

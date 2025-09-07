"""Resource limit helpers for sandboxed execution."""
from __future__ import annotations

import resource  # POSIX only

_CPU_SECONDS = 2
_MAX_MEMORY_BYTES = 128 * 1024 * 1024  # 128MB


def apply_limits():  # pragma: no cover - platform dependent
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (_CPU_SECONDS, _CPU_SECONDS))
        resource.setrlimit(resource.RLIMIT_AS, (_MAX_MEMORY_BYTES, _MAX_MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
    except Exception:
        pass

__all__ = ["apply_limits"]

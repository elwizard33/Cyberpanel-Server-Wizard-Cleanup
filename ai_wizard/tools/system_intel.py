"""System intelligence tools (resource & process snapshot)."""
from __future__ import annotations

import platform
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

import psutil  # type: ignore

from .registry import register_tool

_MAX_PROCESSES = 400


def _proc_entry(p: psutil.Process) -> Dict[str, Any]:
    try:
        with p.oneshot():
            info = {
                "pid": p.pid,
                "name": p.name(),
                "cmdline": " ".join(p.cmdline()[:20]),
                "user": p.username(),
                "cpu": p.cpu_percent(interval=None),
                "mem": p.memory_info().rss,
            }
            return info
    except Exception:
        return {"pid": p.pid, "error": True}


@register_tool(description="Return high-level system overview stats")
def system_overview() -> Dict[str, Any]:
    vm = psutil.virtual_memory()
    loadavg = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=True),
        "load": loadavg,
        "memory": {"total": vm.total, "used": vm.used, "percent": vm.percent},
        "disk_percent_root": psutil.disk_usage("/").percent,
    }


@register_tool(description="List running processes (capped)")
def list_processes(limit: int = 100) -> Dict[str, Any]:
    if limit > _MAX_PROCESSES:
        limit = _MAX_PROCESSES
    procs: List[Dict[str, Any]] = []
    for p in psutil.process_iter(attrs=[]):
        if len(procs) >= limit:
            break
        procs.append(_proc_entry(p))
    return {"count": len(procs), "processes": procs}


__all__ = ["system_overview", "list_processes"]

"""History persistence for conversations and scans.

Stores a capped list (max 50) of recent events in JSON array form.
File: ~/.cyberpanel_cyberzard/history.json
Atomic writes with truncate. Can be disabled.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_HISTORY_PATH = Path.home() / ".cyberpanel_cyberzard" / "history.json"
MAX_HISTORY_ITEMS = 50


class HistoryStore:
    def __init__(self, path: Path = DEFAULT_HISTORY_PATH, max_items: int = MAX_HISTORY_ITEMS, disabled: bool = False) -> None:
        self.path = path
        self.max_items = max_items
        self.disabled = disabled
        self._items: List[Dict[str, Any]] = []
        if not self.disabled:
            self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self._items = data[-self.max_items :]
        except Exception:
            self._items = []

    def add(self, entry: Dict[str, Any]) -> None:
        if self.disabled:
            return
        record = {"ts": time.time(), **entry}
        self._items.append(record)
        if len(self._items) > self.max_items:
            self._items = self._items[-self.max_items :]
        self._save()

    def list(self) -> List[Dict[str, Any]]:
        return list(self._items)

    def _save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._items, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.path)
        except Exception:
            pass


__all__ = [
    "HistoryStore",
    "DEFAULT_HISTORY_PATH",
    "MAX_HISTORY_ITEMS",
]

"""Scanner base classes and registry with context object."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Type, Optional, Callable
import logging

from cyberzard.core.models import Finding
from cyberzard.config import Settings, get_settings


class ScanContext:
    """Holds shared runtime state for scanners.

    Add lightweight caches (e.g., process list) later as needed.
    """

    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger("cyberzard.scanner")
        self.cache: Dict[str, object] = {}


class BaseScanner(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    def scan(self, context: ScanContext) -> List[Finding]:  # pragma: no cover - interface
        ...

    def _log(self, context: ScanContext, msg: str) -> None:  # pragma: no cover - passthrough
        context.logger.debug(f"[{self.name}] {msg}")


_REGISTRY: Dict[str, Type[BaseScanner]] = {}


def register(scanner_cls: Type[BaseScanner]) -> Type[BaseScanner]:
    _REGISTRY[scanner_cls.name] = scanner_cls
    return scanner_cls


def get_scanner_classes() -> List[Type[BaseScanner]]:
    return list(_REGISTRY.values())


__all__ = ["BaseScanner", "ScanContext", "register", "get_scanner_classes"]

"""Logging setup utilities for AI Wizard.

Provides init_logging() to configure both console and rotating file logging.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Any, Dict
import json
import time

try:
    from rich.logging import RichHandler  # type: ignore
    _HAS_RICH = True
except Exception:  # pragma: no cover
    _HAS_RICH = False


DEFAULT_LOG_FILE = Path("/var/log/cyberpanel_cyberzard.log")
FALLBACK_LOG_FILE = Path("./cyberpanel_cyberzard.log")

_ACTIVE_LOG_FILE: Path = DEFAULT_LOG_FILE
_INITIALIZED = False


def ensure_log_dir(path: Path) -> None:
    if path.parent != Path('.'):
        path.parent.mkdir(parents=True, exist_ok=True)


def init_logging(verbosity: int = 0, log_file: Optional[Path] = None) -> None:
    """Initialize application logging.

    verbosity: 0=INFO, 1=DEBUG
    log_file: optional override path
    """

    level = logging.DEBUG if verbosity > 0 else logging.INFO

    global _ACTIVE_LOG_FILE, _INITIALIZED
    if _INITIALIZED:
        return
    lf = log_file or DEFAULT_LOG_FILE
    try:
        ensure_log_dir(lf)
        with open(lf, 'a'):
            pass
    except Exception:
        lf = FALLBACK_LOG_FILE
        ensure_log_dir(lf)
    _ACTIVE_LOG_FILE = lf

    handlers = []

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        lf, maxBytes=2 * 1024 * 1024, backupCount=5
    )
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    handlers.append(file_handler)

    # Console handler (rich if available)
    if _HAS_RICH:
        console_handler = RichHandler(rich_tracebacks=True, markup=True)
        console_handler.setLevel(level)
    else:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    logger = logging.getLogger("cyberzard")
    logger.setLevel(level)
    for h in handlers:
        logger.addHandler(h)
    logger.debug("Logging initialized (level=%s, file=%s)", level, lf)
    _INITIALIZED = True


def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """Write a structured JSON line event.

    event_type: short classifier (e.g. scan_start, finding, remediation_action)
    data: additional serializable fields
    """
    record = {
        "ts": time.time(),
        "event": event_type,
        **data,
    }
    try:
        with open(_ACTIVE_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    except Exception:
        logging.getLogger("cyberzard").debug("Failed to write structured event", exc_info=True)


__all__ = ["init_logging", "log_event", "ensure_log_dir", "DEFAULT_LOG_FILE", "FALLBACK_LOG_FILE"]

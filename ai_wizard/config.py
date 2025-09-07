"""Configuration, IOC constants, and runtime settings for CyberPanel AI Wizard.

This module centralizes indicator-of-compromise (IOC) lists replicated and
extended from the existing bash cleanup scripts, plus runtime configuration
parsed from environment variables.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple, Set
import os
import re

from pydantic import BaseModel, Field, validator


# =============================
# Enums
# =============================


class Severity(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class Category(str, Enum):
    file = "file"
    process = "process"
    service = "service"
    cron = "cron"
    user = "user"
    ssh_key = "ssh_key"
    encryption = "encryption"
    composite = "composite"


class RecommendedAction(str, Enum):
    remove = "remove"
    kill = "kill"
    disable = "disable"
    investigate = "investigate"
    review = "review"
    confirm = "confirm"
    eradicate = "eradicate"  # Deep multi-step remediation


# =============================
# IOC Lists (sourced from bash scripts + minor extensions)
# =============================

MALICIOUS_FILE_PATHS: List[str] = [
    "/etc/data/kinsing",
    "/etc/kinsing",
    "/tmp/kdevtmpfsi",
    "/usr/lib/secure",
    "/usr/lib/secure/udiskssd",
    "/usr/bin/network-setup.sh",
    "/usr/.sshd-network-service.sh",
    "/usr/.network-setup",
    "/usr/.network-setup/config.json",
    "/usr/.network-setup/xmrig-*tar.gz",  # wildcard retained for pattern reference
    "/usr/.network-watchdog.sh",
    "/etc/data/libsystem.so",
    "/dev/shm/kdevtmpfsi",
    "/tmp/.ICEd-unix",
    "/var/tmp/.ICEd-unix",
]

PROCESS_PATTERNS: List[str] = [
    "kinsing",
    "udiskssd",
    "kdevtmpfsi",
    "bash2",
    "syshd",
    "atdb",
    "xmrig",
    "xmrigDaemon",
    "xmrigMiner",
    "xmrigMinerd",
    "xmrigMinerDaemon",
]

# Pre-compiled OR regex for quick scanning of process command lines.
PROCESS_REGEX = re.compile(r"(" + "|".join(re.escape(p) for p in PROCESS_PATTERNS) + r")", re.IGNORECASE)

SUSPICIOUS_SERVICE_NAMES: List[str] = [
    "bot",
    "system_d",
    "sshd-network-service",
    "network-monitor",
]

CRON_SUSPICIOUS_TOKENS: List[str] = [
    "kdevtmpfsi",
    "unk.sh",
    "atdb",
    "cp.sh",
    "p.sh",
    "wget",
    "curl",
]

ENCRYPTED_EXTS: Set[str] = {".psaux", ".encryp", ".locked"}

ENCRYPTED_SEARCH_ROOTS: List[str] = [
    "/home",
    "/var/www",
    "/tmp",
    "/etc/data",
]

# Maximum findings for encrypted file scan to prevent runaway traversal.
MAX_ENCRYPTED_FINDINGS = 500

# Paths we consider acceptable for deletion actions (unless force override).
ALLOWLIST_PATHS: Tuple[str, ...] = (
    "/etc",
    "/usr",
    "/var",
    "/tmp",
    "/dev/shm",
    "/root",
    "/home",
)


# =============================
# Settings Model
# =============================


class Settings(BaseModel):
    evidence_dir: Path = Field(default=Path("/var/lib/cyberzard/evidence"))
    dry_run: bool = True
    preserve_evidence: bool = False
    force: bool = False
    severity_filter: Optional[Severity] = None
    model_provider: str = "none"  # "anthropic" | "openai" | "none"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    max_ai_context_bytes: int = 8000
    no_history: bool = False

    @validator("model_provider")
    def _validate_provider(cls, v: str) -> str:
        allowed = {"anthropic", "openai", "none"}
        return v if v in allowed else "none"

    @classmethod
    def from_env(cls) -> "Settings":
        provider = os.getenv("CYBERZARD_MODEL_PROVIDER", "none").lower()
        settings = cls(
            evidence_dir=Path(os.getenv("CYBERZARD_EVIDENCE_DIR", "/var/lib/cyberzard/evidence")),
            dry_run=os.getenv("CYBERZARD_DRY_RUN", "true").lower() == "true",
            preserve_evidence=os.getenv("CYBERZARD_PRESERVE_EVIDENCE", "false").lower() == "true",
            force=os.getenv("CYBERZARD_FORCE", "false").lower() == "true",
            severity_filter=Severity(os.getenv("CYBERZARD_SEVERITY_FILTER")) if os.getenv("CYBERZARD_SEVERITY_FILTER") else None,
            model_provider=provider,
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            max_ai_context_bytes=int(os.getenv("CYBERZARD_MAX_CONTEXT_BYTES", "8000")),
            no_history=os.getenv("CYBERZARD_NO_HISTORY", "false").lower() == "true",
        )

        # Auto-disable provider if key missing.
        if settings.model_provider == "anthropic" and not settings.anthropic_api_key:
            settings.model_provider = "none"
        if settings.model_provider == "openai" and not settings.openai_api_key:
            settings.model_provider = "none"
        return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


# =============================
# Helper utilities
# =============================


def is_path_allowed(path: Path) -> bool:
    """Return True if path is inside an allowlisted top-level directory."""
    try:
        resolved = path.resolve()
    except Exception:
        return False
    for root in ALLOWLIST_PATHS:
        try:
            if str(resolved).startswith(root):
                return True
        except Exception:
            continue
    return False


def is_encrypted_candidate(path: Path) -> bool:
    return path.suffix in ENCRYPTED_EXTS


__all__ = [
    "Severity",
    "Category",
    "RecommendedAction",
    "MALICIOUS_FILE_PATHS",
    "PROCESS_PATTERNS",
    "PROCESS_REGEX",
    "SUSPICIOUS_SERVICE_NAMES",
    "CRON_SUSPICIOUS_TOKENS",
    "ENCRYPTED_EXTS",
    "ENCRYPTED_SEARCH_ROOTS",
    "MAX_ENCRYPTED_FINDINGS",
    "ALLOWLIST_PATHS",
    "Settings",
    "get_settings",
    "is_path_allowed",
    "is_encrypted_candidate",
]

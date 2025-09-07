"""User & sudo anomaly scanner."""
from __future__ import annotations

import grp
from pathlib import Path
from typing import List

from cyberzard.config import Severity, Category, RecommendedAction
from cyberzard.core.models import Finding
from cyberzard.scanners.base import BaseScanner, register, ScanContext

PASSWD_PATH = Path("/etc/passwd")

SYSTEM_UID_MAX = 999  # typical on many distros
VALID_USERNAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
ALLOWED_SUDO_USERS = {"root", "ubuntu", "ec2-user", "admin"}


@register
class UsersScanner(BaseScanner):
    name = "users"
    description = "Detects anomalous users and unexpected sudo privileges."

    def scan(self, context: ScanContext) -> List[Finding]:
        findings: List[Finding] = []
        if not PASSWD_PATH.exists():
            return findings
        try:
            sudo_members = set()
            try:
                sudo_members.update(grp.getgrnam("sudo").gr_mem)
            except KeyError:
                pass
            try:
                wheel_members = grp.getgrnam("wheel").gr_mem
                sudo_members.update(wheel_members)
            except KeyError:
                pass
        except Exception:
            sudo_members = set()

        for line in PASSWD_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) < 7:
                continue
            username, _pw, uid_str, gid_str, comment, home, shell = parts[:7]
            try:
                uid = int(uid_str)
            except ValueError:
                uid = -1

            # Username validation
            if not username or any(ch not in VALID_USERNAME_CHARS for ch in username):
                findings.append(
                    Finding(
                        category=Category.user,
                        severity=Severity.medium,
                        indicator=username,
                        message=f"Malformed username: {username}",
                        rationale="Username contains invalid characters",
                        recommended_action=RecommendedAction.review,
                        extra={"uid": uid, "home": home},
                    )
                )

            # Suspicious UID range (non-system UID using system range or vice versa)
            if 0 < uid <= SYSTEM_UID_MAX and username not in {"root"}:
                findings.append(
                    Finding(
                        category=Category.user,
                        severity=Severity.medium,
                        indicator=str(uid),
                        message=f"User {username} has system-range UID {uid}",
                        rationale="System UID range anomaly",
                        recommended_action=RecommendedAction.review,
                        extra={"home": home},
                    )
                )

            # Unexpected sudo privileges
            if username in sudo_members and username not in ALLOWED_SUDO_USERS:
                findings.append(
                    Finding(
                        category=Category.user,
                        severity=Severity.high,
                        indicator=username,
                        message=f"Unexpected sudo-capable user: {username}",
                        rationale="User in sudo/wheel group but not in allow list",
                        recommended_action=RecommendedAction.review,
                        removable=False,
                        extra={"uid": uid, "home": home},
                    )
                )
        return findings


__all__ = ["UsersScanner"]

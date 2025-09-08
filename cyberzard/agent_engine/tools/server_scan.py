from __future__ import annotations

import os
import re
import subprocess
from typing import Dict, Any, List

MALICIOUS_FILE_CANDIDATES = [
    "/etc/data/kinsing",
    "/etc/kinsing",
    "/tmp/kdevtmpfsi",
    "/usr/lib/secure",
    "/usr/lib/secure/udiskssd",
    "/usr/bin/network-setup.sh",
    "/usr/.sshd-network-service.sh",
    "/usr/.network-setup",
    "/usr/.network-watchdog.sh",
    "/etc/data/libsystem.so",
    "/dev/shm/kdevtmpfsi",
]

PROCESS_PATTERNS = ["kinsing", "udiskssd", "kdevtmpfsi", "bash2", "syshd", "atdb", "xmrig"]
ENCRYPTED_EXTENSIONS = [".psaux", ".encryp", ".locked"]


def _check_processes() -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    try:
        ps_output = subprocess.check_output(["ps", "aux"], text=True, errors="ignore")
    except Exception:
        return results
    for pat in PROCESS_PATTERNS:
        if re.search(rf"\b{re.escape(pat)}\b", ps_output):
            lines = [ln for ln in ps_output.splitlines() if pat in ln][:10]
            results.append({"indicator": pat, "matches": lines})
    return results


def _find_malicious_files() -> List[str]:
    found = []
    for f in MALICIOUS_FILE_CANDIDATES:
        if os.path.exists(f):
            found.append(f)
    return found


def _find_encrypted(include: bool) -> List[str]:
    if not include:
        return []
    hits: List[str] = []
    for root in ["/tmp", "/var/tmp", "/home", "/etc", "/usr/local/CyberCP"]:
        if not os.path.exists(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            for name in filenames:
                if any(name.endswith(ext) for ext in ENCRYPTED_EXTENSIONS):
                    hits.append(os.path.join(dirpath, name))
            if len(hits) > 250:
                return hits
    return hits


def scan_server(include_encrypted: bool = False) -> Dict[str, Any]:
    malicious = _find_malicious_files()
    processes = _check_processes()
    encrypted = _find_encrypted(include_encrypted)
    summary = {
        "malicious_file_count": len(malicious),
        "suspicious_process_groups": len(processes),
        "encrypted_file_count": len(encrypted),
    }
    return {
        "success": True,
        "summary": summary,
        "malicious_files": malicious,
        "suspicious_processes": processes,
        "encrypted_files": encrypted,
    }


def propose_remediation(scan_results: Dict[str, Any]) -> Dict[str, Any]:
    actions = []
    for f in scan_results.get("malicious_files", []):
        actions.append({
            "type": "remove_file",
            "target": f,
            "risk": "low",
            "reason": "Known IOC path",
            "command_preview": f"rm -f '{f}'",
        })
    for group in scan_results.get("suspicious_processes", []):
        indicator = group.get("indicator")
        actions.append({
            "type": "kill_process_group",
            "pattern": indicator,
            "risk": "medium",
            "reason": "Suspicious process name",
            "command_preview": f"pkill -9 -f '{indicator}'",
        })
    plan = {"total_actions": len(actions), "dry_run": True, "actions": actions}
    return {"success": True, "plan": plan}

__all__ = ["scan_server", "propose_remediation"]

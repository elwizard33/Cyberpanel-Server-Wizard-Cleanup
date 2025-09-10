from __future__ import annotations

import os
import re
import subprocess
import shutil
import pwd
import stat
from typing import Dict, Any, List
from typing import Tuple

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

# Suspicious cron patterns often seen in common compromises
CRON_SUSPICIOUS_REGEX = re.compile(
    r"(kdevtmpfsi|unk\.sh|\batdb\b|cp\.sh|\bp\.sh\b|wget\s+http|curl\s+http)",
    re.IGNORECASE,
)


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


def _scan_cron_jobs() -> Dict[str, Any]:
    """Inspect root cron files for suspicious entries.

    Checks typical root cron locations and scans lines using CRON_SUSPICIOUS_REGEX.
    Returns a structured payload with files checked and suspicious entries.
    """
    candidates = [
        "/var/spool/cron/crontabs/root",  # Debian/Ubuntu
        "/var/spool/cron/root",  # RHEL/CentOS
    ]
    files_checked: List[str] = []
    suspicious_entries: List[Dict[str, Any]] = []

    for path in candidates:
        if not os.path.exists(path):
            continue
        files_checked.append(path)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for idx, line in enumerate(fh, start=1):
                    m = CRON_SUSPICIOUS_REGEX.search(line)
                    if m:
                        text = line.strip()
                        if len(text) > 300:
                            text = text[:297] + "..."
                        suspicious_entries.append(
                            {
                                "file": path,
                                "line_no": idx,
                                "text": text,
                                "matched": m.group(0),
                            }
                        )
        except Exception:
            # Permission or transient read issues should not break scan
            continue

    return {
        "files_checked": files_checked,
        "suspicious_entries": suspicious_entries,
        "counts": {
            "total": len(files_checked),
            "suspicious": len(suspicious_entries),
        },
    }


def _scan_systemd_units() -> Dict[str, Any]:
    """Check suspicious systemd unit names and their status.

    Looks for known suspicious names and inspects status via systemctl when available.
    Also attempts to read excerpts from unit files in /etc/systemd/system.
    """
    suspects = ["bot", "system_d", "sshd-network-service", "network-monitor"]
    has_systemctl = shutil.which("systemctl") is not None

    units_found: List[Dict[str, Any]] = []
    active_count = 0

    for name in suspects:
        unit = f"{name}.service"
        status = "unknown"
        if has_systemctl:
            try:
                cp = subprocess.run(
                    ["systemctl", "is-active", unit],
                    text=True,
                    capture_output=True,
                    timeout=2,
                )
                s = cp.stdout.strip() or cp.stderr.strip()
                if s:
                    status = s
            except Exception:
                status = "unknown"
        unit_file = os.path.join("/etc/systemd/system", unit)
        excerpt = None
        if os.path.exists(unit_file):
            try:
                with open(unit_file, "r", encoding="utf-8", errors="ignore") as fh:
                    excerpt = "".join([next(fh, "") for _ in range(20)])
            except Exception:
                excerpt = None
        if status == "active":
            active_count += 1
        units_found.append(
            {
                "name": name,
                "unit": unit,
                "status": status,
                "unit_file": unit_file if os.path.exists(unit_file) else None,
                "excerpt": excerpt,
            }
        )

    return {
        "units_found": units_found,
        "counts": {"total": len(units_found), "active": active_count, "suspicious_named": len(units_found)},
    }


def _scan_users_and_ssh() -> Dict[str, Any]:
    """Enumerate users and inspect authorized_keys files.

    Includes root and users with uid >= 1000 and valid home directories.
    Returns users list and ssh findings with counts.
    """
    users: List[Dict[str, Any]] = []
    ssh_findings: List[Dict[str, Any]] = []
    total_keys = 0

    try:
        entries = pwd.getpwall()
    except Exception:
        entries = []

    # collect root and non-system users
    for pw in entries:
        try:
            name = pw.pw_name
            uid = pw.pw_uid
            home = pw.pw_dir
        except Exception:
            continue
        if name == "root" or (isinstance(uid, int) and uid >= 1000):
            if home and os.path.isdir(home):
                users.append({"name": name, "uid": uid, "home": home})

    for u in users:
        ak_path = os.path.join(u["home"], ".ssh", "authorized_keys")
        if not os.path.exists(ak_path):
            continue
        count = 0
        keys_sample: List[str] = []
        mode_str = None
        try:
            st = os.stat(ak_path)
            mode_str = oct(st.st_mode & 0o777)
        except Exception:
            mode_str = None
        try:
            with open(ak_path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    s = line.strip()
                    if not s or s.startswith("#"):
                        continue
                    count += 1
                    if len(keys_sample) < 3:
                        keys_sample.append(s[:120])
        except Exception:
            continue
        total_keys += count
        ssh_findings.append(
            {
                "user": u["name"],
                "path": ak_path,
                "count": count,
                "keys_detected": keys_sample,
                "mode": mode_str,
            }
        )

    return {
        "users": users,
        "ssh_findings": ssh_findings,
        "counts": {"users": len(users), "keys_files": len(ssh_findings), "total_keys": total_keys},
    }


def _check_ld_preload() -> Dict[str, Any]:
    path = "/etc/ld.so.preload"
    exists = os.path.exists(path)
    size = None
    excerpt = None
    if exists:
        try:
            size = os.path.getsize(path)
        except Exception:
            size = None
        try:
            with open(path, "rb") as fh:
                data = fh.read(200)
                excerpt = data.decode("utf-8", errors="ignore")
        except Exception:
            excerpt = None
    return {"exists": exists, "size": size, "excerpt": excerpt}


def _check_cyberpanel_integrity() -> Dict[str, Any]:
    base = "/usr/local/CyberCP"
    files_to_check = [
        os.path.join(base, "databases", "views.py"),
        os.path.join(base, "CyberCP", "settings.py"),
    ]
    base_exists = os.path.isdir(base)
    records: List[Dict[str, Any]] = []
    present = 0
    for p in files_to_check:
        exists = os.path.exists(p)
        sz = None
        mt = None
        if exists:
            present += 1
            try:
                sz = os.path.getsize(p)
            except Exception:
                sz = None
            try:
                mt = os.path.getmtime(p)
            except Exception:
                mt = None
        records.append({"path": p, "exists": exists, "size": sz, "mtime": mt})
    return {
        "base_exists": base_exists,
        "files": records,
        "counts": {"present": present, "missing": len(files_to_check) - present},
    }


def scan_server(include_encrypted: bool = False) -> Dict[str, Any]:
    malicious = _find_malicious_files()
    processes = _check_processes()
    encrypted = _find_encrypted(include_encrypted)
    cron = _scan_cron_jobs()
    systemd = _scan_systemd_units()
    users = _scan_users_and_ssh()
    ld_preload = _check_ld_preload()
    cyberpanel = _check_cyberpanel_integrity()

    summary = {
        "malicious_file_count": len(malicious),
        "suspicious_process_groups": len(processes),
        "encrypted_file_count": len(encrypted),
        "cron_suspicious_count": len(cron.get("suspicious_entries", [])),
        "systemd_units_count": len(systemd.get("units_found", [])),
        "users_count": len(users.get("users", [])),
        "ssh_keys_files": users.get("counts", {}).get("keys_files", 0),
        "ld_preload_exists": bool(ld_preload.get("exists")),
        "cyberpanel_files_present": cyberpanel.get("counts", {}).get("present", 0),
    }
    return {
        "success": True,
        "summary": summary,
        "malicious_files": malicious,
        "suspicious_processes": processes,
        "encrypted_files": encrypted,
        "cron": cron,
        "systemd": systemd,
        "users": users,
        "ld_preload": ld_preload,
        "cyberpanel": cyberpanel,
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
    # Systemd units
    for u in scan_results.get("systemd", {}).get("units_found", []):
        unit = u.get("unit")
        if not unit:
            continue
        actions.append({
            "type": "systemd_unit",
            "target": unit,
            "risk": "medium",
            "reason": "Suspicious unit name detected",
            "command_preview": f"systemctl stop '{unit}' && systemctl disable '{unit}'",
        })
        unit_file = u.get("unit_file")
        if unit_file:
            actions.append({
                "type": "remove_unit_file",
                "target": unit_file,
                "risk": "medium",
                "reason": "Remove suspicious unit file and reload",
                "command_preview": f"rm -f '{unit_file}' && systemctl daemon-reload",
            })
    # Cron lines
    for entry in scan_results.get("cron", {}).get("suspicious_entries", []):
        file = entry.get("file")
        line_no = entry.get("line_no")
        matched = entry.get("matched")
        if file and line_no:
            actions.append({
                "type": "cron_line",
                "target": file,
                "pattern": matched,
                "risk": "medium",
                "reason": "Suspicious cron entry",
                "command_preview": f"sed -i.bak '{line_no}d' '{file}'",
            })
    # ld.so.preload
    if scan_results.get("ld_preload", {}).get("exists"):
        actions.append({
            "type": "remove_file",
            "target": "/etc/ld.so.preload",
            "risk": "high",
            "reason": "Unexpected ld.so.preload present",
            "command_preview": "rm -f '/etc/ld.so.preload'",
        })
    # SSH keys review
    for finding in scan_results.get("users", {}).get("ssh_findings", []):
        path = finding.get("path")
        if not path:
            continue
        actions.append({
            "type": "review_ssh_keys",
            "target": path,
            "risk": "low",
            "reason": "Manual review of authorized_keys recommended",
            "command_preview": f"ls -l '{path}' && sed -n '1,20p' '{path}'",
        })
    plan = {"total_actions": len(actions), "dry_run": True, "actions": actions}
    return {"success": True, "plan": plan}

__all__ = ["scan_server", "propose_remediation"]

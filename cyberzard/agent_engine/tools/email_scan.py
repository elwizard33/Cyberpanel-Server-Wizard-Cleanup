from __future__ import annotations
"""Email stack scanning & hardening plan generation.

Lightweight, read-only collection of CyberPanel email subsystem posture:
- Service status (postfix, dovecot, mailscanner, cpecs)
- Queue size & backlog flag
- SASL auth failure aggregation (IPs + /24)
- DNS mismatch detection for mail.<domain>
- RainLoop domain config host/IP check
- Fail2Ban status (postfix-sasl jail)
- TLS & rate limiting posture (postconf -n)
- Dovecot brute force mitigation directives
- Firewall heuristic (ufw status)
- Tail of mail log (truncated)

Produces summary flags used by higher-level commands.
All subprocess calls are bounded with short timeouts and failure-safe.

NOTE: This module does NOT execute any changes – only observation & plan proposal.
"""

from typing import Dict, Any, List, Tuple, Optional
import subprocess, shutil, os, socket, re, time, json, pathlib

MAIL_LOG_CANDIDATES = [
    "/var/log/mail.log",
    "/var/log/maillog",
]
SERVICES = ["postfix", "dovecot", "mailscanner", "cpecs"]
POSTFIX_RATE_PARAMS = [
    "smtpd_client_connection_count_limit",
    "smtpd_client_connection_rate_limit",
    "anvil_rate_time_unit",
]
POSTFIX_TLS_PARAMS = [
    "smtpd_tls_protocols",
    "smtp_tls_protocols",
    "smtpd_tls_ciphers",
]
DOVECOT_AUTH_FILE = "/etc/dovecot/conf.d/10-auth.conf"
RAINLOOP_GLOB = "/home/*webmail*/public_html/data/_data_/_default_/domains/*.ini"

SASL_FAIL_RE = re.compile(r"SASL (PLAIN|LOGIN) authentication failed", re.IGNORECASE)
IP_RE = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")

# ---------------- Utility helpers -----------------

def _run(cmd: List[str], timeout: int = 3) -> Tuple[int, str, str]:
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return cp.returncode, cp.stdout, cp.stderr
    except Exception as e:  # pragma: no cover - defensive
        return 127, "", str(e)


def _service_status(names: List[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    systemctl = shutil.which("systemctl")
    for n in names:
        status = "unknown"
        rc = 0
        if systemctl:
            rc, so, se = _run([systemctl, "is-active", n])
            raw = (so or se).strip()
            if raw:
                status = raw
            else:
                status = "unknown"
        out[n] = {"status": status, "active": status == "active"}
    return out


def _queue_size() -> Dict[str, Any]:
    postqueue = shutil.which("postqueue")
    if not postqueue:
        return {"available": False, "size": None}
    rc, so, se = _run([postqueue, "-p"], timeout=6)
    if rc != 0:
        return {"available": True, "size": None, "error": se.strip() or so[:200]}
    # Count non-header lines (postqueue -p output lines -> each message starts with queue id followed by space)
    lines = [l for l in so.splitlines() if l and re.match(r"^[A-F0-9]{5,}\s", l)]
    return {"available": True, "size": len(lines)}


def _tail_mail_log(limit: int) -> Tuple[str, str]:
    path_used = ""
    for p in MAIL_LOG_CANDIDATES:
        if os.path.exists(p):
            path_used = p
            break
    if not path_used:
        return "", ""
    try:
        with open(path_used, "r", encoding="utf-8", errors="ignore") as fh:
            try:
                fh.seek(0, os.SEEK_END)
                size = fh.tell()
                # naive tail: read last ~200k max
                read_back = 200_000
                pos = max(0, size - read_back)
                fh.seek(pos)
                data = fh.read()
            except Exception:
                fh.seek(0)
                data = fh.read()
        lines = data.splitlines()[-limit:]
        text = "\n".join(lines)
        if len(text) > 64_000:
            text = text[-64_000:]
        return text, path_used
    except Exception:
        return "", path_used


def _parse_sasl_failures(log_text: str) -> Dict[str, Any]:
    if not log_text:
        return {"count": 0, "by_ip": {}, "by_cidr24": {}, "top_ip": None, "top_cidr24": None}
    by_ip: Dict[str, int] = {}
    for line in log_text.splitlines():
        if SASL_FAIL_RE.search(line):
            m = IP_RE.search(line)
            if m:
                ip = m.group(1)
                by_ip[ip] = by_ip.get(ip, 0) + 1
    by_cidr: Dict[str, int] = {}
    for ip, c in by_ip.items():
        parts = ip.split('.')
        if len(parts) == 4:
            cidr = '.'.join(parts[:3]) + '.0/24'
            by_cidr[cidr] = by_cidr.get(cidr, 0) + c
    top_ip = None
    if by_ip:
        top_ip = max(by_ip.items(), key=lambda x: x[1])[0]
    top_cidr = None
    if by_cidr:
        top_cidr = max(by_cidr.items(), key=lambda x: x[1])[0]
    return {
        "count": sum(by_ip.values()),
        "by_ip": by_ip,
        "by_cidr24": by_cidr,
        "top_ip": top_ip,
        "top_cidr24": top_cidr,
    }


def _dns_info(domain: Optional[str]) -> Dict[str, Any]:
    if not domain:
        return {"domain": None, "mail_host": None, "resolved_ip": None, "public_ip": None, "mismatch": False}
    mail_host = f"mail.{domain}"
    resolved_ip = None
    try:
        resolved_ip = socket.gethostbyname(mail_host)
    except Exception:
        pass
    public_ip = None
    curl = shutil.which("curl")
    if curl:
        rc, so, _ = _run([curl, "-4", "-s", "ifconfig.me"], timeout=4)
        if rc == 0:
            candidate = (so or "").strip().split()[0]
            if IP_RE.match(candidate):
                public_ip = candidate
    mismatch = False
    if resolved_ip and public_ip and resolved_ip != public_ip:
        mismatch = True
    return {"domain": domain, "mail_host": mail_host, "resolved_ip": resolved_ip, "public_ip": public_ip, "mismatch": mismatch}


def _rainloop_config(domain: Optional[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {"paths": [], "host_mismatch": False}
    if not domain:
        return result
    import glob
    for path in glob.glob(RAINLOOP_GLOB):
        try:
            txt = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        result["paths"].append(path)
        # simple heuristic: if file references original domain but not current public IP we flag mismatch later at higher layer
        # Here just capture host lines
        # optionally parse host = value
        m = re.search(r"host\s*=\s*(.+)", txt)
        if m:
            host_val = m.group(1).strip()
            result.setdefault("hosts", []).append(host_val)
    return result


def _fail2ban_status() -> Dict[str, Any]:
    cli = shutil.which("fail2ban-client")
    if not cli:
        return {"available": False, "postfix_sasl": None}
    rc, so, se = _run([cli, "status", "postfix-sasl"], timeout=5)
    if rc != 0:
        return {"available": True, "postfix_sasl": None, "error": (se or so)[:200]}
    banned = None
    m = re.search(r"Banned IP list:\s*(.*)", so)
    if m:
        ips = [x for x in m.group(1).strip().split() if x]
        banned = len(ips)
    return {"available": True, "postfix_sasl": {"raw": so[:5000], "banned_count": banned}}


def _postfix_conf() -> Dict[str, str]:
    postconf = shutil.which("postconf")
    if not postconf:
        return {}
    rc, so, se = _run([postconf, "-n"], timeout=5)
    if rc != 0:
        return {}
    conf: Dict[str, str] = {}
    for line in so.splitlines():
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        conf[k.strip()] = v.strip()
    return conf


def _tls_posture(conf: Dict[str, str]) -> Dict[str, Any]:
    tls_ok = True
    detail: Dict[str, Any] = {}
    # Expect protocols exclude SSLv2/3 and ciphers high
    for p in POSTFIX_TLS_PARAMS:
        val = conf.get(p)
        detail[p] = val
    proto_ok = False
    for key in ["smtpd_tls_protocols", "smtp_tls_protocols"]:
        val = conf.get(key, "")
        if val and "SSLv2" not in val and "SSLv3" not in val:
            proto_ok = True
    cipher_ok = False
    c = conf.get("smtpd_tls_ciphers", "")
    if c and ("high" in c.lower() or "HIGH" in c):
        cipher_ok = True
    tls_ok = proto_ok and cipher_ok
    return {"hardened": tls_ok, "detail": detail}


def _rate_limit_posture(conf: Dict[str, str]) -> Dict[str, Any]:
    values = {k: conf.get(k) for k in POSTFIX_RATE_PARAMS}
    count_ok = False
    rate_ok = False
    unit_ok = False
    try:
        c = int(values.get("smtpd_client_connection_count_limit") or 0)
        if c and c <= 10:
            count_ok = True
    except Exception:
        pass
    try:
        r = int(values.get("smtpd_client_connection_rate_limit") or 0)
        if r and r <= 30:
            rate_ok = True
    except Exception:
        pass
    unit = values.get("anvil_rate_time_unit") or ""
    if unit.strip() in {"60s", "1m"}:
        unit_ok = True
    limited = count_ok and rate_ok and unit_ok
    return {"limited": limited, "values": values}


def _dovecot_posture() -> Dict[str, Any]:
    try:
        if not os.path.exists(DOVECOT_AUTH_FILE):
            return {"present": False, "hints": []}
        txt = pathlib.Path(DOVECOT_AUTH_FILE).read_text(encoding="utf-8", errors="ignore")
        hints = []
        if re.search(r"auth_failure_delay\s*=\s*\d", txt):
            hints.append("auth_failure_delay")
        if re.search(r"auth_cache_negative_ttl", txt):
            hints.append("auth_cache_negative_ttl")
        return {"present": True, "hints": hints}
    except Exception:
        return {"present": False, "hints": []}


def _firewall_posture() -> Dict[str, Any]:
    ufw = shutil.which("ufw")
    if not ufw:
        return {"available": False}
    rc, so, se = _run([ufw, "status"], timeout=4)
    if rc != 0:
        return {"available": True, "error": (se or so)[:120]}
    enabled = "Status: active" in so
    return {"available": True, "enabled": enabled, "raw": so[:4000]}

# ---------------- Main scan & plan -----------------

def scan_email_system(domain: Optional[str] = None, log_lines: int = 2000) -> Dict[str, Any]:
    services = _service_status(SERVICES)
    queue = _queue_size()
    log_text, log_path = _tail_mail_log(log_lines)
    sasl = _parse_sasl_failures(log_text)
    dns = _dns_info(domain)
    rainloop = _rainloop_config(domain)
    fail2ban = _fail2ban_status()
    conf = _postfix_conf()
    tls = _tls_posture(conf)
    rate_limits = _rate_limit_posture(conf)
    dovecot = _dovecot_posture()
    firewall = _firewall_posture()

    failed_services = [n for n, st in services.items() if not st.get("active")]
    brute_force = sasl.get("count", 0) > 20  # heuristic threshold
    summary = {
        "failed_services_count": len(failed_services),
        "failed_services": failed_services,
        "queue_size": queue.get("size"),
        "queue_backlog": (queue.get("size") or 0) > 500,
        "sasl_failures": sasl.get("count", 0),
        "top_attack_ip": sasl.get("top_ip"),
        "top_attack_cidr": sasl.get("top_cidr24"),
        "brute_force_detected": brute_force,
        "dns_mismatch": bool(dns.get("mismatch")),
        "fail2ban_active": bool(fail2ban.get("available") and fail2ban.get("postfix_sasl")),
        "tls_hardened": bool(tls.get("hardened")),
        "rate_limited": bool(rate_limits.get("limited")),
        "dovecot_hardening_present": bool(dovecot.get("hints")),
        "firewall_present": bool(firewall.get("available")),
    }

    return {
        "success": True,
        "summary": summary,
        "services": services,
        "queue": queue,
        "sasl": sasl,
        "dns": dns,
        "rainloop": rainloop,
        "fail2ban": fail2ban,
        "tls": tls,
        "rate_limits": rate_limits,
        "dovecot": dovecot,
        "firewall": firewall,
        "log_excerpt": log_text[:64000],
        "log_path": log_path,
    }

# Hardening / repair plan -------------------------------------------------

def propose_email_hardening(scan: Dict[str, Any]) -> Dict[str, Any]:
    summary = scan.get("summary", {}) if isinstance(scan, dict) else {}
    actions: List[Dict[str, Any]] = []

    def add(type_: str, category: str, risk: str, reason: str, cmd: str):
        actions.append({
            "type": type_,
            "category": category,
            "risk": risk,
            "reason": reason,
            "command_preview": cmd,
        })

    failed_services: List[str] = summary.get("failed_services", []) or []
    for svc in failed_services:
        add("service_restart", "service_recovery", "low", f"Service {svc} inactive", f"systemctl restart {svc}")

    if summary.get("queue_backlog"):
        add("queue_clear", "queue", "low", "Large queue backlog", "postqueue -p && postsuper -d ALL")

    if summary.get("dns_mismatch"):
        add("dns_rainloop_fix", "dns_config", "low", "mail.<domain> DNS mismatch", "sed -i 's/mail.\\<domain>/$(curl -s ifconfig.me)/g' /home/*webmail*/public_html/data/_data_/_default_/domains/*.ini")

    sasl_failures = summary.get("sasl_failures", 0)
    if sasl_failures > 20:
        if not summary.get("rate_limited"):
            add("postfix_rate_limit", "rate_limit", "medium", "No Postfix rate limiting", "postconf -e 'smtpd_client_connection_count_limit=10' 'smtpd_client_connection_rate_limit=30' 'anvil_rate_time_unit=60s' && systemctl reload postfix")
        if not summary.get("fail2ban_active"):
            add("fail2ban_install", "fail2ban", "medium", "Fail2Ban not active", "apt-get update && apt-get install -y fail2ban")
            add("fail2ban_config", "fail2ban", "medium", "Add postfix-sasl jail", "tee /etc/fail2ban/jail.d/postfix.conf >/dev/null <<'EOF'\n[postfix-sasl]\nenabled=true\nport=smtp,465,587\nfilter=postfix-sasl\nlogpath=/var/log/mail.log\nmaxretry=3\nbantime=3600\nfindtime=600\nEOF\n&& systemctl restart fail2ban")
    top_cidr = summary.get("top_attack_cidr")
    if top_cidr:
        add("block_cidr", "ip_block", "medium", f"Block attacking subnet {top_cidr}", f"ufw deny from {top_cidr} || iptables -I INPUT -s {top_cidr.split('/')[0]}/24 -j DROP")

    if not summary.get("tls_hardened"):
        add("tls_hardening", "tls", "medium", "Weak or incomplete TLS posture", "postconf -e 'smtpd_tls_protocols=!SSLv2,!SSLv3' 'smtp_tls_protocols=!SSLv2,!SSLv3' 'smtpd_tls_ciphers=high' && systemctl reload postfix")

    if not summary.get("dovecot_hardening_present"):
        add(
            "dovecot_hardening",
            "dovecot",
            "medium",
            "Missing Dovecot brute force mitigations",
            "bash -lc 'echo \"auth_failure_delay = 2s\" >> /etc/dovecot/conf.d/10-auth.conf && systemctl restart dovecot'",
        )

    if not summary.get("firewall_present"):
        add("firewall_setup", "firewall", "medium", "Firewall tool (ufw) absent or inactive", "apt-get install -y ufw && ufw --force enable && ufw allow 22 25 80 443 587 993 995")

    # Monitoring + backups always recommended
    add("monitor_script", "monitoring", "low", "Add monitoring script", "tee /usr/local/bin/monitor-email-attacks.sh >/dev/null <<'EOF'\n#!/bin/bash\necho '=== Email Security Monitor ==='\nDate=$(date)\n...\nEOF\n&& chmod +x /usr/local/bin/monitor-email-attacks.sh")
    add("daily_health_cron", "monitoring", "low", "Daily health check cron", "tee /etc/cron.daily/email-health-check >/dev/null <<'EOF'\n#!/bin/bash\n# simplified health check\nEOF\n&& chmod +x /etc/cron.daily/email-health-check")

    plan = {"total_actions": len(actions), "dry_run": True, "actions": actions}
    return {"success": True, "plan": plan}

__all__ = ["scan_email_system", "propose_email_hardening"]

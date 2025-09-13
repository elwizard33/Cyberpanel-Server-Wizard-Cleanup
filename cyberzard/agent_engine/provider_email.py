from __future__ import annotations
"""Email-focused AI provider helpers with graceful static fallbacks.

Functions exported:
- summarize_email_security(scan_results, hardening_plan)
- generate_email_fix_guide(scan_results, hardening_plan)
- justify_email_action(action, scan_summary)
- refine_email_action(action, stdout, stderr, failure_reason, scan_summary)

Design mirrors provider.py pattern (OpenAI / Anthropic selection via
CYBERZARD_MODEL_PROVIDER env var). Failures always degrade to deterministic
static output; never raise outward.
"""
from typing import Any, Dict, Optional
import os, textwrap, json

MAX_JUSTIFICATION_LEN = 120

# ---------------- Static fallbacks -----------------

def _static_summary(scan: Dict[str, Any], plan: Optional[Dict[str, Any]]) -> str:
    s = scan.get("summary", {}) if isinstance(scan, dict) else {}
    lines = ["Email Security Posture (static)"]
    lines.append(f"Failed services: {s.get('failed_services_count',0)}")
    lines.append(f"Queue size: {s.get('queue_size')} backlog={bool(s.get('queue_backlog'))}")
    lines.append(f"SASL failures: {s.get('sasl_failures',0)} brute_force={bool(s.get('brute_force_detected'))}")
    lines.append(f"DNS mismatch: {bool(s.get('dns_mismatch'))}")
    lines.append(f"Fail2Ban active: {bool(s.get('fail2ban_active'))}")
    lines.append(f"TLS hardened: {bool(s.get('tls_hardened'))}; rate limited: {bool(s.get('rate_limited'))}")
    lines.append(f"Dovecot hardening: {bool(s.get('dovecot_hardening_present'))}")
    if plan:
        total = plan.get('plan', {}).get('total_actions') if isinstance(plan, dict) else None
        lines.append(f"Planned actions: {total}")
    return "\n".join(lines[:12])


def _static_fix_guide(scan: Dict[str, Any], plan: Optional[Dict[str, Any]]) -> str:
    s = scan.get("summary", {}) if isinstance(scan, dict) else {}
    backlog = s.get('queue_backlog')
    brute = s.get('brute_force_detected')
    dns = s.get('dns_mismatch')
    tls = s.get('tls_hardened')
    lines = []
    lines.append("# Email Fix & Hardening Guide (Static)")
    lines.append("\n## Overview")
    lines.append("This guide summarizes detected issues and recommended hardening steps.")
    lines.append("\n## Detected Issues")
    issues = []
    if s.get('failed_services_count'): issues.append("One or more services inactive")
    if backlog: issues.append("Large mail queue backlog")
    if brute: issues.append("High SASL failure volume / brute force pattern")
    if dns: issues.append("mail.<domain> DNS mismatch vs server IP")
    if not tls: issues.append("TLS posture incomplete")
    if not s.get('rate_limited'): issues.append("Postfix rate limiting absent")
    if not s.get('fail2ban_active'): issues.append("Fail2Ban not active")
    if not s.get('dovecot_hardening_present'): issues.append("Dovecot brute force mitigations missing")
    lines.extend([f"- {i}" for i in issues] or ["- No critical issues detected"])
    lines.append("\n## Recommended Fix Sequence")
    seq = []
    if s.get('failed_services_count'): seq.append("Restart failed services (postfix/dovecot/mailscanner/cpecs)")
    if backlog: seq.append("Inspect & clear backlog with postqueue/postsupper")
    if dns: seq.append("Update RainLoop domain config host -> correct server IP")
    if brute and not s.get('rate_limited'): seq.append("Apply Postfix connection rate limiting")
    if brute and not s.get('fail2ban_active'): seq.append("Install & configure Fail2Ban postfix-sasl jail")
    if not tls: seq.append("Harden TLS (disable SSLv2/3, enforce high ciphers)")
    if not s.get('dovecot_hardening_present'): seq.append("Add auth_failure_delay to Dovecot auth config")
    seq.append("Add monitoring script & daily health cron")
    lines.extend([f"1. {step}" for step in seq])
    lines.append("\n## Hardening Actions")
    if plan and isinstance(plan, dict):
        actions = plan.get('plan', {}).get('actions', [])
        for a in actions[:25]:
            lines.append(f"- [{a.get('risk','?')}] {a.get('type')}: {a.get('reason')}")
    lines.append("\n## Verification")
    lines.append("Re-run 'cyberzard email-security --json' after applying steps to confirm improvements.")
    return "\n".join(lines)

# ---------------- Provider selection -----------------

def _provider_name() -> str:
    return (os.getenv("CYBERZARD_MODEL_PROVIDER") or "none").lower().strip()


def _openai_client():  # pragma: no cover - optional
    try:
        from openai import OpenAI  # type: ignore
    except Exception:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        return OpenAI()
    except Exception:
        return None


def _anthropic_client():  # pragma: no cover - optional
    try:
        import anthropic  # type: ignore
    except Exception:
        return None
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        return anthropic.Anthropic()
    except Exception:
        return None

# --------------- Public functions --------------------

def summarize_email_security(scan_results: Dict[str, Any], hardening_plan: Optional[Dict[str, Any]]) -> str:
    provider = _provider_name()
    if provider not in {"openai", "anthropic"}:
        return _static_summary(scan_results, hardening_plan)
    s = scan_results.get("summary", {}) if isinstance(scan_results, dict) else {}
    compact = {
        "failed_services": s.get("failed_services_count"),
        "queue": s.get("queue_size"),
        "backlog": bool(s.get("queue_backlog")),
        "sasl": s.get("sasl_failures"),
        "dns_mismatch": bool(s.get("dns_mismatch")),
        "fail2ban": bool(s.get("fail2ban_active")),
        "tls_hardened": bool(s.get("tls_hardened")),
        "rate_limited": bool(s.get("rate_limited")),
        "dovecot_hardening": bool(s.get("dovecot_hardening_present")),
    }
    instruction = (
        "Provide up to 10 short bullet lines prioritizing email service recovery, anti-abuse, and security \n"
        "Focus on deterministic, CLI-applicable steps only."
    )
    try:
        if provider == "openai":
            client = _openai_client()
            if not client:
                return _static_summary(scan_results, hardening_plan)
            prompt = f"{instruction}\nContext: {json.dumps(compact)}"
            resp = client.chat.completions.create(  # type: ignore
                model=os.getenv("CYBERZARD_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=220,
            )
            text = resp.choices[0].message.content  # type: ignore[attr-defined]
            return text or _static_summary(scan_results, hardening_plan)
        if provider == "anthropic":
            client = _anthropic_client()
            if not client:
                return _static_summary(scan_results, hardening_plan)
            prompt = f"{instruction}\nContext: {json.dumps(compact)}"
            msg = client.messages.create(  # type: ignore
                model=os.getenv("CYBERZARD_MODEL", "claude-3-5-sonnet-latest"),
                max_tokens=220,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = getattr(msg, "content", [])
            text = " ".join(getattr(p, "text", "") for p in parts).strip()
            return text or _static_summary(scan_results, hardening_plan)
    except Exception:
        return _static_summary(scan_results, hardening_plan)
    return _static_summary(scan_results, hardening_plan)


def generate_email_fix_guide(scan_results: Dict[str, Any], hardening_plan: Optional[Dict[str, Any]]) -> str:
    provider = _provider_name()
    if provider not in {"openai", "anthropic"}:
        return _static_fix_guide(scan_results, hardening_plan)
    s = scan_results.get("summary", {}) if isinstance(scan_results, dict) else {}
    compact = {k: s.get(k) for k in [
        "failed_services_count","queue_size","queue_backlog","sasl_failures","dns_mismatch","fail2ban_active","tls_hardened","rate_limited","dovecot_hardening_present"
    ]}
    plan_actions = []
    if hardening_plan and isinstance(hardening_plan, dict):
        plan_actions = hardening_plan.get("plan", {}).get("actions", [])[:20]
    plan_preview = [
        {"type": a.get("type"), "risk": a.get("risk"), "category": a.get("category")} for a in plan_actions
    ]
    instruction = textwrap.dedent(
        """
        Produce a concise markdown incident+hardening guide for the CyberPanel email stack.
        Sections: Overview, Detected Issues, Step-by-Step Recovery, Security Hardening, Verification.
        Emphasize deterministic Linux CLI commands (no remote downloads except apt-get / distro packages).
        Keep each command on a single line. Avoid speculative actions. Base strictly on provided context.
        Limit total length to ~1000 tokens.
        """.strip()
    )
    try:
        if provider == "openai":
            client = _openai_client()
            if not client:
                return _static_fix_guide(scan_results, hardening_plan)
            prompt = json.dumps({"instruction": instruction, "context": compact, "plan_preview": plan_preview})
            resp = client.chat.completions.create(  # type: ignore
                model=os.getenv("CYBERZARD_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=1200,
            )
            text = resp.choices[0].message.content  # type: ignore[attr-defined]
            if text and "Overview" in text:
                return text
            return _static_fix_guide(scan_results, hardening_plan)
        if provider == "anthropic":
            client = _anthropic_client()
            if not client:
                return _static_fix_guide(scan_results, hardening_plan)
            prompt = json.dumps({"instruction": instruction, "context": compact, "plan_preview": plan_preview})
            msg = client.messages.create(  # type: ignore
                model=os.getenv("CYBERZARD_MODEL", "claude-3-5-sonnet-latest"),
                max_tokens=1200,
                temperature=0.25,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = getattr(msg, "content", [])
            text = " ".join(getattr(p, "text", "") for p in parts)
            if text and "Overview" in text:
                return text
            return _static_fix_guide(scan_results, hardening_plan)
    except Exception:
        return _static_fix_guide(scan_results, hardening_plan)
    return _static_fix_guide(scan_results, hardening_plan)


def justify_email_action(action: Dict[str, Any], scan_summary: Dict[str, Any]) -> str:
    """Return a one-line justification for an email hardening/remediation action.
    Falls back to deterministic static explanation when provider disabled.
    """
    provider = _provider_name()
    base = f"{action.get('type')} ({action.get('risk')}): {action.get('reason')}"
    if len(base) > MAX_JUSTIFICATION_LEN:
        base = base[:MAX_JUSTIFICATION_LEN-3] + '...'
    if provider not in {"openai", "anthropic"}:
        return base
    try:
        compact = {
            "queue_backlog": scan_summary.get("queue_backlog"),
            "sasl_failures": scan_summary.get("sasl_failures"),
            "dns_mismatch": scan_summary.get("dns_mismatch"),
            "tls_hardened": scan_summary.get("tls_hardened"),
            "rate_limited": scan_summary.get("rate_limited"),
        }
        instruction = (
            "One line (<=120 chars) justification for executing this email security action in a CyberPanel context. "
            "No extra commentary."
        )
        if provider == "openai":
            client = _openai_client()
            if not client:
                return base
            prompt = f"{instruction}\nAction: {action.get('type')} risk={action.get('risk')} reason={action.get('reason')}\nContext: {compact}"
            resp = client.chat.completions.create(  # type: ignore
                model=os.getenv("CYBERZARD_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=80,
            )
            text = (resp.choices[0].message.content or "").strip()  # type: ignore[attr-defined]
            if text:
                if len(text) > MAX_JUSTIFICATION_LEN:
                    text = text[:MAX_JUSTIFICATION_LEN-3] + '...'
                return text
            return base
        if provider == "anthropic":
            client = _anthropic_client()
            if not client:
                return base
            prompt = f"{instruction}\nAction: {action.get('type')} risk={action.get('risk')} reason={action.get('reason')}\nContext: {compact}"
            msg = client.messages.create(  # type: ignore
                model=os.getenv("CYBERZARD_MODEL", "claude-3-5-sonnet-latest"),
                max_tokens=80,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = getattr(msg, "content", [])
            text = " ".join(getattr(p, "text", "") for p in parts).strip()
            if text:
                if len(text) > MAX_JUSTIFICATION_LEN:
                    text = text[:MAX_JUSTIFICATION_LEN-3] + '...'
                return text
            return base
    except Exception:
        return base
    return base


def refine_email_action(action: Dict[str, Any], stdout: str, stderr: str, failure_reason: str, scan_summary: Dict[str, Any]) -> Optional[str]:
    """Attempt to refine a failed command. Returns new one-line command or None.

    Safety: Only suggests a new command when provider enabled; otherwise None.
    The caller must still subject the refined command to safety validation.
    """
    provider = _provider_name()
    if provider not in {"openai", "anthropic"}:
        return None
    # If stderr empty, nothing to refine
    if not (stderr or failure_reason):
        return None
    compact = {k: scan_summary.get(k) for k in ["queue_backlog","sasl_failures","dns_mismatch","tls_hardened","rate_limited"]}
    instruction = (
        "Suggest a corrected SINGLE shell command (no explanation, no backticks) for this email security action. "
        "Must be one line. Keep same intent."
    )
    try:
        if provider == "openai":
            client = _openai_client()
            if not client:
                return None
            prompt = (
                f"{instruction}\nActionType={action.get('type')}\nOriginal={action.get('command_preview')}\n"
                f"FailureReason={failure_reason}\nSTDERR={stderr[:400]}\nContext={compact}"
            )
            resp = client.chat.completions.create(  # type: ignore
                model=os.getenv("CYBERZARD_MODEL", "gpt-4o-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=120,
            )
            text = (resp.choices[0].message.content or "").strip()  # type: ignore[attr-defined]
            if text and "\n" in text:
                text = text.splitlines()[0].strip()
            return text or None
        if provider == "anthropic":
            client = _anthropic_client()
            if not client:
                return None
            prompt = json.dumps({
                "instruction": instruction,
                "action": action.get('type'),
                "original": action.get('command_preview'),
                "failure": failure_reason,
                "stderr": stderr[:400],
                "context": compact,
            })
            msg = client.messages.create(  # type: ignore
                model=os.getenv("CYBERZARD_MODEL", "claude-3-5-sonnet-latest"),
                max_tokens=120,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = getattr(msg, "content", [])
            text = " ".join(getattr(p, "text", "") for p in parts).strip()
            if text and "\n" in text:
                text = text.splitlines()[0].strip()
            return text or None
    except Exception:
        return None
    return None

__all__ = [
    "summarize_email_security",
    "generate_email_fix_guide",
    "justify_email_action",
    "refine_email_action",
]

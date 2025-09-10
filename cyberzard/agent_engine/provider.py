from __future__ import annotations

import os
from typing import Any, Dict


def _static_summary(scan_results: Dict[str, Any]) -> str:
    s = scan_results.get("summary", {})
    lines = []
    lines.append("Cyberzard Advice (static)")
    lines.append(f"- Malicious files: {s.get('malicious_file_count', 0)}")
    lines.append(f"- Suspicious process groups: {s.get('suspicious_process_groups', 0)}")
    lines.append(f"- Encrypted-like files: {s.get('encrypted_file_count', 0)}")
    lines.append(f"- Suspicious cron entries: {s.get('cron_suspicious_count', 0)}")
    lines.append(f"- Suspicious systemd units: {s.get('systemd_units_count', 0)}")
    lines.append(f"- Users: {s.get('users_count', 0)}; keys files: {s.get('ssh_keys_files', 0)}")
    lines.append(f"- ld.so.preload present: {bool(s.get('ld_preload_exists', False))}")
    lines.append(f"- CyberPanel key files present: {s.get('cyberpanel_files_present', 0)}")
    return "\n".join(lines[:8])


def summarize(scan_results: Dict[str, Any]) -> str:
    provider = (os.getenv("CYBERZARD_MODEL_PROVIDER") or "none").lower().strip()
    if provider not in {"openai", "anthropic"}:
        return _static_summary(scan_results)

    # Build a compact prompt payload
    s = scan_results.get("summary", {})
    compact = {
        "malicious": s.get("malicious_file_count", 0),
        "proc_groups": s.get("suspicious_process_groups", 0),
        "encrypted": s.get("encrypted_file_count", 0),
        "cron": s.get("cron_suspicious_count", 0),
        "systemd": s.get("systemd_units_count", 0),
        "users": s.get("users_count", 0),
        "keys_files": s.get("ssh_keys_files", 0),
        "ld_preload": bool(s.get("ld_preload_exists", False)),
        "cyberpanel_present": s.get("cyberpanel_files_present", 0),
    }
    instruction = (
        "Provide concise CyberPanel-focused incident triage advice (6-8 lines). "
        "Use deterministic actions, no remote downloads/executions."
    )

    try:
        if provider == "openai":
            import os as _os  # lazy import already done
            try:
                from openai import OpenAI  # type: ignore
            except Exception:
                return _static_summary(scan_results)
            if not _os.getenv("OPENAI_API_KEY"):
                return _static_summary(scan_results)
            client = OpenAI()
            prompt = (
                f"{instruction}\nSummary: {compact}\nRespond briefly."
            )
            try:
                # Using responses API for brevity; fallback as needed
                resp = client.chat.completions.create(
                    model=_os.getenv("CYBERZARD_MODEL", "gpt-4o-mini"),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=200,
                )
                text = resp.choices[0].message.content  # type: ignore[attr-defined]
                return text or _static_summary(scan_results)
            except Exception:
                return _static_summary(scan_results)
        elif provider == "anthropic":
            try:
                import anthropic  # type: ignore
            except Exception:
                return _static_summary(scan_results)
            if not os.getenv("ANTHROPIC_API_KEY"):
                return _static_summary(scan_results)
            client = anthropic.Anthropic()
            prompt = (
                f"{instruction}\nSummary: {compact}\nRespond briefly."
            )
            try:
                msg = client.messages.create(
                    model=os.getenv("CYBERZARD_MODEL", "claude-3-5-sonnet-latest"),
                    max_tokens=200,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}],
                )
                # Extract text from content
                parts = getattr(msg, "content", [])
                text = " ".join(getattr(p, "text", "") for p in parts)
                return text.strip() or _static_summary(scan_results)
            except Exception:
                return _static_summary(scan_results)
    except Exception:
        return _static_summary(scan_results)


__all__ = ["summarize"]


def justify_actions(actions, scan_results):
    """Optionally produce brief justifications per action using configured provider.

    Returns a list of strings with the same length as actions, or None when provider
    is not configured/available. Any failure results in None (graceful degrade).
    """
    try:
        provider = (os.getenv("CYBERZARD_MODEL_PROVIDER") or "none").lower().strip()
        if provider not in {"openai", "anthropic"}:
            return None
        # Build compact context once
        s = scan_results.get("summary", {}) if isinstance(scan_results, dict) else {}
        compact = {
            "malicious": s.get("malicious_file_count", 0),
            "proc_groups": s.get("suspicious_process_groups", 0),
            "encrypted": s.get("encrypted_file_count", 0),
            "cron": s.get("cron_suspicious_count", 0),
            "systemd": s.get("systemd_units_count", 0),
            "users": s.get("users_count", 0),
            "keys_files": s.get("ssh_keys_files", 0),
            "ld_preload": bool(s.get("ld_preload_exists", False)),
            "cyberpanel_present": s.get("cyberpanel_files_present", 0),
        }
        if provider == "openai":
            try:
                from openai import OpenAI  # type: ignore
            except Exception:
                return None
            if not os.getenv("OPENAI_API_KEY"):
                return None
            client = OpenAI()
            out: list[str] = []
            for a in actions or []:
                t = a.get("type"); tgt = a.get("target")
                prompt = (
                    "One-line justification (max 25 words) for verifying this remediation action in a CyberPanel context. "
                    "Be specific and cautious.\n"
                    f"Action: type={t} target={tgt}\nSummary: {compact}"
                )
                try:
                    resp = client.chat.completions.create(
                        model=os.getenv("CYBERZARD_MODEL", "gpt-4o-mini"),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=60,
                    )
                    text = resp.choices[0].message.content  # type: ignore[attr-defined]
                    out.append((text or "").strip())
                except Exception:
                    out.append("")
            return out
        if provider == "anthropic":
            try:
                import anthropic  # type: ignore
            except Exception:
                return None
            if not os.getenv("ANTHROPIC_API_KEY"):
                return None
            client = anthropic.Anthropic()
            out: list[str] = []
            for a in actions or []:
                t = a.get("type"); tgt = a.get("target")
                prompt = (
                    "One-line justification (max 25 words) for verifying this remediation action in a CyberPanel context. "
                    "Be specific and cautious.\n"
                    f"Action: type={t} target={tgt}\nSummary: {compact}"
                )
                try:
                    msg = client.messages.create(
                        model=os.getenv("CYBERZARD_MODEL", "claude-3-5-sonnet-latest"),
                        max_tokens=60,
                        temperature=0.2,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    parts = getattr(msg, "content", [])
                    text = " ".join(getattr(p, "text", "") for p in parts).strip()
                    out.append(text)
                except Exception:
                    out.append("")
            return out
        return None
    except Exception:
        return None


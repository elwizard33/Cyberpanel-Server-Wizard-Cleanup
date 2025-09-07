"""Static hardening & remediation advice generation.

Provides generate_advice(categories, ai_callback=None) which returns
unique guidance strings. Optional ai_callback(list[str]) -> list[str]
allows enrichment when an AI provider is available.
"""
from __future__ import annotations

from typing import Iterable, List, Callable, Set, Optional
import json

from cyberzard.core.provider_base import ProviderResponse, Provider
from cyberzard.providers.openai_provider import OpenAIProvider
from cyberzard.providers.anthropic_provider import AnthropicProvider
from cyberzard.config import get_settings

from cyberzard.config import Category

_STATIC_ADVICE = {
    Category.file: [
        "Quarantine suspicious binaries and compute cryptographic hashes before deletion.",
        "Ensure file integrity monitoring (e.g., AIDE) is deployed for critical paths.",
    ],
    Category.process: [
        "Terminate unauthorized miner processes; collect memory sample if needed for forensics.",
        "Harden process accounting (enable auditd / enhanced logging).",
    ],
    Category.service: [
        "Disable and mask rogue systemd services after capturing unit file evidence.",
        "Restrict creation of new services to privileged automation workflows.",
    ],
    Category.cron: [
        "Audit user crontabs for unexpected downloaders or encoded payload fetch lines.",
        "Implement cron allow/deny lists and version control critical cron files.",
    ],
    Category.user: [
        "Rotate credentials for unexpected or anomalous privileged accounts.",
        "Enforce MFA / key-based authentication; disable password login where possible.",
    ],
    Category.ssh_key: [
        "Prune unused or unknown SSH public keys; enforce key provenance documentation.",
        "Deploy SSH CA signing or centralized key management for traceability.",
    ],
    Category.encryption: [
        "Investigate encrypted/locked files; confirm if ransomware staging or legitimate backup encryption.",
        "Maintain offline backups and test restoration procedures regularly.",
    ],
    Category.composite: [
        "Perform full incident response workflow (triage, containment, eradication, recovery).",
        "Hunt for lateral movement indicators across adjacent infrastructure.",
    ],
}


def _make_provider(name: str) -> Optional[Provider]:  # pragma: no cover - thin wrapper
    if name == "openai":
        return OpenAIProvider()
    if name == "anthropic":
        return AnthropicProvider()
    return None


def _enrich_with_provider(base_tips: List[str]) -> List[str]:
    settings = get_settings()
    prov = _make_provider(settings.model_provider)
    if not prov:
        return []
    # Truncate context size
    joined = "\n".join(base_tips)
    if len(joined) > 2000:
        joined = joined[:2000]
    messages = [
        {"role": "system", "content": "You add concise, actionable, security-hardening advice. Avoid duplication."},
        {"role": "user", "content": f"Existing advice list (may be truncated):\n{joined}\nAdd 2-4 high-impact additional recommendations."},
    ]
    try:
        resp: ProviderResponse = prov.generate(messages, tools_schema=None, max_tokens=280)
        text = resp.content.strip()
        if not text:
            return []
        # Split lines, basic bullet cleanup
        tips: List[str] = []
        for line in text.splitlines():
            line = line.strip(" -*#")
            if not line:
                continue
            if len(line) > 300:
                line = line[:300] + "…"
            tips.append(line)
            if len(tips) >= 6:
                break
        return tips
    except Exception:  # network or SDK failure; soft fail
        return []


def generate_advice(categories: Iterable[Category], ai_callback: Callable[[List[str]], List[str]] | None = None, enable_ai: bool = True) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for cat in categories:
        for tip in _STATIC_ADVICE.get(cat, []):
            if tip not in seen:
                seen.add(tip)
                out.append(tip)
    if ai_callback and out:
        try:
            enriched = ai_callback(out)
            if enriched:
                for tip in enriched:
                    if tip and tip not in seen:
                        seen.add(tip)
                        out.append(tip)
        except Exception:
            # Fail soft; keep static advice
            pass
    elif enable_ai and out:
        # Internal provider-based enrichment path
        extra = _enrich_with_provider(out)
        for tip in extra:
            if tip and tip not in seen:
                seen.add(tip)
                out.append(tip)
    return out

__all__ = ["generate_advice"]

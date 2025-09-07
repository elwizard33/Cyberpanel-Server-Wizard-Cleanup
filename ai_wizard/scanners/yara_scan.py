"""Optional YARA scanner.

Attempts to import python-yara. If unavailable or rules directory not
configured, returns empty list quickly. Environment variable:
  CYBERZARD_YARA_RULES_DIR - directory containing .yar/.yara files.

Each matching rule emits a Finding with severity derived from rule meta
`severity` (critical|high|medium|low) default medium.
"""
from __future__ import annotations

from pathlib import Path
from typing import List
import os

from cyberzard.scanners.base import BaseScanner, ScanContext, register
from cyberzard.core.models import Finding
from cyberzard.config import Category, Severity, RecommendedAction

try:  # pragma: no cover - import side path
    import yara  # type: ignore
except Exception:  # pragma: no cover
    yara = None  # type: ignore


@register
class YaraScanner(BaseScanner):
    name = "yara_rules"
    description = "Scan suspicious files using YARA rules if available"

    def scan(self, context: ScanContext) -> List[Finding]:
        rules_dir = os.getenv("CYBERZARD_YARA_RULES_DIR")
        if not yara or not rules_dir:
            return []
        root = Path(rules_dir)
        if not root.exists() or not root.is_dir():
            return []
        # Collect rule file paths
        paths = [p for p in root.rglob("*") if p.suffix.lower() in {".yar", ".yara"}]
        if not paths:
            return []
        matches: List[Finding] = []
        try:
            # Compile multi-file set
            namespace_map = {f"r{i}": str(p) for i, p in enumerate(paths)}
            compiled = yara.compile(filepaths=namespace_map)  # type: ignore[attr-defined]
        except Exception:
            return []
        # Candidate file list: if prior file findings exist, restrict to those paths; else skip heavy traversal
        prior = context.cache.get("prior_findings")
        candidate_paths = []
        if isinstance(prior, list):
            for f in prior:
                if getattr(f, "path", None):
                    candidate_paths.append(getattr(f, "path"))
        # Deduplicate
        seen_paths = set()
        pruned = []
        for p in candidate_paths:
            if p and p not in seen_paths:
                seen_paths.add(p)
                pruned.append(p)
        for path in pruned[:200]:  # cap for safety
            try:
                data = Path(path).read_bytes()
            except Exception:
                continue
            try:
                res = compiled.match(data=data)
            except Exception:
                continue
            for r in res:
                try:
                    meta = getattr(r, "meta", {})
                    sev_str = str(meta.get("severity", "medium")).lower()
                    sev = Severity.medium
                    if sev_str in {"critical", "high", "medium", "low", "info"}:
                        sev = Severity(sev_str if sev_str != "critical" else "critical") if sev_str != "info" else Severity.low
                    fid = f"yara:{r.rule}:{Path(path).name}"
                    rationale = f"YARA rule '{r.rule}' matched file {path}" + (f" (tags: {','.join(r.tags)})" if getattr(r, 'tags', None) else "")
                    matches.append(
                        Finding(
                            id=fid,
                            indicator=r.rule,
                            category=Category.file,
                            severity=sev,
                            rationale=rationale,
                            recommended_action=RecommendedAction.investigate,
                            path=Path(path),
                        )
                    )
                except Exception:
                    continue
        return matches

__all__ = ["YaraScanner"]
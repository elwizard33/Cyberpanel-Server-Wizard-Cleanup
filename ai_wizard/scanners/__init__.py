"""Scanner orchestration utilities."""

from __future__ import annotations

from typing import List, Dict, Tuple, DefaultDict
from collections import defaultdict

from cyberzard.config import PROCESS_PATTERNS

from cyberzard.core.models import Finding
from cyberzard.severity import classify, weight
from cyberzard.scanners.base import get_scanner_classes, ScanContext


def run_all_scanners() -> List[Finding]:
	"""Run all registered scanners, de-duplicate findings, and return list.

	De-duplication key strategy:
	  - process: (category, pid)
	  - file / encryption / cron / service / ssh_key: (category, path or indicator)
	  - composite: always unique by id
	"""
	context = ScanContext()
	all_findings: List[Finding] = []
	# First pass: run non-composite scanners
	for cls in get_scanner_classes():
		if cls.name == "kinsing_family":
			continue
		scanner = cls()
		findings = scanner.scan(context)
		all_findings.extend(findings)

	# Cache prior findings for composite scanners
	context.cache["prior_findings"] = list(all_findings)

	# Second pass: composite scanners
	for cls in get_scanner_classes():
		if cls.name != "kinsing_family":
			continue
		scanner = cls()
		comp = scanner.scan(context)
		all_findings.extend(comp)

	dedup: Dict[Tuple[str, str], Finding] = {}
	for f in all_findings:
		if f.category.name == "composite":
			# Keep composite as-is; use id as unique key
			dedup[(f.category.value, f.id)] = f
			continue
		if f.category.name == "process" and f.pid is not None:
			key = (f.category.value, str(f.pid))
		elif f.path:
			key = (f.category.value, str(f.path))
		else:
			key = (f.category.value, f.indicator)
		# Fill missing severity with classifier fallback (rare)
		if not f.severity:
			f.severity = classify(f.indicator)
		existing = dedup.get(key)
		if existing is None:
			dedup[key] = f
		else:
			# Choose higher weighted severity; if tie keep earlier (stable)
			if weight(f.severity) > weight(existing.severity):
				dedup[key] = f

	# Convert dedup dict to list for correlation
	base_results = list(dedup.values())

	# Correlation pass: build token occurrence map across categories
	token_map: DefaultDict[str, Dict[str, List[Finding]]] = defaultdict(lambda: defaultdict(list))
	# Candidate tokens: process patterns (lowercased) + basenames of file findings
	proc_tokens = {p.lower(): p for p in PROCESS_PATTERNS}
	for f in base_results:
		indicators: List[str] = []
		if f.category.name == "process" and f.indicator:
			indicators.append(f.indicator.lower())
		if f.path and f.path.name:
			indicators.append(f.path.name.lower())
		for tok in indicators:
			for pattern in proc_tokens.keys():
				if pattern in tok:
					token_map[pattern][f.category.value].append(f)
	# Create composite findings where token spans >=2 distinct categories
	composite_findings: List[Finding] = []
	for token, cat_map in token_map.items():
		if len(cat_map) < 2:
			continue
		# Determine elevated severity: high if any high/critical else medium
		sev_rank = 0
		for cat_list in cat_map.values():
			for f in cat_list:
				sev_rank = max(sev_rank, weight(f.severity))
		from cyberzard.config import Severity, Category, RecommendedAction  # local import to avoid cycle
		if sev_rank >= weight(Severity.high):
			sev = Severity.high
		elif sev_rank >= weight(Severity.medium):
			sev = Severity.medium
		else:
			sev = Severity.medium
		fid = f"composite:{token}"
		rationale = f"Multiple indicators referencing token '{token}' across categories: {', '.join(sorted(cat_map.keys()))}."
		comp = Finding(
			id=fid,
			indicator=token,
			category=Category.composite,
			severity=sev,
			rationale=rationale,
			recommended_action=RecommendedAction.investigate,
		)
		# Avoid duplicate composite id if already exists
		if not any(cf.id == fid for cf in base_results) and not any(cf.id == fid for cf in composite_findings):
			composite_findings.append(comp)

	result = base_results + composite_findings
	# Final ordering
	result.sort(key=lambda x: (weight(x.severity), x.timestamp, x.id))
	result.reverse()
	return result


__all__ = ["run_all_scanners"]

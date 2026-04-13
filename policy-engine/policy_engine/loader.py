from __future__ import annotations

from pathlib import Path
from typing import Any

from .output_validator import DEFAULT_RULE_PATH, load_rule_catalog


def load_enabled_policy_rules(
    path: Path | None = None,
    *,
    stages: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    catalog = load_rule_catalog(path or DEFAULT_RULE_PATH)
    enabled_rules: list[dict[str, Any]] = []
    for rule in catalog.values():
        if not bool(rule.get("enabled", True)):
            continue
        if stages and str(rule.get("stage") or "") not in stages:
            continue
        enabled_rules.append(rule)
    enabled_rules.sort(key=lambda row: (str(row.get("stage") or ""), str(row.get("rule_id") or "")))
    return enabled_rules


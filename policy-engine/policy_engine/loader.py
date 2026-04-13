from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from .output_validator import DEFAULT_RULE_PATH, load_rule_catalog


class PolicySource(Protocol):
    """Read-through interface for precheck/runtime policy consumers.

    A PolicySource returns normalized rule dicts that match the JSON
    seed format: {rule_id, stage, severity, enabled, description,
    trigger_flags, enforcement, source_version, ...}. Only enabled
    rules should be returned.
    """

    def list_enabled_rules(self, stages: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
        ...


class FilePolicySource:
    """Loads rules from a JSON seed file (default behavior)."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_RULE_PATH

    def list_enabled_rules(self, stages: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
        catalog = load_rule_catalog(self._path)
        return _filter_enabled_rules(catalog.values(), stages=stages)


class StaticPolicySource:
    """In-memory source for tests.

    Accepts a list of rule dicts and filters them on each call.
    """

    def __init__(self, rules: list[dict[str, Any]]) -> None:
        self._rules = list(rules)

    def list_enabled_rules(self, stages: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
        return _filter_enabled_rules(self._rules, stages=stages)


_active_source: PolicySource | None = None


def set_active_policy_source(source: PolicySource | None) -> None:
    """Install a process-global PolicySource consulted by load_enabled_policy_rules.

    ops-api registers a DB-backed source during create_app so precheck
    evaluations reflect live policy toggles. Pass ``None`` to clear and
    fall back to the on-disk JSON seed (useful for test teardown).
    """
    global _active_source
    _active_source = source


def get_active_policy_source() -> PolicySource | None:
    return _active_source


def load_enabled_policy_rules(
    path: Path | None = None,
    *,
    stages: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """Return enabled rules, honoring the active PolicySource when set.

    An explicit ``path`` bypasses the active source so callers that need
    the canonical on-disk catalog (seed loaders, migrations) can still
    read directly from the JSON file.
    """
    if path is not None:
        return FilePolicySource(path).list_enabled_rules(stages=stages)
    if _active_source is not None:
        return _active_source.list_enabled_rules(stages=stages)
    return FilePolicySource().list_enabled_rules(stages=stages)


def _filter_enabled_rules(
    rules,
    *,
    stages: tuple[str, ...] | None,
) -> list[dict[str, Any]]:
    enabled_rules: list[dict[str, Any]] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if not bool(rule.get("enabled", True)):
            continue
        if stages and str(rule.get("stage") or "") not in stages:
            continue
        enabled_rules.append(rule)
    enabled_rules.sort(key=lambda row: (str(row.get("stage") or ""), str(row.get("rule_id") or "")))
    return enabled_rules

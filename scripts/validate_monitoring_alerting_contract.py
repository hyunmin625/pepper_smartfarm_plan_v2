#!/usr/bin/env python3
"""Validate monitoring, alerting, and audit contract wiring."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_LOG_TERMS = [
    "request log",
    "decision log",
    "command log",
    "robot log",
    "policy block log",
    "sensor anomaly log",
]
EXPECTED_METRICS = [
    "sensor_ingest_rate_per_min",
    "stale_sensor_count",
    "decision_latency_avg_ms",
    "malformed_response_count",
    "blocked_action_count",
    "approval_pending_count",
    "command_success_rate",
    "robot_task_success_rate",
    "safe_mode_count",
]
EXPECTED_ALARMS = [
    "high_temperature",
    "high_humidity",
    "sensor_anomaly",
    "device_unresponsive",
    "policy_block_spike",
    "decision_failure",
    "robot_safety",
    "safe_mode_entry",
]
EXPECTED_ROUTES = [
    "/monitoring/metrics",
    "/monitoring/alarms",
    "/operator/overrides",
]


def read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def require_contains(errors: list[str], label: str, text: str, expected: list[str]) -> None:
    for item in expected:
        if item not in text:
            errors.append(f"{label} missing {item}")


def main() -> int:
    errors: list[str] = []
    app_text = read("ops-api/ops_api/app.py")
    models_text = read("ops-api/ops_api/models.py")
    api_models_text = read("ops-api/ops_api/api_models.py")
    auth_text = read("ops-api/ops_api/auth.py")
    doc_text = read("docs/monitoring_alerting_audit_contract.md")
    schema_text = read("infra/postgres/001_initial_schema.sql") + read("infra/postgres/007_operator_overrides.sql")
    todo_text = read("todo.md")

    require_contains(errors, "doc log contract", doc_text, EXPECTED_LOG_TERMS)
    require_contains(errors, "doc metrics", doc_text, EXPECTED_METRICS)
    require_contains(errors, "doc alarms", doc_text, EXPECTED_ALARMS)
    require_contains(errors, "app routes", app_text, EXPECTED_ROUTES)
    require_contains(errors, "app metrics", app_text, EXPECTED_METRICS)
    require_contains(errors, "app alarms", app_text, EXPECTED_ALARMS)
    require_contains(errors, "dashboard payload", app_text, ["monitoring", "operator_overrides"])
    require_contains(errors, "operator override model", models_text, ["class OperatorOverrideRecord", "operator_overrides"])
    require_contains(errors, "operator override request", api_models_text, ["class OperatorOverrideRequest", "manual_override", "safe_mode"])
    require_contains(errors, "operator override permission", auth_text, ["record_operator_override"])
    require_contains(errors, "operator override schema", schema_text, ["CREATE TABLE IF NOT EXISTS operator_overrides", "idx_operator_overrides_state_created_at"])

    section_start = todo_text.index("# 13. 모니터링/알람/감사")
    section_end = todo_text.index("# 14. 프론트엔드/운영 대시보드", section_start)
    section = todo_text[section_start:section_end]
    if "[ ]" in section:
        errors.append("todo section 13 still has unchecked items")

    print(json.dumps({"errors": errors, "checked_routes": EXPECTED_ROUTES}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

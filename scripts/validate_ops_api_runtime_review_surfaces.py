#!/usr/bin/env python3
"""Validate Phase P runtime review surfaces against PostgreSQL only.

Checks:
1. Dashboard HTML contains runtime/policy/automation review hooks.
2. PATCH /policies/{id} updates source_version and writes policy_changed.
3. GET /policies/{id}/history and /policies/events?policy_id=... expose it.
4. GET /dashboard/data returns the official runtime_gate payload and
   dashboard policy_changes summary.

The script follows the repository PostgreSQL-only rule. If no PostgreSQL
URL is configured, it exits 0 with a SKIP message rather than bootstrapping
SQLite.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from ops_api.database import build_session_factory, init_db  # noqa: E402
from ops_api.models import PolicyEventRecord, PolicyRecord  # noqa: E402
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402


HTML_HOOKS = [
    'id="runtimeGateCard"',
    "function renderRuntimeGateCard",
    'id="policyEventQueueList"',
    "function renderPolicyEventQueues",
    'id="policyChangeList"',
    "function renderPolicyChanges",
    "function showPolicyHistory",
    'id="automationReviewSummary"',
    "function renderAutomationReviewSummary",
]


def _resolve_base_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print(
            "[validate_ops_api_runtime_review_surfaces] SKIP: set OPS_API_DATABASE_URL "
            "or OPS_API_POSTGRES_SMOKE_URL",
        )
        raise SystemExit(0)
    return url.strip()


@contextmanager
def _scoped_smoke_run():
    base_url = _resolve_base_postgres_url()
    suffix = secrets.token_hex(4)
    session_factory = build_session_factory(base_url)
    init_db(session_factory)
    try:
        yield base_url, suffix
    finally:
        policy_id = f"runtime-review-smoke-{suffix}"
        session = session_factory()
        try:
            session.query(PolicyEventRecord).filter(
                PolicyEventRecord.request_id.like(f"policy-update-{policy_id}%")
            ).delete(synchronize_session=False)
            session.query(PolicyRecord).filter(PolicyRecord.policy_id == policy_id).delete(
                synchronize_session=False
            )
            session.commit()
        finally:
            session.close()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def _make_settings(tmp_root: Path, database_url: str) -> Settings:
    mode_path = tmp_root / "runtime_mode.json"
    save_runtime_mode(mode_path, mode="approval", actor_id="runtime-review-smoke", reason="phase-p")
    return Settings(
        database_url=database_url,
        runtime_mode_path=mode_path,
        auth_mode="disabled",
        auth_tokens_json="",
        shadow_audit_log_path=tmp_root / "shadow.jsonl",
        validator_audit_log_path=tmp_root / "validator.jsonl",
        llm_provider="stub",
        llm_model_id=(
            "ft:gpt-4.1-mini-2025-04-14:hyunmin:"
            "ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3"
        ),
        llm_prompt_version="sft_v5",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
        retriever_type="keyword",
        retriever_rag_index_path="",
        automation_enabled=False,
    )


def _seed_policy(database_url: str, policy_id: str) -> str:
    session_factory = build_session_factory(database_url)
    session = session_factory()
    try:
        row = PolicyRecord(
            policy_id=policy_id,
            policy_stage="runtime_smoke",
            severity="medium",
            enabled=True,
            description="runtime review smoke policy",
            trigger_flags_json=json.dumps(["runtime_smoke"]),
            enforcement_json=json.dumps({"action": "approval_required"}),
            source_version="runtime-smoke-v0",
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.source_version
    finally:
        session.close()


def test_runtime_review_surfaces(database_url: str, suffix: str) -> None:
    policy_id = f"runtime-review-smoke-{suffix}"
    original_version = _seed_policy(database_url, policy_id)
    with tempfile.TemporaryDirectory() as tmp:
        settings = _make_settings(Path(tmp), database_url)
        app = create_app(settings=settings)
        with TestClient(app) as client:
            print("[1] dashboard HTML hooks")
            html_resp = client.get("/dashboard")
            _assert(html_resp.status_code == 200, "GET /dashboard returns 200")
            html = html_resp.text
            for hook in HTML_HOOKS:
                _assert(hook in html, f"dashboard contains {hook}")

            print()
            print("[2] policy update writes source_version + event")
            update_resp = client.post(
                f"/policies/{policy_id}",
                json={"enabled": False, "severity": "high"},
            )
            _assert(update_resp.status_code == 200, "policy update returns 200")
            updated = update_resp.json()["data"]["policy"]
            _assert(updated["enabled"] is False, "policy enabled changed")
            _assert(updated["severity"] == "high", "policy severity changed")
            _assert(updated["source_version"] != original_version, "source_version changed")
            _assert(updated["source_version"].startswith(policy_id), "source_version includes policy id")

            print()
            print("[3] history and event filters")
            history_resp = client.get(f"/policies/{policy_id}/history", params={"limit": 5})
            _assert(history_resp.status_code == 200, "policy history returns 200")
            history_items = history_resp.json()["data"]["items"]
            _assert(len(history_items) == 1, "policy history returns one smoke event")
            event = history_items[0]
            _assert(event["event_type"] == "policy_changed", "history event_type is policy_changed")
            _assert(event["payload"]["changed_fields"] == ["enabled", "severity"], "changed_fields captured")

            events_resp = client.get(
                "/policies/events",
                params={"event_type": "policy_changed", "policy_id": policy_id, "limit": 10},
            )
            _assert(events_resp.status_code == 200, "policy events filter returns 200")
            events = events_resp.json()["data"]["items"]
            _assert(len(events) == 1, "policy events filter returns one smoke event")
            _assert(events[0]["policy_ids"] == [policy_id], "policy_id filter scoped correctly")

            print()
            print("[4] dashboard runtime_gate payload")
            dash_resp = client.get("/dashboard/data")
            _assert(dash_resp.status_code == 200, "dashboard data returns 200")
            data = dash_resp.json()["data"]
            gate = data.get("runtime_gate") or {}
            for key in (
                "gate_state",
                "runtime_mode",
                "champion",
                "retriever_type",
                "shadow_window_status",
                "approval_queue_count",
                "policy_risk_event_count",
                "policy_change_count",
                "blockers",
            ):
                _assert(key in gate, f"runtime_gate contains {key}")
            _assert(gate["runtime_mode"] == "approval", "runtime_gate reflects approval mode")
            _assert(gate["champion"]["is_ds_v11_frozen"] is True, "runtime_gate detects ds_v11 frozen champion")
            _assert(gate["retriever_type"] == "keyword", "runtime_gate reports keyword retriever")
            _assert(data["summary"]["policy_change_count"] >= 1, "summary includes policy_change_count")
            _assert(
                any(policy_id in item["policy_ids"] for item in data.get("policy_changes", [])),
                "dashboard policy_changes includes smoke event",
            )


def main() -> int:
    with _scoped_smoke_run() as (database_url, suffix):
        test_runtime_review_surfaces(database_url, suffix)
    print()
    print("all runtime review surface invariants passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

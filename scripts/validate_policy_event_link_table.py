#!/usr/bin/env python3
"""Validate indexed policy_event -> policy_id link filtering on PostgreSQL."""

from __future__ import annotations

import json
import os
import secrets
import sys
import tempfile
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
from ops_api.models import PolicyEventPolicyLinkRecord, PolicyEventRecord, PolicyRecord  # noqa: E402
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402


def _resolve_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print("[validate_policy_event_link_table] SKIP: set OPS_API_DATABASE_URL or OPS_API_POSTGRES_SMOKE_URL")
        raise SystemExit(0)
    return url.strip()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def _make_settings(tmp_root: Path, database_url: str) -> Settings:
    mode_path = tmp_root / "runtime_mode.json"
    save_runtime_mode(mode_path, mode="approval", actor_id="policy-event-link-smoke", reason="link-table")
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


def _seed_policy(session_factory, policy_id: str) -> None:
    session = session_factory()
    try:
        session.add(
            PolicyRecord(
                policy_id=policy_id,
                policy_stage="link_smoke",
                severity="medium",
                enabled=True,
                description="policy event link smoke policy",
                trigger_flags_json=json.dumps(["link_smoke"]),
                enforcement_json=json.dumps({"action": "approval_required"}),
                source_version="link-smoke-v0",
            )
        )
        session.commit()
    finally:
        session.close()


def _cleanup(session_factory, policy_id: str) -> None:
    session = session_factory()
    try:
        session.query(PolicyEventPolicyLinkRecord).filter(
            PolicyEventPolicyLinkRecord.policy_id == policy_id
        ).delete(synchronize_session=False)
        session.query(PolicyEventRecord).filter(
            PolicyEventRecord.request_id.like(f"policy-update-{policy_id}%")
        ).delete(synchronize_session=False)
        session.query(PolicyRecord).filter(PolicyRecord.policy_id == policy_id).delete(
            synchronize_session=False
        )
        session.commit()
    finally:
        session.close()


def main() -> int:
    database_url = _resolve_postgres_url()
    suffix = secrets.token_hex(4)
    policy_id = f"policy-link-smoke-{suffix}"
    session_factory = build_session_factory(database_url)
    init_db(session_factory)
    _cleanup(session_factory, policy_id)
    _seed_policy(session_factory, policy_id)

    try:
        with tempfile.TemporaryDirectory(prefix="policy-event-link-") as tmp:
            app = create_app(settings=_make_settings(Path(tmp), database_url))
            with TestClient(app) as client:
                print("[1] policy update writes policy_event link rows")
                resp = client.post(f"/policies/{policy_id}", json={"enabled": False, "severity": "high"})
                _assert(resp.status_code == 200, f"policy update returns 200 (got {resp.status_code})")

                session = session_factory()
                try:
                    links = session.query(PolicyEventPolicyLinkRecord).filter(
                        PolicyEventPolicyLinkRecord.policy_id == policy_id
                    ).all()
                finally:
                    session.close()
                _assert(len(links) == 1, f"one link row exists for {policy_id}")

                print()
                print("[2] policy_id filter uses the normalized link path")
                events_resp = client.get(
                    "/policies/events",
                    params={"event_type": "policy_changed", "policy_id": policy_id, "limit": 10},
                )
                _assert(events_resp.status_code == 200, f"policy events returns 200 (got {events_resp.status_code})")
                events = events_resp.json()["data"]["items"]
                _assert(len(events) == 1, "policy_id filter returns exactly one smoke event")
                _assert(events[0]["policy_ids"] == [policy_id], "filtered event carries expected policy_id")

                miss_resp = client.get(
                    "/policies/events",
                    params={"event_type": "policy_changed", "policy_id": f"{policy_id}-missing", "limit": 10},
                )
                _assert(miss_resp.status_code == 200, "missing policy_id filter returns 200")
                _assert(miss_resp.json()["data"]["items"] == [], "missing policy_id filter returns no events")

        print()
        print("policy event link table smoke passed.")
        return 0
    finally:
        _cleanup(session_factory, policy_id)


if __name__ == "__main__":
    raise SystemExit(main())

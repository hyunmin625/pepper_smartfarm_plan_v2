#!/usr/bin/env python3
"""Validate that ops-api's DbPolicySource drives live precheck behavior.

This smoke proves three things without needing a real PostgreSQL:

1. ``create_app`` installs ``DbPolicySource`` as the active PolicySource,
   so ``load_enabled_policy_rules()`` in precheck returns DB rows rather
   than the canonical JSON seed file.
2. Toggling a policy through ``PATCH /policies/{policy_id}`` is picked
   up immediately: the next call to ``list_enabled_rules`` no longer
   yields that rule, and the device precheck for its trigger stops
   firing.
3. Re-enabling the policy restores precheck behavior so the toggle path
   is reversible.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from policy_engine import (  # noqa: E402
    evaluate_device_policy_precheck,
    get_active_policy_source,
    load_enabled_policy_rules,
    set_active_policy_source,
)


TARGET_RULE_ID = "HSV-01"


def _worker_present_raw() -> dict[str, Any]:
    return {
        "action_type": "adjust_fan",
        "operator_context": {"operator_present": True},
        "policy_snapshot": {"policy_result": "pass", "policy_ids": []},
        "sensor_quality": {"overall": "good"},
    }


def _make_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path}/ops_api.db",
        runtime_mode_path=tmp_path / "runtime_mode.json",
        auth_mode="disabled",
        auth_tokens_json="",
        shadow_audit_log_path=tmp_path / "shadow.jsonl",
        validator_audit_log_path=tmp_path / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
    )


def main() -> int:
    errors: list[str] = []
    for key in ("OPS_API_AUTH_MODE", "OPS_API_AUTH_TOKENS_JSON"):
        os.environ.pop(key, None)

    # Clear any lingering active source from a prior import
    set_active_policy_source(None)

    with tempfile.TemporaryDirectory(prefix="ops-api-policy-source-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        app = create_app(settings=_make_settings(tmp_path))
        client = TestClient(app)

        source = get_active_policy_source()
        if source is None:
            errors.append("create_app should register an active policy source")
            return _finish(errors)

        db_rules = {rule["rule_id"] for rule in source.list_enabled_rules()}
        if TARGET_RULE_ID not in db_rules:
            errors.append(f"seed must include {TARGET_RULE_ID} in enabled DB rules")
            return _finish(errors, extra={"db_rules": sorted(db_rules)})

        seed_rules = {
            rule["rule_id"]
            for rule in load_enabled_policy_rules(
                path=REPO_ROOT / "data/examples/policy_output_validator_rules_seed.json"
            )
        }
        if TARGET_RULE_ID not in seed_rules:
            errors.append("on-disk seed must include the target rule for a baseline check")

        runtime_rules = {rule["rule_id"] for rule in load_enabled_policy_rules()}
        if TARGET_RULE_ID not in runtime_rules:
            errors.append(
                "load_enabled_policy_rules() with no path should delegate to the active DB source"
            )

        initial_precheck = evaluate_device_policy_precheck(_worker_present_raw())
        if initial_precheck.policy_result != "blocked":
            errors.append(
                f"expected worker_present to block adjust_fan before toggling, "
                f"got {initial_precheck.policy_result}"
            )
        if TARGET_RULE_ID not in initial_precheck.policy_ids:
            errors.append(f"expected {TARGET_RULE_ID} in initial precheck policy_ids")

        disable = client.post(f"/policies/{TARGET_RULE_ID}", json={"enabled": False})
        if disable.status_code != 200:
            errors.append(f"disable toggle returned {disable.status_code}")

        post_disable_rules = {rule["rule_id"] for rule in source.list_enabled_rules()}
        if TARGET_RULE_ID in post_disable_rules:
            errors.append(
                f"{TARGET_RULE_ID} should be absent from list_enabled_rules after disable"
            )

        after_disable = evaluate_device_policy_precheck(_worker_present_raw())
        if TARGET_RULE_ID in after_disable.policy_ids:
            errors.append(
                f"precheck should stop matching {TARGET_RULE_ID} once the DB row is disabled"
            )
        if any(reason.endswith(TARGET_RULE_ID) for reason in after_disable.reasons):
            errors.append("precheck reasons should not reference a disabled rule")

        reenable = client.post(f"/policies/{TARGET_RULE_ID}", json={"enabled": True})
        if reenable.status_code != 200:
            errors.append(f"re-enable toggle returned {reenable.status_code}")

        reenabled = evaluate_device_policy_precheck(_worker_present_raw())
        if reenabled.policy_result != "blocked":
            errors.append(
                "precheck must resume blocking after re-enabling the target rule"
            )
        if TARGET_RULE_ID not in reenabled.policy_ids:
            errors.append(f"expected {TARGET_RULE_ID} in precheck after re-enable")

        return _finish(
            errors,
            extra={
                "db_rule_count": len(db_rules),
                "seed_rule_count": len(seed_rules),
                "initial_policy_result": initial_precheck.policy_result,
                "post_disable_policy_ids": after_disable.policy_ids,
                "reenabled_policy_result": reenabled.policy_result,
            },
        )


def _finish(errors: list[str], extra: dict[str, Any] | None = None) -> int:
    payload: dict[str, Any] = {
        "errors": errors,
        "status": "ok" if not errors else "failed",
    }
    if extra:
        payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    set_active_policy_source(None)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

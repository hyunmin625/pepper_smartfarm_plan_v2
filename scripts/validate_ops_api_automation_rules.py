#!/usr/bin/env python3
"""Validate automation rules CRUD + engine end-to-end.

Exercises:
1. GET /automation/rules on empty DB returns [].
2. POST /automation/rules creates a rule, GET reflects it.
3. PATCH /automation/rules/{id} updates fields.
4. PATCH /automation/rules/{id}/toggle flips enabled.
5. POST /automation/evaluate with sensor_snapshot that MATCHES produces a
   matched rule + proposed_action in the dry-run report without persisting.
6. POST /automation/evaluate with sensor_snapshot that does NOT match
   returns 0 matches.
7. Live evaluate_rules() with persist=True writes a trigger row.
8. DELETE removes the rule and its triggers (cascade).
9. Dashboard HTML carries the automation view + modal hooks.
10. Permission: header_token + viewer role can read but cannot create.
"""

from __future__ import annotations

import json
import os
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
from ops_api.automation import evaluate_rules  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from ops_api.database import build_session_factory, init_db, build_engine  # noqa: E402
from ops_api.models import (  # noqa: E402
    AutomationRuleRecord,
    AutomationRuleTriggerRecord,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def make_settings(tmp_root: Path, *, auth_mode: str = "disabled") -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_root}/ops_api.db",
        runtime_mode_path=tmp_root / "runtime_mode.json",
        auth_mode=auth_mode,
        auth_tokens_json="",
        shadow_audit_log_path=tmp_root / "shadow.jsonl",
        validator_audit_log_path=tmp_root / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
        retriever_type="keyword",
        retriever_rag_index_path="",
    )


SAMPLE_RULE = {
    "rule_id": "rain-close-vent",
    "name": "강우 시 천장 닫기",
    "description": "강우량이 0.5mm 초과 시 roof vent 닫기",
    "sensor_key": "ext_rainfall_mm",
    "operator": "gt",
    "threshold_value": 0.5,
    "target_device_type": "roof_vent",
    "target_action": "close_vent",
    "action_payload": {"target_position_pct": 0},
    "runtime_mode_gate": "approval",
    "priority": 10,
    "cooldown_minutes": 5,
    "enabled": True,
    "owner_role": "operator",
}


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="automation-smoke-") as tmpdir:
        tmp = Path(tmpdir)
        settings = make_settings(tmp)
        app = create_app(settings=settings)
        client = TestClient(app)

        # 1) Empty list
        print("[1] GET /automation/rules empty")
        res = client.get("/automation/rules")
        _assert(res.status_code == 200, f"status 200 (got {res.status_code})")
        data = res.json()["data"]
        _assert(isinstance(data.get("rules"), list), "rules is a list")
        _assert(len(data["rules"]) == 0, f"rules empty (got {len(data['rules'])})")

        # 2) Create rule
        print("\n[2] POST /automation/rules create")
        res = client.post("/automation/rules", json=SAMPLE_RULE)
        _assert(res.status_code == 200, f"status 200 (got {res.status_code}: {res.text})")
        body = res.json()
        _assert(body.get("meta", {}).get("created") is True, "meta.created == True")
        rule_payload = body["data"]
        _assert(rule_payload["rule_id"] == SAMPLE_RULE["rule_id"], "rule_id echoed")
        _assert(rule_payload["sensor_key"] == "ext_rainfall_mm", "sensor_key echoed")

        # 3) PATCH rule
        print("\n[3] PATCH /automation/rules/{id} update priority")
        res = client.patch(
            f"/automation/rules/{SAMPLE_RULE['rule_id']}",
            json={"priority": 5, "description": "updated"},
        )
        _assert(res.status_code == 200, f"status 200 (got {res.status_code}: {res.text})")
        updated = res.json()["data"]
        _assert(updated["priority"] == 5, f"priority updated (got {updated['priority']})")
        _assert(updated["description"] == "updated", "description updated")

        # 4) Toggle
        print("\n[4] PATCH /automation/rules/{id}/toggle")
        res = client.patch(
            f"/automation/rules/{SAMPLE_RULE['rule_id']}/toggle",
            json={"enabled": False},
        )
        _assert(res.status_code == 200, f"status 200 (got {res.status_code})")
        _assert(res.json()["data"]["enabled"] is False, "enabled flipped to False")
        # Re-enable for match test
        client.patch(
            f"/automation/rules/{SAMPLE_RULE['rule_id']}/toggle",
            json={"enabled": True},
        )

        # 5) Evaluate dry-run with MATCHING snapshot
        print("\n[5] POST /automation/evaluate matching snapshot")
        res = client.post(
            "/automation/evaluate",
            json={
                "sensor_snapshot": {"ext_rainfall_mm": 1.2},
                "runtime_mode_override": "approval",
            },
        )
        _assert(res.status_code == 200, f"status 200 (got {res.status_code})")
        report = res.json()["data"]
        _assert(report["matched_rules"] == 1, f"1 matched rule (got {report['matched_rules']})")
        match = report["matches"][0]
        _assert(match["sensor_key"] == "ext_rainfall_mm", "match sensor_key")
        _assert(match["status"] == "approval_pending", f"gate → approval_pending (got {match['status']})")
        proposed = match["proposed_action"]
        _assert(proposed["action_type"] == "close_vent", "proposed action_type")
        _assert(proposed["target"]["target_type"] == "roof_vent", "proposed target_type")

        # 6) Evaluate NON-matching snapshot
        print("\n[6] POST /automation/evaluate non-matching snapshot")
        res = client.post(
            "/automation/evaluate",
            json={"sensor_snapshot": {"ext_rainfall_mm": 0.1}},
        )
        report = res.json()["data"]
        _assert(report["matched_rules"] == 0, f"0 matched (got {report['matched_rules']})")

        # 7) Direct evaluate_rules() with persist=True writes a trigger
        print("\n[7] evaluate_rules(persist=True) writes trigger row")
        factory = build_session_factory(settings.database_url)
        with factory() as session:
            rep = evaluate_rules(
                session,
                runtime_mode="approval",
                sensor_snapshot={"ext_rainfall_mm": 2.5},
                persist=True,
            )
            _assert(rep.matched_rules == 1, "offline evaluate matched 1")

        res = client.get("/automation/triggers?limit=10")
        _assert(res.status_code == 200, f"triggers status 200 (got {res.status_code})")
        triggers = res.json()["data"]["triggers"]
        _assert(len(triggers) >= 1, f"at least one trigger persisted (got {len(triggers)})")
        _assert(triggers[0]["sensor_key"] == "ext_rainfall_mm", "trigger sensor_key")
        _assert(triggers[0]["status"] in ("approval_pending", "shadow_logged"), f"trigger status valid (got {triggers[0]['status']})")

        # 8) DELETE rule cascades triggers
        print("\n[8] DELETE /automation/rules/{id} cascades")
        res = client.delete(f"/automation/rules/{SAMPLE_RULE['rule_id']}")
        _assert(res.status_code == 200, "delete status 200")
        _assert(res.json()["data"]["deleted"] is True, "deleted flag")
        res = client.get(f"/automation/rules/{SAMPLE_RULE['rule_id']}")
        _assert(res.status_code == 404, f"GET after delete → 404 (got {res.status_code})")
        res = client.get("/automation/triggers")
        _assert(res.status_code == 200, "triggers after delete")
        # Cascade should have removed the trigger too
        remaining = res.json()["data"]["triggers"]
        _assert(len(remaining) == 0, f"triggers cascaded (got {len(remaining)})")

        # 9) Dashboard HTML carries the automation view hooks
        print("\n[9] GET /dashboard has automation view hooks")
        res = client.get("/dashboard")
        _assert(res.status_code == 200, "dashboard status 200")
        html = res.text
        for hook in (
            'data-view="automation"',
            'id="automationRuleModal"',
            'id="automationRuleList"',
            'id="automationTriggerList"',
            'id="automationRuntimeChip"',
            "function refreshAutomation",
            "function renderAutomationRules",
            "function submitAutomationRuleForm",
            ">환경설정</span>",
        ):
            _assert(hook in html, f"dashboard contains `{hook}`")

    # 10) header_token + viewer role can read but cannot create
    with tempfile.TemporaryDirectory(prefix="automation-smoke-auth-") as tmpdir2:
        tmp2 = Path(tmpdir2)
        settings2 = make_settings(tmp2, auth_mode="header_token")
        app2 = create_app(settings=settings2)
        client2 = TestClient(app2)
        print("\n[10] header_token role gating")
        res = client2.get("/automation/rules", headers={"X-API-Key": "viewer-demo-token"})
        _assert(res.status_code == 200, f"viewer GET 200 (got {res.status_code})")
        res = client2.post(
            "/automation/rules",
            json=SAMPLE_RULE,
            headers={"X-API-Key": "viewer-demo-token"},
        )
        _assert(res.status_code == 403, f"viewer POST 403 (got {res.status_code})")
        res = client2.post(
            "/automation/rules",
            json=SAMPLE_RULE,
            headers={"X-API-Key": "operator-demo-token"},
        )
        _assert(res.status_code == 200, f"operator POST 200 (got {res.status_code}: {res.text})")

    print("\nall automation rules invariants passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

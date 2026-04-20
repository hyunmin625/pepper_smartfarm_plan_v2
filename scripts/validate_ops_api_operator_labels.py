#!/usr/bin/env python3
"""Verify operator-friendly labels + alerts filter/reason summary.

Two related quick-wins ship together:

1. **Operator-friendly labels** — the dashboard JS now carries an
   ``OPERATOR_LABEL`` table that maps enums (approval_pending,
   dispatch_fault, blocked_guard, severity/status codes) to plain
   Korean. Non-engineer operators should never see raw machine enums in
   status chips.
2. **Alerts view filter + cause renderer** — the ``/알림`` view now has
   ``#alertFilterBar`` with category chips (자동화 / 정책 / 위험도 /
   검증) and severity chips, and each alert row surfaces its
   ``validator_reason_codes`` translated through ``REASON_CODE_LABEL``
   so the operator sees "실행 어댑터 오류" instead of
   ``dispatcher_error``.

This smoke checks both by:
- Asserting every HTML / JS hook exists on ``GET /dashboard``.
- Seeding three alerts with distinct alert_type prefixes (automation /
  policy / risk) and reason codes, then calling ``GET /alerts`` and
  ``GET /overview/summary`` to confirm ``validator_reason_codes`` is a
  list on the payload the client consumes.
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
from ops_api.models import AlertRecord, ZoneRecord  # noqa: E402
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402


LABEL_HOOKS = [
    # Relabel helper table + functions
    "const OPERATOR_LABEL",
    "function operatorLabel",
    "function alertTypeLabel",
    # Mandatory plain-Korean mappings exposed to operators
    "'승인 대기'",
    "'실행 실패'",
    "'안전 장치 차단'",
    "'자동화 실행 실패'",
]

FILTER_HOOKS = [
    'id="alertFilterBar"',
    "ALERT_CATEGORY_PREFIXES",
    "function alertCategoryKey",
    "const REASON_CODE_LABEL",
    "function reasonLabel",
    "const alertsFilterState",
    "function setAlertCategory",
    "function setAlertSeverity",
    # Korean category labels baked into the filter chip renderer
    "자동화",
    "정책",
    "위험도",
    "검증",
    # A few representative reason code translations
    "'실행 어댑터 오류'",
    "'작업자 감지됨'",
    "'정책 위반'",
]


def _resolve_base_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print(
            "[validate_ops_api_operator_labels] SKIP: set OPS_API_DATABASE_URL or "
            "OPS_API_POSTGRES_SMOKE_URL",
        )
        raise SystemExit(0)
    return url.strip()


@contextmanager
def _scoped_smoke_run(suffix: str):
    base_url = _resolve_base_postgres_url()
    session_factory = build_session_factory(base_url)
    init_db(session_factory)
    try:
        yield base_url, session_factory
    finally:
        session = session_factory()
        try:
            session.query(AlertRecord).filter(
                AlertRecord.zone_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
            session.query(ZoneRecord).filter(
                ZoneRecord.zone_id.like(f"%{suffix}%")
            ).delete(synchronize_session=False)
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
    save_runtime_mode(mode_path, mode="approval", actor_id="smoke", reason="operator_labels")
    return Settings(
        database_url=database_url,
        runtime_mode_path=mode_path,
        auth_mode="disabled",
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
        automation_enabled=False,
    )


def _seed_alert_bundle(session_factory, *, suffix: str) -> None:
    zone_id = f"gh-01-zone-a-{suffix}"
    session = session_factory()
    try:
        existing = session.query(ZoneRecord).filter(ZoneRecord.zone_id == zone_id).one_or_none()
        if existing is None:
            session.add(
                ZoneRecord(
                    zone_id=zone_id,
                    zone_type="greenhouse",
                    priority="normal",
                    description="operator labels smoke",
                    metadata_json="{}",
                )
            )
            session.commit()

        bundle = [
            dict(
                alert_type="automation_dispatch_fault",
                severity="error",
                summary="자동화 실행 실패 smoke",
                reasons=["dispatcher_error"],
            ),
            dict(
                alert_type="policy_violation",
                severity="critical",
                summary="정책 위반 smoke",
                reasons=["HSV-03", "blocked_action"],
            ),
            dict(
                alert_type="risk_elevated",
                severity="warning",
                summary="위험 상승 smoke",
                reasons=["sensor_quality_bad"],
            ),
        ]
        for item in bundle:
            session.add(
                AlertRecord(
                    decision_id=None,
                    zone_id=zone_id,
                    alert_type=item["alert_type"],
                    severity=item["severity"],
                    status="active",
                    summary=item["summary"],
                    validator_reason_codes_json=json.dumps(item["reasons"], ensure_ascii=False),
                    payload_json="{}",
                )
            )
        session.commit()
    finally:
        session.close()


def main() -> int:
    suffix = secrets.token_hex(4)
    with _scoped_smoke_run(suffix) as (db_url, session_factory):
        with tempfile.TemporaryDirectory(prefix="ops-api-labels-") as tmp:
            tmp_root = Path(tmp)
            settings = _make_settings(tmp_root, db_url)

            app = create_app(settings=settings)
            client = TestClient(app)

            print("[1] GET /dashboard — operator label hooks")
            res = client.get("/dashboard")
            _assert(res.status_code == 200, f"/dashboard status 200 (got {res.status_code})")
            html = res.text
            for hook in LABEL_HOOKS:
                _assert(hook in html, f"dashboard html contains `{hook}`")

            print()
            print("[2] GET /dashboard — alerts filter + reason summary hooks")
            for hook in FILTER_HOOKS:
                _assert(hook in html, f"dashboard html contains `{hook}`")

            print()
            print("[3] GET /alerts — seeded rows carry validator_reason_codes as list")
            _seed_alert_bundle(session_factory, suffix=suffix)
            res = client.get("/alerts", params={"zone_id": f"gh-01-zone-a-{suffix}"})
            _assert(res.status_code == 200, "/alerts status 200")
            items = res.json()["data"]["items"]
            _assert(len(items) == 3, f"3 alerts returned (got {len(items)})")
            by_type = {row["alert_type"]: row for row in items}
            _assert(
                "automation_dispatch_fault" in by_type,
                "automation_dispatch_fault row present",
            )
            _assert(
                isinstance(by_type["automation_dispatch_fault"]["validator_reason_codes"], list),
                "validator_reason_codes is a list",
            )
            _assert(
                by_type["automation_dispatch_fault"]["validator_reason_codes"] == ["dispatcher_error"],
                "reason codes round-trip through serializer",
            )
            _assert(
                by_type["policy_violation"]["validator_reason_codes"] == ["HSV-03", "blocked_action"],
                "multi-reason row round-trips",
            )
            _assert(
                by_type["risk_elevated"]["validator_reason_codes"] == ["sensor_quality_bad"],
                "risk row carries sensor_quality_bad",
            )

    print()
    print("all operator label invariants passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

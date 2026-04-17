#!/usr/bin/env python3
"""Validate AutomationRunner tick and lifespan wiring.

Exercises:

1. run_once() with a matching rule + fresh sensor_readings row →
   one approval_pending trigger row written.
2. Second run_once() → cooldown_skipped trigger appended (rule still
   matches but cooldown window is active).
3. run_once() where sensor_readings are older than snapshot window →
   no match (trigger count unchanged).
4. Farm-wide rule (zone_id=None) fires per concrete zone discovered
   from sensor_readings.
5. automation_enabled=False → lifespan does not spawn a runner task
   (app.state.services.automation_runner._task is None after startup).
6. automation_enabled=True + interval_sec>0 → lifespan spawns a
   runner task (task is set after startup, cleaned up after shutdown).

Each data-touching test is scoped via ``_scoped_smoke_run`` which
returns a suffix tagged onto rule_id / zone_id. Cleanup deletes those
rows (and, via ON DELETE CASCADE, their trigger children) so repeated
runs stay deterministic on a shared ``pepper_ops`` database without
requiring CREATEDB privilege.
"""

from __future__ import annotations

import os
import secrets
import sys
import tempfile
from contextlib import contextmanager
from datetime import timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.automation_runner import AutomationRunner  # noqa: E402
from ops_api.config import Settings  # noqa: E402
from ops_api.database import build_session_factory, init_db  # noqa: E402
from ops_api.models import (  # noqa: E402
    AutomationRuleRecord,
    AutomationRuleTriggerRecord,
    SensorReadingRecord,
    utc_now,
)
from ops_api.runtime_mode import save_runtime_mode  # noqa: E402


def _resolve_base_postgres_url() -> str:
    url = os.getenv("OPS_API_POSTGRES_SMOKE_URL") or os.getenv("OPS_API_DATABASE_URL")
    if not url or not url.strip():
        print(
            "[validate_ops_api_automation_runner] SKIP: set OPS_API_DATABASE_URL or "
            "OPS_API_POSTGRES_SMOKE_URL",
        )
        raise SystemExit(0)
    return url.strip()


@contextmanager
def _scoped_smoke_run():
    """Yield (db_url, suffix) scoped to this run, cleaning up afterwards.

    We reuse the configured ``pepper_ops`` database rather than creating
    a throwaway one because the configured role typically lacks
    CREATEDB. Every test run tags its rule_id and zone_id with a random
    suffix so cleanup can DELETE this run's rows without touching seed
    data. Trigger rows cascade via the ON DELETE CASCADE on rule_id.
    """

    base_url = _resolve_base_postgres_url()
    suffix = secrets.token_hex(4)
    session_factory = build_session_factory(base_url)
    init_db(session_factory)
    try:
        yield base_url, suffix
    finally:
        session = session_factory()
        try:
            session.query(AutomationRuleRecord).filter(
                AutomationRuleRecord.rule_id.like(f"%{suffix}")
            ).delete(synchronize_session=False)
            session.query(SensorReadingRecord).filter(
                SensorReadingRecord.zone_id.like(f"%{suffix}")
            ).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def make_settings(
    tmp_root: Path,
    *,
    database_url: str,
    automation_enabled: bool = False,
    interval_sec: float = 15.0,
    window_sec: float = 120.0,
    runtime_mode: str = "approval",
) -> Settings:
    mode_path = tmp_root / "runtime_mode.json"
    save_runtime_mode(
        mode_path,
        mode=runtime_mode,
        actor_id="smoke",
        reason="automation_runner_smoke",
    )
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
        automation_enabled=automation_enabled,
        automation_interval_sec=interval_sec,
        automation_snapshot_window_sec=window_sec,
    )


def _insert_rule(
    session_factory,
    *,
    rule_id: str,
    zone_id: str | None,
    sensor_key: str,
    threshold: float,
    cooldown_minutes: int = 15,
) -> int:
    session = session_factory()
    try:
        row = AutomationRuleRecord(
            rule_id=rule_id,
            name=rule_id,
            description="",
            zone_id=zone_id,
            sensor_key=sensor_key,
            operator="gt",
            threshold_value=threshold,
            threshold_min=None,
            threshold_max=None,
            hysteresis_value=None,
            cooldown_minutes=cooldown_minutes,
            target_device_type="roof_vent",
            target_device_id=None,
            target_action="close_vent",
            action_payload_json="{}",
            priority=10,
            enabled=1,
            runtime_mode_gate="approval",
            owner_role="operator",
            created_by="smoke",
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id
    finally:
        session.close()


def _insert_reading(
    session_factory,
    *,
    zone_id: str,
    metric_name: str,
    value: float,
    offset_sec: float = 0.0,
) -> None:
    session = session_factory()
    try:
        measured_at = utc_now() - timedelta(seconds=offset_sec)
        row = SensorReadingRecord(
            measured_at=measured_at,
            ingested_at=measured_at,
            site_id="gh-01",
            zone_id=zone_id,
            record_kind="sensor",
            source_id="smoke-sensor",
            source_type="climate",
            metric_name=metric_name,
            metric_value_double=value,
            metric_value_text=None,
            unit=None,
            quality_flag="good",
            transport_status="ok",
            source="smoke",
            metadata_json="{}",
        )
        session.add(row)
        session.commit()
    finally:
        session.close()


def _trigger_rows_for(
    session_factory, *, rule_pks: list[int]
) -> list[AutomationRuleTriggerRecord]:
    if not rule_pks:
        return []
    session = session_factory()
    try:
        return list(
            session.query(AutomationRuleTriggerRecord)
            .filter(AutomationRuleTriggerRecord.rule_id.in_(rule_pks))
            .all()
        )
    finally:
        session.close()


def test_run_once_matching(db_url: str, suffix: str) -> None:
    print("[test] run_once emits approval_pending on match")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        settings = make_settings(tmp_root, database_url=db_url)
        session_factory = build_session_factory(settings.database_url)

        zone = f"gh-01-zone-a-{suffix}"
        rule_pk = _insert_rule(
            session_factory,
            rule_id=f"smoke-air-temp-{suffix}",
            zone_id=zone,
            sensor_key="air_temp_c",
            threshold=30.0,
        )
        _insert_reading(
            session_factory,
            zone_id=zone,
            metric_name="air_temp_c",
            value=32.5,
        )

        runner = AutomationRunner(session_factory=session_factory, settings=settings)
        results = runner.run_once()
        scoped = [r for r in results if r.zone_id == zone]
        _assert(len(scoped) == 1, "runner returns one tick result for this zone")
        _assert(scoped[0].matched_rules == 1, "one rule matched")
        _assert(scoped[0].snapshot_keys >= 1, "snapshot includes at least one key")

        rows = _trigger_rows_for(session_factory, rule_pks=[rule_pk])
        _assert(len(rows) == 1, "one trigger row persisted for this rule")
        _assert(rows[0].status == "approval_pending", "status is approval_pending")
        _assert(abs(rows[0].matched_value - 32.5) < 1e-6, "matched_value captured")


def test_cooldown_on_repeat(db_url: str, suffix: str) -> None:
    print("[test] cooldown_skipped on repeat inside cooldown window")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        settings = make_settings(tmp_root, database_url=db_url)
        session_factory = build_session_factory(settings.database_url)

        zone = f"gh-01-zone-a-{suffix}"
        rule_pk = _insert_rule(
            session_factory,
            rule_id=f"smoke-repeat-{suffix}",
            zone_id=zone,
            sensor_key="air_temp_c",
            threshold=30.0,
            cooldown_minutes=30,
        )
        _insert_reading(
            session_factory,
            zone_id=zone,
            metric_name="air_temp_c",
            value=33.0,
        )

        runner = AutomationRunner(session_factory=session_factory, settings=settings)
        runner.run_once()
        runner.run_once()

        rows = _trigger_rows_for(session_factory, rule_pks=[rule_pk])
        statuses = [r.status for r in rows]
        _assert(len(rows) == 2, "two trigger rows after two ticks")
        _assert(statuses.count("approval_pending") == 1, "first tick approval_pending")
        _assert(statuses.count("cooldown_skipped") == 1, "second tick cooldown_skipped")


def test_old_reading_outside_window_skipped(db_url: str, suffix: str) -> None:
    print("[test] reading older than window is ignored")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        settings = make_settings(tmp_root, database_url=db_url, window_sec=60)
        session_factory = build_session_factory(settings.database_url)

        zone = f"gh-01-zone-a-{suffix}"
        rule_pk = _insert_rule(
            session_factory,
            rule_id=f"smoke-window-{suffix}",
            zone_id=zone,
            sensor_key="air_temp_c",
            threshold=30.0,
        )
        _insert_reading(
            session_factory,
            zone_id=zone,
            metric_name="air_temp_c",
            value=35.0,
            offset_sec=300.0,  # 5 minutes old, window=60s
        )

        runner = AutomationRunner(session_factory=session_factory, settings=settings)
        results = runner.run_once()
        scoped = [r for r in results if r.zone_id == zone]
        _assert(len(scoped) == 1, "zone still discovered via enabled rule")
        _assert(scoped[0].snapshot_keys == 0, "old reading excluded from snapshot")
        _assert(scoped[0].matched_rules == 0, "no rule matches empty snapshot")
        _assert(
            len(_trigger_rows_for(session_factory, rule_pks=[rule_pk])) == 0,
            "no triggers persisted",
        )


def test_farm_wide_rule_fans_out(db_url: str, suffix: str) -> None:
    print("[test] farm-wide rule fires per zone discovered from readings")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        settings = make_settings(tmp_root, database_url=db_url)
        session_factory = build_session_factory(settings.database_url)

        zone_a = f"gh-01-zone-a-{suffix}"
        zone_b = f"gh-01-zone-b-{suffix}"
        rule_pk = _insert_rule(
            session_factory,
            rule_id=f"smoke-farm-wide-{suffix}",
            zone_id=None,
            sensor_key="ext_wind_speed_m_s",
            threshold=9.0,
        )
        _insert_reading(
            session_factory,
            zone_id=zone_a,
            metric_name="ext_wind_speed_m_s",
            value=12.0,
        )
        _insert_reading(
            session_factory,
            zone_id=zone_b,
            metric_name="ext_wind_speed_m_s",
            value=11.5,
        )

        runner = AutomationRunner(session_factory=session_factory, settings=settings)
        results = runner.run_once()
        zones_ticked = sorted(r.zone_id for r in results if r.zone_id in (zone_a, zone_b))
        _assert(zones_ticked == [zone_a, zone_b], "both zones ticked")

        rows = _trigger_rows_for(session_factory, rule_pks=[rule_pk])
        _assert(len(rows) == 2, "one trigger per zone")
        zone_triggers = [r.zone_id for r in rows]
        _assert(
            zone_triggers == [None, None],
            "triggers stamped with rule zone_id=None",
        )


def test_lifespan_disabled(db_url: str) -> None:
    print("[test] lifespan does not start runner when automation_enabled=False")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        settings = make_settings(
            tmp_root, database_url=db_url, automation_enabled=False
        )
        app = create_app(settings=settings)
        with TestClient(app) as client:
            response = client.get("/health")
            _assert(response.status_code == 200, "/health responds 200 with runner off")
            runner = app.state.services.automation_runner
            _assert(runner is not None, "automation_runner attached to services")
            _assert(runner._task is None, "runner task not spawned")


def test_lifespan_enabled_starts_task(db_url: str) -> None:
    print("[test] lifespan starts runner task when automation_enabled=True")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        settings = make_settings(
            tmp_root,
            database_url=db_url,
            automation_enabled=True,
            interval_sec=3600.0,  # avoid burning CPU during smoke
        )
        app = create_app(settings=settings)
        with TestClient(app) as client:
            response = client.get("/health")
            _assert(response.status_code == 200, "/health responds 200 with runner on")
            runner = app.state.services.automation_runner
            _assert(runner._task is not None, "runner task spawned in lifespan")
            _assert(not runner._task.done(), "runner task still running during request")
        _assert(runner._task is None, "runner task cleared after lifespan shutdown")


def main() -> int:
    scoped_tests = [
        ("run_once_matching", test_run_once_matching),
        ("cooldown_on_repeat", test_cooldown_on_repeat),
        ("old_reading_outside_window_skipped", test_old_reading_outside_window_skipped),
        ("farm_wide_rule_fans_out", test_farm_wide_rule_fans_out),
    ]
    lifespan_tests = [
        ("lifespan_disabled", test_lifespan_disabled),
        ("lifespan_enabled_starts_task", test_lifespan_enabled_starts_task),
    ]
    for _name, fn in scoped_tests:
        with _scoped_smoke_run() as (db_url, suffix):
            fn(db_url, suffix)
    # Lifespan tests only touch app state, not DB rows — a single
    # scoped run is enough to resolve db_url.
    with _scoped_smoke_run() as (db_url, _suffix):
        for _name, fn in lifespan_tests:
            fn(db_url)
    print("[validate_ops_api_automation_runner] all invariants passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

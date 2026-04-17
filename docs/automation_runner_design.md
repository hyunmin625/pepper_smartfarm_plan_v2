# Automation Runner 설계 (Phase P)

`evaluate_rules`를 주기적으로 자동 호출하는 백그라운드 컴포넌트를 정의한다.
Phase O에서는 `POST /automation/evaluate` dry-run과 `POST /automation/rules/{id}/toggle` 만 열려 있어 자동화 규칙이 실제로는 수동 호출로만 평가됐다. Phase P에서는 센서 데이터 흐름에 연결해 규칙을 자동으로 매칭한다.

## 1. 설계 방침

1. **폴링 기반 snapshot collector**를 먼저 구현한다. 주기(`automation_interval_sec`)마다 최근 snapshot window 안의 `sensor_readings` 최신값을 zone 단위로 dict로 묶어 `evaluate_rules(session, persist=True)`를 호출한다.
2. **RealtimeBroker 구독 기반 실시간 경로**는 후속 P-2.5 범위다. 첫 cut에서는 단순한 decorator-less asyncio 루프로 시작한다. 긴급 규칙(강우/강풍) 지연은 `interval_sec`(기본 15초) 크기로만 제한된다. 현장 도입 시 허용 지연 검증 후 실시간 경로를 추가한다.
3. **실행 순서는 기존 safety pipeline과 동일**하다. `evaluate_rules` 안의 cooldown → `_build_proposed_action` → `_gate_status`(runtime_mode ∩ rule gate 중 더 엄격한 쪽) 흐름을 그대로 쓴다. Phase O-3 이후 policy/guard 후처리는 Phase P-3에서 `approval` → `approvals` 테이블 연결로 확장한다.
4. **Fail soft**: sensor_readings DB 조회, evaluate_rules, session commit이 실패해도 runner는 예외를 삼키고 다음 tick에서 재시도한다. 단일 평가 실패가 FastAPI 프로세스를 죽이지 않도록 한다.
5. **테스트 가능성**: 주기 루프 없이 단일 tick만 실행하는 `run_once()`를 노출해 smoke에서 직접 호출한다. `start(app)` / `stop()` 인터페이스는 FastAPI `lifespan` context로 묶는다.

## 2. 데이터 흐름

```
sensor-ingestor (기존)
    │ write_records(normalized) → sensor_readings insert
    ▼
Postgres/TimescaleDB sensor_readings (canonical)
    │
    ▼
AutomationRunner.tick() (신규, 주기 15s)
    ├─ _discover_zones(session): 활성 규칙의 zone_id 집합 (+ None → 전 zone)
    ├─ _build_zone_snapshot(session, zone_id, window_sec):
    │    latest sensor_readings per metric_name (within window)
    │    dict[AUTOMATION_SENSOR_KEYS → float]
    ├─ load_runtime_mode(path) → 전역 runtime_mode
    └─ evaluate_rules(session, runtime_mode=..., sensor_snapshot=..., zone_id=..., persist=True)
              → automation_rule_triggers insert
```

`AUTOMATION_SENSOR_KEYS`는 `ops-api/ops_api/api_models.py`에서 고정돼 있고 모두 `sensor_readings.metric_name`과 1:1로 일치한다(§2.1~§2.5). 따라서 snapshot은 단순 dict 조립이다.

## 3. 구성 가능 값 (Settings)

| 필드 | env 변수 | 기본값 | 의미 |
|---|---|---|---|
| `automation_enabled` | `OPS_API_AUTOMATION_ENABLED` | `true` | runner 기동 여부. 테스트/디버그에서 `false`로 끌 수 있다. |
| `automation_interval_sec` | `OPS_API_AUTOMATION_INTERVAL_SEC` | `15.0` | tick 주기. 0 이하면 disabled로 취급. |
| `automation_snapshot_window_sec` | `OPS_API_AUTOMATION_SNAPSHOT_WINDOW_SEC` | `120.0` | 최신 metric 조회 윈도우. 이 범위 밖의 metric은 `None`으로 처리돼 매칭 실패. |

## 4. 오류 처리

- 각 `tick` 시작 시 `session = session_factory()`를 새로 만든다.
- zone 단위 루프에서 예외가 나면 해당 zone만 `logger.warning`으로 기록하고 다음 zone 진행.
- `run_once()`는 예외를 re-raise 하지 않는다(상위 스케줄러 루프 유지). 단, 테스트 편의를 위해 `run_once(raise_on_error=True)` 옵션을 남긴다.
- cooldown/gate 로직은 evaluate_rules 내부에 남아 있고 runner는 snapshot 조립과 스케줄링만 담당한다.

## 5. FastAPI Lifespan 연결

`create_app()` 내부에 `@asynccontextmanager`로 `lifespan` 함수를 정의한다.

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    runner = AutomationRunner(session_factory, settings)
    if settings.automation_enabled and settings.automation_interval_sec > 0:
        await runner.start()
    try:
        yield
    finally:
        await runner.stop()
```

`runner.start()`는 `asyncio.create_task`로 tick 루프를 건다. `stop()`은 task.cancel + 완료 대기.

## 6. 검증 (Phase P-2 smoke)

`scripts/validate_ops_api_automation_runner.py`:

1. `create_app(settings_with_automation_disabled=True)`로 앱 부트. TestClient로 규칙 1건 POST (sensor_key=air_temp_c, operator=gt, threshold=30, gate=approval).
2. `sensor_readings` 테이블에 `zone_id=gh-01-zone-a`, `metric_name=air_temp_c`, `metric_value_double=32.0` 행 삽입.
3. `AutomationRunner(session_factory, settings).run_once()` 직접 호출.
4. `automation_rule_triggers` 조회: 1건, status=`approval_pending`, matched_value≈32.0.
5. 두 번째 `run_once()` 호출 → cooldown 유지 시 trigger 추가 1건 (`status=cooldown_skipped`).
6. 윈도우 밖 old reading → snapshot에서 `None` → no match 확인.
7. `OPS_API_AUTOMATION_ENABLED=false`로 lifespan 기동 시 runner task가 생성되지 않는지 검증.

## 7. 후속 단계

- **Phase P-2.5**: RealtimeBroker 이벤트 중 `execute` gate 규칙 대상 key (e.g., `ext_rainfall_mm`, `ext_wind_speed_m_s`)에 한해 즉시 tick 호출.
- **Phase P-3** (완료, 2026-04-18): `AutomationRuleTriggerRecord` 에 `reviewed_by`/`reviewed_at`/`review_reason` 추가, `POST /automation/triggers/{id}/approve|reject` 엔드포인트, 운영 runbook(`docs/automation_trigger_review_runbook.md`). Dispatch는 Phase Q에서 연결.
- **Phase Q**: `approved` trigger → `DecisionRecord + DeviceCommandRecord` 자동 flush. `AutomationRuleTriggerRecord ↔ DecisionRecord` FK 확장, shadow_window 리포트 편입.

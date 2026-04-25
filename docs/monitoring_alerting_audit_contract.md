# Monitoring, Alerting, Audit Contract

이 문서는 todo 13 모니터링/알람/감사 항목의 runtime 계약을 고정한다. 기준 runtime은 PostgreSQL/TimescaleDB only이며 SQLite smoke 또는 dashboard 경로는 사용하지 않는다.

## Logging Contract

### request log

- 저장 위치: `decisions.raw_output_json`, `decisions.zone_state_json`, `policy_events.payload_json`
- 필수 키: `request_id`, `farm_id`, `zone_id`, `task_type`, `runtime_mode`, `actor_id`, `received_at`, `source`
- LLM 요청은 `raw_output_json.parse_result`, `fallback_used`, `response_contract_errors`, `response_contract_warnings`를 함께 남긴다.
- 정책/운영 요청은 `policy_events.request_id`와 `payload.actor_id`로 추적한다.

### decision log

- 저장 위치: `decisions`, `policy_evaluations`, `operator_reviews`
- 필수 키: `decision_id`, `request_id`, `model_id`, `prompt_version`, `validated_output`, `citations`, `validator_reason_codes`, `created_at`
- `validated_output`은 LLM 결과가 아니라 policy output validator와 response contract 이후의 최종 판단이다.

### command log

- 저장 위치: `device_commands`
- 필수 키: `decision_id`, `command_kind`, `target_id`, `action_type`, `status`, `payload`, `adapter_result`, `created_at`
- 성공 status는 `acknowledged`, `state_updated`로 집계한다.
- 실패 status는 `rejected`, `dispatch_fault`, `failed`, `timeout`으로 집계한다.

### robot log

- 저장 위치: `robot_candidates`, `robot_tasks`
- 필수 키: `decision_id`, `zone_id`, `candidate_id`, `task_type`, `priority`, `approval_required`, `status`, `reason`, `target`, `payload`
- 로봇 제어 경로는 task envelope만 저장하고 실제 경로계획과 제어 로그는 robot controller 쪽 감사 로그가 담당한다.

### policy block log

- 저장 위치: `policy_events`, `policy_event_policy_links`, `device_commands.adapter_result.policy_event`
- 필수 키: `event_type`, `policy_result`, `policy_ids`, `reason_codes`, `dispatch_request`, `dispatch_result`
- `blocked`와 `approval_required`는 runtime gate blocker로 집계한다.

### sensor anomaly log

- 저장 위치: `sensor_readings`, `zone_state_snapshots`, `alerts`
- 필수 키: `measured_at`, `source_id`, `metric_name`, `quality_flag`, `transport_status`, `metadata_json`
- stale, missing, flatline, communication_loss, bad, blocked는 `stale_sensor_count`와 sensor anomaly alarm의 입력이다.

## Metrics Contract

API: `GET /monitoring/metrics?window_minutes=60`

| Metric | Source | Rule |
|---|---|---|
| sensor_ingest_rate_per_min | sensor_readings | window sensor metric row count / window minutes |
| stale_sensor_count | sensor_readings | anomaly quality_flag 또는 degraded transport_status source count |
| decision_latency_avg_ms | decisions.zone_state_json | source timestamp부터 decision.created_at까지 평균 |
| decision_latency_p95_ms | decisions.zone_state_json | source timestamp부터 decision.created_at까지 p95 |
| malformed_response_count | decisions.raw_output_json | parse failure, fallback, response contract error count |
| blocked_action_count | policy_events | blocked event 또는 blocked policy_result count |
| approval_pending_count | approvals, decisions | pending approval rows + approval mode evaluated decisions |
| command_success_rate | device_commands | acknowledged/state_updated / command count |
| robot_task_success_rate | robot_tasks | done/completed/success / robot task count |
| safe_mode_count | operator_overrides, device_commands | active safe_mode/emergency_stop + enter_safe_mode commands |

## Alarm Contract

API: `GET /monitoring/alarms?window_minutes=60`

| Alarm | Trigger | Severity |
|---|---|---|
| high_temperature | latest air_temp_c >= 32.0 | warning, critical at >= 35.0 |
| high_humidity | latest rh_pct >= 90.0 | warning |
| sensor_anomaly | stale_sensor_count > 0 | warning |
| device_unresponsive | command_failure_count > 0 | critical |
| policy_block_spike | blocked_action_count >= 3 in window | warning |
| decision_failure | malformed_response_count > 0 | warning |
| robot_safety | robot safety policy event or blocked robot task > 0 | critical |
| safe_mode_entry | safe_mode_count > 0 | critical |

Alarms are computed from operational tables and returned as active runtime indicators. Persistent alert rows are still stored in `alerts` when a decision or automation dispatch creates an operator-facing alert.

## Operator Override Audit

API:

- `POST /operator/overrides`
- `GET /operator/overrides?zone_id=...&active_only=true`

Storage:

- `operator_overrides`: manual override, safe mode, emergency stop, operator lock events
- `policy_events`: each override also writes an `operator_override` event with reason code `operator_<type>_<state>`

Required fields:

- `target_scope`: system, zone, device, robot
- `target_id`: system, zone id, device id, or robot target id
- `override_type`: manual_override, safe_mode, emergency_stop, operator_lock
- `override_state`: active or cleared
- `actor_id`: authenticated actor from API auth context
- `reason`: operator reason
- `payload`: optional structured context

## Dashboard Contract

`GET /dashboard/data` includes:

- `summary.sensor_ingest_rate_per_min`
- `summary.stale_sensor_count`
- `summary.decision_latency_avg_ms`
- `summary.malformed_response_count`
- `summary.command_success_rate`
- `summary.robot_task_success_rate`
- `summary.operator_override_active_count`
- `summary.monitoring_alarm_count`
- `monitoring.metrics`
- `monitoring.alarms`
- `operator_overrides`

## Verification

- `python3 scripts/validate_monitoring_alerting_contract.py`
- `python3 -m py_compile ops-api/ops_api/app.py ops-api/ops_api/models.py ops-api/ops_api/api_models.py ops-api/ops_api/auth.py`
- `python3 scripts/run_phase_p_quality_gate.py --skip-postgres-smoke --no-env`

# System Schema Design

이 문서는 `todo.md`의 `#4. 시스템 스키마 설계` 항목을 기준으로, 현재 저장소의 상위 계약 스키마를 하나의 canonical set으로 정리한다.

## 1. Canonical Schema Set

| 영역 | canonical schema | 연결 문서 / 샘플 |
| --- | --- | --- |
| zone state | `schemas/state_schema.json` | `schemas/feature_schema.json`, `schemas/sensor_quality_schema.json`, `data/examples/zone_state_payload_samples.jsonl` |
| AI action payload | `schemas/action_schema.json` | `data/examples/action_recommendation_samples.jsonl` |
| decision envelope | `schemas/decision_schema.json` | `data/examples/decision_payload_samples.jsonl` |
| common domain models | `schemas/domain_models_schema.json` | `ops-api/ops_api/models.py` |
| execution command | `schemas/device_command_request_schema.json` | `docs/execution_gateway_command_contract.md`, `data/examples/device_command_request_samples.jsonl` |
| override transition | `schemas/control_override_request_schema.json` | `docs/execution_gateway_override_contract.md`, `data/examples/control_override_request_samples.jsonl` |
| event envelope | `schemas/system_event_schema.json` | `data/examples/system_event_samples.jsonl` |

## 2. 공통 도메인 모델

공통 도메인 모델의 source of truth는 `ops-api/ops_api/models.py`와 schema layer를 함께 본다.

- `Zone`: `zone_id`, `zone_type`, `priority`, `description`, `metadata`
- `Sensor`: `sensor_id`, `zone_id`, `sensor_type`, `measurement_fields`, `raw_sample_seconds`, `ai_aggregation_seconds`, `model_profile`, `protocol`
- `Device`: `device_id`, `zone_id`, `device_type`, `model_profile`, `controller_id`, `control_mode`, `supported_action_types`
- `Constraint`: `constraint_id`, `severity`, `summary`, `source`, `policy_ids`
- `Decision`: `decision_id`, `request_id`, `task_type`, `runtime_mode`, `status`, `model_id`, `prompt_version`, `audit_refs`
- `Action`: `action_id`, `action_type`, `target`, `parameters`, `risk_level`, `approval_required`
- `RobotCandidate`: `candidate_id`, `zone_id`, `candidate_type`, `priority`, `status`, `target`, `summary`
- `RobotTask`: `task_type`, `candidate_id`, `priority`, `approval_required`, `reason`, `target`

`Zone/Sensor/Device/Constraint/RobotCandidate/RobotTask`는 `schemas/domain_models_schema.json`에서 재사용 가능한 `$defs`로 고정하고, `Decision`과 `Action`은 각각 `schemas/decision_schema.json`, `schemas/action_schema.json`을 canonical model로 둔다.

## 3. 상태 스키마 설계

상태 스키마는 `schemas/state_schema.json`을 기준으로 한다.

- `current_state`: `environment`, `rootzone`, `outside_weather`
- `derived_features`: 추세, VPD, DLI, 누적 관수량 등 파생값. `schemas/feature_schema.json` 사용
- `device_status`: `device_id`, `device_type`, `mode`, `state`, `last_command_id`, `last_readback_at`, `health`
- `constraints`: top-level field name은 `active_constraints`로 유지하고, 항목 구조는 `constraint` model을 재사용
- `sensor_quality`: `schemas/sensor_quality_schema.json` 사용
- `weather_context`: 별도 top-level object를 두지 않고 `current_state.outside_weather`를 canonical weather context로 사용
- `growth_stage`: `pre_planting`부터 `season_end`까지 enum을 `state_schema.json`에서 고정
- enum 값: crop / device_type / mode / quality_flag / constraint severity 등은 모두 schema enum으로 명시

예제 payload는 `data/examples/zone_state_payload_samples.jsonl`에 두고, `scripts/validate_zone_state_payloads.py`로 schema-level 필수 필드와 cross-field 규칙을 확인한다.

## 4. 액션 / 결정 스키마 설계

액션 스키마는 `schemas/action_schema.json`을 기준으로 한다.

- `action_type`: `observe_only`, `create_alert`, `request_human_check`, `adjust_fan`, `adjust_shade`, `adjust_vent`, `short_irrigation`, `adjust_fertigation`, `adjust_heating`, `adjust_co2`, `pause_automation`, `enter_safe_mode`, `create_robot_task`, `block_action`
- 장치별 parameter schema는 저수준 setpoint bounds와 함께 `docs/device_command_mapping_matrix.md`, `data/examples/sensor_catalog_seed.json`, `schemas/device_command_request_schema.json`으로 연결
- irrigation / shade / vent / fan / heating / co2는 모두 `recommended_action.parameters`를 통해 device-specific parameter contract를 갖고, 실제 write 전에는 `execution-gateway`가 재검증
- robot task schema와 follow-up schema는 `schemas/action_schema.json`의 `$defs.robot_task`, `$defs.follow_up`를 canonical contract로 사용

결정 스키마는 `schemas/decision_schema.json`으로 분리한다.

- zone state snapshot과 action payload를 한 envelope에 묶는다.
- policy summary / validator summary / approval request / alert summary / audit refs를 decision 수준에서 기록한다.
- generated device command request와 robot candidate / robot task 결과를 trace 가능하게 남긴다.

예제 payload는 `data/examples/decision_payload_samples.jsonl`, 검증 스크립트는 `scripts/validate_decision_payloads.py`를 사용한다.

## 5. 이벤트 스키마 설계

운영 이벤트는 `schemas/system_event_schema.json`의 단일 envelope로 통일한다.

- `sensor.snapshot.updated`
- `zone.state.updated`
- `action.requested`
- `action.blocked`
- `action.executed`
- `robot.task.created`
- `robot.task.failed`
- `alert.created`
- `approval.requested`

모든 이벤트는 `event_id`, `event_type`, `emitted_at`, `source_service`, `farm_id`, `severity`, `payload`를 공통 필드로 갖는다.

`payload`는 event type마다 다른 contract를 가지며, action/decision/state/device command schema를 재사용한다.

예제 payload는 `data/examples/system_event_samples.jsonl`, 검증 스크립트는 `scripts/validate_system_events.py`를 사용한다.

## 6. Validation Commands

문서/샘플 변경 후 기본 검증 명령은 아래와 같다.

- `python3 scripts/validate_zone_state_payloads.py`
- `python3 scripts/validate_decision_payloads.py`
- `python3 scripts/validate_system_events.py`
- `python3 scripts/validate_device_command_requests.py`
- `python3 scripts/validate_control_override_requests.py`
- `rg "TODO|TBD" README.md PROJECT_STATUS.md AI_MLOPS_PLAN.md schedule.md todo.md docs/system_schema_design.md`

## 7. Completion Mapping

`todo.md`의 `#4`는 아래 기준으로 완료 처리한다.

- `4.1 공통 도메인 모델`: `schemas/domain_models_schema.json`, `schemas/action_schema.json`, `schemas/decision_schema.json`
- `4.2 상태 스키마 설계`: `schemas/state_schema.json`, `schemas/feature_schema.json`, `schemas/sensor_quality_schema.json`, `data/examples/zone_state_payload_samples.jsonl`
- `4.3 액션 스키마 설계`: `schemas/action_schema.json`, `schemas/decision_schema.json`, `docs/device_command_mapping_matrix.md`
- `4.4 이벤트 스키마 설계`: `schemas/system_event_schema.json`, `data/examples/system_event_samples.jsonl`

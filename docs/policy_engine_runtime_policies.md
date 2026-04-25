# Policy Engine Runtime Policies

이 문서는 todo 8번 정책 엔진 구현 범위를 닫기 위한 runtime 정책 DSL과 기본 정책 catalog를 고정한다.

## 목적

- LLM 출력 validator가 놓친 실행 직전 위험을 policy-engine에서 다시 평가한다.
- 파일 기반 seed와 ops-api DB PolicyRecord 기반 source가 같은 rule shape을 사용한다.
- PostgreSQL runtime에서는 SQLite 대체 없이 policies 테이블의 enabled/source_version 변경을 다음 precheck에 즉시 반영한다.

## 정책 카테고리

| category | stage | 기본 결과 | 목적 |
|---|---|---|---|
| hard block | hard_block | blocked | 사람, 장치, 작물에 즉시 위험한 명령 차단 |
| approval | approval | approval_required | 고위험 액션을 승인 큐로 전환 |
| range limit | range_limit | blocked 또는 approval_required | setpoint와 duration 안전 범위 검증 |
| scheduling | scheduling | approval_required | 시간대/운영 모드에 따른 자동 실행 제한 |
| sensor quality | sensor_quality | blocked | 센서 품질 불량 시 자동 제어 차단 |
| robot safety | robot_safety | blocked | 작업자/통로/clearance 불확실 시 로봇 작업 차단 |

## DSL 필드

POL-* 규칙의 runtime DSL은 enforcement_json 안에 둔다. 이유는 ops-api PolicyRecord가 trigger_flags_json과 enforcement_json만 저장하므로, 파일 source와 DB source를 같은 evaluator로 처리하기 위해서다.

필수 구조는 rule_id, stage, severity, enabled, description, trigger_flags, enforcement로 구성한다. enforcement 안에는 mode, outcome, category, scope, target_action_types, condition, reason_code, message를 둔다.

## Condition 표현

- 단일 조건: field, operator, value를 사용한다.
- 복합 조건: all, any, not을 사용한다.
- field는 request root 또는 dotted path를 지원한다. 예: parameters.duration_seconds.
- between은 min_value/max_value를 사용하고, 야간처럼 범위가 자정을 넘으면 wrap=true를 둔다.
- contains는 list/string/dict key 포함을 확인한다.

지원 operator:

- exists, missing
- truthy, falsy
- eq, ne
- gt, gte, lt, lte
- between
- in, not_in
- contains

## 기본 정책

현재 seed catalog에는 다음 POL-* 정책을 포함한다.

| policy_id | category | 결과 | 대상 |
|---|---|---|---|
| POL-HARD-SENSOR-QUALITY | sensor_quality | blocked | device control |
| POL-HARD-OVERWET-IRRIGATION | hard_block | blocked | short_irrigation, adjust_fertigation |
| POL-HARD-WIND-VENT | hard_block | blocked | adjust_vent |
| POL-ROBOT-WORKER-SAFETY | robot_safety | blocked | create_robot_task |
| POL-HARD-DEVICE-READBACK | hard_block | blocked | all actions |
| POL-APPROVAL-HIGH-RISK | approval | approval_required | fertigation, heating, co2, robot task |
| POL-SCHED-NIGHT-IRRIGATION | scheduling | approval_required | short_irrigation |
| POL-RANGE-IRRIGATION-PULSE | range_limit | blocked | short_irrigation duration 30~900s |
| POL-RANGE-SETPOINT-DELTA | range_limit | approval_required | large setpoint delta |

## 검증

- scripts/validate_policy_engine_runtime_policies.py가 9개 기본 정책과 evaluate_device_policy_precheck 통합을 검증한다.
- scripts/validate_policy_engine_precheck.py는 기존 HSV precheck와 POL-* runtime result 병합을 유지한다.
- scripts/run_phase_p_quality_gate.py는 policy_engine_runtime_policy_smoke를 포함한다.

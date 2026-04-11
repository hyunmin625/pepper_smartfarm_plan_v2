# Execution Gateway Override Contract

이 문서는 `execution-gateway`가 일반 장치 명령과 분리해서 처리해야 하는 override 요청 형식을 정의한다.

## 1. 목적

- `emergency stop`, `manual override`, `safe mode`, `auto mode re-entry`를 일반 `device_command_request`와 분리한다.
- 장치별 write 요청과 제어 상태 전환 요청을 다른 검증 경로로 처리한다.
- `estop`과 `manual_override`는 장치 setpoint 변경과 달리 zone/site 수준 state transition으로 취급한다.

## 2. override 유형

- `emergency_stop_latch`
- `emergency_stop_reset_request`
- `manual_override_start`
- `manual_override_release`
- `safe_mode_entry`
- `auto_mode_reentry_request`

## 3. 핵심 규칙

1. `emergency_stop_latch`는 즉시 실행 가능한 hard stop 요청이다.
2. `manual_override_start`와 `manual_override_release`는 반드시 `operator`가 요청해야 한다.
3. `emergency_stop_reset_request`와 `auto_mode_reentry_request`는 `approval_context.approval_status=approved`가 필요하다.
4. `auto_mode_reentry_request`는 `state_sync_completed=true`, `manual_override_cleared=true`, `estop_cleared=true`가 모두 필요하다.
5. override 요청은 `scope_type/site|zone|device`와 `scope_id`를 반드시 포함한다.

## 4. 연결 파일

- schema: `schemas/control_override_request_schema.json`
- samples: `data/examples/control_override_request_samples.jsonl`
- validator: `scripts/validate_control_override_requests.py`
- safety baseline: `docs/safety_requirements.md`

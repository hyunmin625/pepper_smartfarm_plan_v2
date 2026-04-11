# Execution Dispatcher Runtime

이 문서는 `execution-gateway`가 preflight 통과 요청을 실제 dispatch하는 런타임 구조를 정리한다.

## 1. 현재 구현 범위

- `execution-gateway/execution_gateway/dispatch.py`
- `execution-gateway/execution_gateway/state.py`
- `scripts/validate_execution_dispatcher.py`
- `scripts/validate_execution_safe_mode.py`
- `execution-gateway/demo.py`

현재 dispatcher는 `device_command`와 `control_override`를 서로 다른 실행 경로로 분리한다.

## 2. device_command dispatch

순서:

1. `guards.evaluate_device_command()`로 range, duplicate, cooldown, approval, policy 재검사
2. `ControlStateStore`의 `estop/manual_override/safe_mode` 상태로 추가 차단
3. 통과 시 `plc-adapter` 호출
4. adapter 결과를 runtime fault tracker에 반영
5. timeout/fault가 연속되면 zone/site scope를 `safe_mode_active`로 전환
6. adapter 결과를 audit log에 기록
7. `acknowledged`면 cooldown key 활성화

지원 adapter:

- `mock`
- `plc_tag_modbus_tcp`

현재 기본 demo/validator는 `mock` adapter를 사용한다.

## 3. control_override dispatch

override는 장치 write가 아니라 제어 상태 전이로 처리한다.

- `emergency_stop_latch`
- `emergency_stop_reset_request`
- `manual_override_start`
- `manual_override_release`
- `safe_mode_entry`
- `auto_mode_reentry_request`

전이는 `ControlStateStore`에 저장되며, 이후 장치 명령 dispatch 시 차단 조건으로 재사용된다.

## 4. runtime fault -> safe mode

- `execution-gateway/execution_gateway/state.py`의 `RuntimeFaultTracker`가 scope별 연속 timeout/fault를 기록한다.
- 현재 threshold는 `2`이며, 같은 zone/site에서 timeout 또는 fault가 연속 두 번 발생하면 `safe_mode_active=true`로 전환한다.
- `safe_mode_active`가 켜지면 이후 device command는 preflight 뒤 `ControlStateStore` 단계에서 추가로 차단된다.
- 이 경로는 `scripts/validate_execution_safe_mode.py`에서 heater timeout 2회 후 fan 요청 차단 시나리오로 검증한다.

## 5. audit log

기본 경로:

- `artifacts/runtime/execution_gateway/dispatch_audit.jsonl`

환경 변수:

- `EXECUTION_GATEWAY_AUDIT_LOG_PATH`

최소 기록 필드:

- `recorded_at`
- `request_id`
- `request_kind`
- `status`
- `allow_dispatch`
- `reasons`
- `normalized`
- `preflight`
- `adapter_result` 또는 `state_transition`

## 6. 다음 후속 작업

1. `mock` 대신 실제 `plc_tag_modbus_tcp` transport 연결
2. cooldown 만료와 duplicate window를 시간 기반으로 고도화
3. approval/rejection 결과를 별도 approval store와 연결
4. audit log를 backend DB와 운영 UI에서 조회 가능하게 연결

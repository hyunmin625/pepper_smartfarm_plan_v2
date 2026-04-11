# PLC Modbus Governance

이 문서는 `11.1 프로토콜 설계`와 `11.4 실행 검증`의 공통 기준을 정리한다.

## 1. 현재 통신 방식 기준

- 온실 제어기 연동 기본 경로는 `Modbus TCP`를 사용한다.
- controller endpoint 형식은 `modbus-tcp://host:502?unit_id=1&timeout=1.0`를 기준으로 한다.
- `OPC UA`는 향후 확장 후보이며, 현재 저장소 기준 기본 transport는 아니다.

## 2. register/write 안전 규칙

- write 가능 table은 `holding_register`, `coil`만 허용한다.
- `input_register`, `discrete_input`에는 절대 write하지 않는다.
- 장치 명령은 `Device Profile.parameter_specs` 검증을 통과한 뒤에만 write한다.
- 같은 요청에서 여러 raw register를 한 번에 바꾸지 않고, `device_id` 기준 단일 command channel을 사용한다.
- 난방, CO2, 양액, 자동모드 복귀, estop reset은 승인 완료 후에만 write 가능하다.
- timeout 또는 readback mismatch 뒤에는 동일 명령을 무제한 재시도하지 않는다.

## 3. readback 검증 방식

- write 후 반드시 readback을 다시 읽는다.
- 성공 판정은 `DeviceProfile.ack_policy.success_conditions`를 따른다.
- 기본 success condition:
  - `run_state_matches`
  - `position_pct_within_tolerance`
  - `speed_pct_within_tolerance`
  - `dose_pct_within_tolerance`
  - `stage_matches`
  - `recipe_stage_matches`
- readback이 기대값과 다르면 `acknowledged`가 아니라 `fault` 또는 `timeout`으로 처리한다.

## 4. 장애 코드 기준

- `connect_failed`
- `endpoint_not_connected`
- `write_timeout`
- `read_timeout`
- `ack_mismatch`
- `device_fault`
- `unsupported_table`
- `unsupported_register_value`
- `policy_blocked`
- `manual_override_state_active`
- `safe_mode_active`
- `estop_active`

실제 vendor fault code는 장치 readback의 `fault_code` 필드에 그대로 보존하고, 위 코드는 adapter/execution-gateway 내부 상태 코드로 사용한다.

## 5. 부분 성공 / rollback 기준

- 단일 `device_id` 요청은 부분 성공을 허용하지 않는다.
- multi-device orchestration은 상위 계층에서 분해해 개별 요청으로 실행한다.
- rollback 후보:
  - `adjust_fan`
  - `adjust_shade`
  - `adjust_vent`
  - `short_irrigation` 전 대기 단계
- rollback 비권장:
  - `adjust_fertigation`
  - `adjust_co2`
  - `adjust_heating`
  - `auto_mode_reentry_request`

## 6. safe mode 전환 조건

- 장치 timeout이 연속 발생
- readback mismatch가 연속 발생
- 핵심 controller endpoint 연결 상실
- must-have sensor 품질 `bad`
- estop 또는 manual override active

이 조건은 `execution-gateway`와 `policy-engine`의 공통 입력으로 사용한다.

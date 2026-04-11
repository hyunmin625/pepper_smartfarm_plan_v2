# Approval Governance

이 문서는 `10.3 승인 체계`의 기준 문서다. 목적은 `execution-gateway`가 액션 위험도, 승인자 역할, timeout, 거절 fallback을 일관되게 적용하도록 하는 것이다.

## 1. 위험도 분류

### 저위험 액션

- `pause_automation`
- `create_alert`
- `request_human_check`
- `observe_only`

원칙:

- 즉시 실행 가능
- 운영 로그만 남기고 별도 승인 불필요
- 단, 사람 감지/정비 중인 장치에 대한 덮어쓰기 명령은 불가

### 중위험 액션

- `adjust_fan`
- `adjust_shade`
- `adjust_vent`
- `short_irrigation`
- `safe_mode_entry`
- `manual_override_start`
- `manual_override_release`

원칙:

- 범위 제한과 cooldown을 반드시 적용
- 야간, 장마, 강풍, 센서 품질 `partial`이면 승인 요구 가능
- 동일 zone에 15분 이내 연속 재요청 시 운영자 확인 우선

### 고위험 액션

- `adjust_heating`
- `adjust_co2`
- `adjust_fertigation`
- `create_robot_task`
- `auto_mode_reentry_request`
- `emergency_stop_reset_request`
- 배합 recipe 변경
- 장시간 관수 전략 변경

원칙:

- 기본 승인 필수
- 승인 없이 자동 dispatch 금지
- 실행 전 policy snapshot과 장치 readback을 다시 검증

## 2. 승인자 역할

- `operator`
  - 저위험/중위험 승인
  - 현장 확인, 수동 전환, 장치 재동기화
- `shift_lead`
  - 고위험 액션 1차 승인
  - 야간/주말 운영 판단
- `facility_manager`
  - 난방, CO2, 양액 recipe, 재가동 승인
- `safety_manager`
  - 로봇 작업구역, estop reset, 사람 접근 관련 승인

## 3. 승인 UI 요구사항

- 요청별 `request_id`, `zone_id`, `device_id`, `action_type`, `parameters`
- 위험도와 승인 필요 사유
- 현재 `sensor_quality`, `policy_result`, `recent_events`, `readback`
- RAG citation 또는 SOP 근거 링크
- 승인/거절 버튼과 사유 입력
- timeout 남은 시간 표시
- 실행 후 결과와 ack/readback 표시

## 4. 승인 timeout 정책

- 저위험: timeout 없음
- 중위험: `10분`
- 고위험: `5분`
- `auto_mode_reentry_request`: `3분`
- `emergency_stop_reset_request`: `3분`

timeout 시 기본 동작:

- 요청 상태 `expired`
- dispatch 금지
- 운영자에게 재검토 요청

## 5. 거절 시 fallback

- `adjust_heating`, `adjust_co2`, `adjust_fertigation` 거절
  - `request_human_check`
  - 현재 상태 유지
- `short_irrigation` 거절
  - 즉시 재시도 금지
  - 배지/배액 재측정 요청
- `auto_mode_reentry_request` 거절
  - `safe_mode` 유지
  - 상태 재동기화 체크리스트 재수행
- `create_robot_task` 거절
  - 작업 보류
  - 사람 접근 여부와 후보 품질 재확인

## 6. 구현 연결

- `docs/safety_requirements.md`
- `docs/execution_gateway_flow.md`
- `docs/execution_dispatcher_runtime.md`
- `schemas/device_command_request_schema.json`
- `schemas/control_override_request_schema.json`

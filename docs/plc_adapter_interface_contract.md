# PLC Adapter Interface Contract

이 문서는 `plc-adapter`가 `Device Profile`을 이용해 논리 명령을 PLC/장치 프로토콜로 변환하는 최소 인터페이스를 정의한다.

## 1. 입력

- `device_id`
- `profile_id`
- `action_type`
- `parameters`
- `request_id`
- `issued_at`

실제 구현에서는 `CommandRequest`와 `CommandResult`를 표준 형태로 사용한다.

## 2. 핵심 메서드

- `connect()`: 연결 초기화
- `health()`: 연결 상태와 마지막 오류 반환
- `validate_command(profile_id, action_type, parameters)`: 프로필 범위 검증
- `build_command_payload(profile, action_type, parameters)`: encoder를 사용해 write payload 생성
- `write_command(device_id, profile_id, action_type, parameters)`: 실제 write 수행
- `readback(device_id, profile_id)`: readback 필드 조회
- `evaluate_ack(profile_id, readback, expected)`: ack policy와 success condition 평가

## 3. 반환 구조

write 결과는 아래 필드를 포함한다.

- `request_id`
- `device_id`
- `profile_id`
- `status`: `accepted`, `acknowledged`, `timeout`, `rejected`, `fault`
- `payload`
- `readback`
- `latency_ms`
- `failure_reason`

## 4. 규칙

1. 명령 생성 전 `parameter_specs`와 `supported_action_types`를 검증한다.
2. `safety_interlocks`가 active이면 write를 보내기 전에 `rejected` 처리한다.
3. ack가 필요한 profile은 `ack_timeout_seconds` 안에 readback success condition을 만족해야 한다.
4. `plc-adapter`는 논리 명령을 직접 해석하지 않고 `Device Profile`의 encoder/decoder 식별자를 사용한다.
5. `profile_id`는 `data/examples/sensor_catalog_seed.json`의 `model_profile`과 일치해야 한다.
6. `supported_action_types`는 `schemas/action_schema.json`의 `action_type` enum과 동기화한다.
7. runtime payload의 `write_channel_ref`, `read_channel_refs`는 `site override` binding이 있으면 그 값을 우선 사용한다.

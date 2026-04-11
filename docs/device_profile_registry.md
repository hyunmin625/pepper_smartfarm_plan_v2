# Device Profile Registry

이 문서는 `plc-adapter`가 장치별 PLC 주소 체계와 명령 형식을 직접 하드코딩하지 않도록 `Device Profile` registry를 관리하는 기준을 정의한다. 핵심은 장치 타입, 제어 방식, 인터록, readback 규칙, PLC 매핑을 하나의 프로필로 묶고, 실제 장치 인스턴스는 해당 프로필을 참조만 하도록 하는 것이다.

## 1. 목적

- `model_profile`를 단순 설명 문자열이 아니라 실행 계약의 key로 사용한다.
- `execution-gateway`, `plc-adapter`, `state-estimator`가 같은 장치 의미를 공유한다.
- vendor 변경이나 PLC 주소 변경이 생겨도 인스턴스 목록보다 profile registry만 먼저 바꾸면 된다.

## 2. 관리 단위

각 `Device Profile`은 다음을 포함한다.

- `profile_id`: 장치 인스턴스가 참조하는 고유 키
- `device_type`: fan, vent, irrigation_valve 같은 논리 타입
- `protocol`, `control_mode`, `command_family`
- `supported_action_types`
- `parameter_specs`: 허용 파라미터, 범위, 단위
- `readback_fields`: readback에서 반드시 읽어야 하는 상태
- `safety_interlocks`
- `ack_policy`: ack 필요 여부, timeout, readback 검증 방식
- `mapping`: PLC/OPC UA write/read 채널과 encoder/decoder 식별자

## 3. 적용 규칙

1. `data/examples/sensor_catalog_seed.json`의 각 device `model_profile`은 registry의 `profile_id`와 일치해야 한다.
2. `plc-adapter`는 `device_id`만 보고 동작하지 않고, 항상 `Device Profile`을 먼저 resolve한 뒤 write/readback을 수행한다.
3. `execution-gateway`의 range validation은 `parameter_specs`를 기준으로 한다.
4. 인터록, ack timeout, readback success 조건은 인스턴스별 override보다 profile 기본값을 우선한다.

## 4. 프로필 계층

- `logical profile`: 장치 의미와 허용 액션
- `mapping profile`: PLC/OPC UA 주소, encoder/decoder
- `site override`: 특정 현장 address map, hold time, scaling

현재 seed는 `logical + default mapping`을 함께 두고, 실제 현장 채널은 `docs/plc_site_override_map.md`와 `data/examples/device_site_override_seed.json`에서 분리 관리한다.

## 5. 분리 기준

아래 조건 중 하나라도 다르면 별도 profile로 분리한다.

- `device_type`이 다르다.
- `safety_interlocks`가 다르다.
- `ack_policy`나 readback success condition이 다르다.
- PLC write/read channel 구조가 다르다.

예를 들어 zone 관수밸브는 `valve_open_close_feedback`, 원수 메인 밸브는 `source_water_valve_feedback`으로 분리한다. 둘 다 binary valve처럼 보이지만 인터록과 현장 의미가 다르기 때문이다.

## 6. 연결 파일

- `schemas/device_profile_registry_schema.json`
- `data/examples/device_profile_registry_seed.json`
- `docs/plc_site_override_map.md`
- `data/examples/device_site_override_seed.json`
- `scripts/validate_device_profile_registry.py`
- `plc-adapter/plc_adapter/device_profiles.py`
- `plc-adapter/plc_adapter/interface.py`

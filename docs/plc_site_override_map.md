# PLC Site Override Map

이 문서는 `Device Profile`의 논리 계약과 실제 현장 PLC 채널을 분리하기 위한 `site override address map` 기준을 정의한다.

## 1. 목적

- `Device Profile`은 장치 의미, 허용 액션, 인터록, ack 규칙만 관리한다.
- 실제 PLC tag/register/node는 현장별 `site override` 파일에서 관리한다.
- 장비 교체, PLC 재배선, controller 분리 시 profile 자체를 바꾸지 않고 binding만 수정한다.

## 2. 관리 단위

각 binding은 다음을 포함한다.

- `device_id`
- `profile_id`
- `controller_id`
- `protocol`
- `write_channel_ref`
- `read_channel_refs`
- 선택적 `command_encoder`, `readback_decoder`

controller는 `controller_id`, `protocol`, `endpoint`, `role`을 가진다. `endpoint`는 실제 접속 정보가 아니라 placeholder 또는 비식별 명칭만 커밋한다.

## 3. 적용 규칙

1. `device_id`는 `data/examples/sensor_catalog_seed.json`의 device와 1:1로 대응한다.
2. `profile_id`는 catalog의 `model_profile`과 일치해야 한다.
3. binding `protocol`은 catalog device와 controller protocol과 일치해야 한다.
4. `write_channel_ref`와 `read_channel_refs`는 실행 시 payload에 주입되며, profile 기본 `mapping`보다 우선한다.
5. 실제 IP, slave id, register 주소, OPC UA 인증정보는 커밋하지 않는다.
6. `write_channel_ref`와 `read_channel_refs`는 `plc_tag://{controller_id}/...` 형식을 유지해야 하며, ref 안의 controller id는 binding `controller_id`와 일치해야 한다.

## 4. 현재 seed 범위

- `data/examples/device_site_override_seed.json`은 `gh-01` 예시 binding만 담는다.
- 값은 실제 현장 주소가 아닌 placeholder tag path다.
- 구조 검증은 `scripts/validate_device_site_overrides.py`에서 수행한다.
- 실제 Modbus register 주소는 `docs/plc_channel_address_registry.md`와 별도 registry에서 관리한다.
- 실제 endpoint override는 `docs/plc_runtime_endpoint_config.md`와 환경 변수로 주입한다.

## 5. 연결 파일

- `schemas/device_site_override_schema.json`
- `data/examples/device_site_override_seed.json`
- `scripts/validate_device_site_overrides.py`
- `docs/plc_runtime_endpoint_config.md`
- `docs/plc_channel_address_registry.md`
- `plc-adapter/plc_adapter/site_overrides.py`
- `plc-adapter/plc_adapter/resolver.py`

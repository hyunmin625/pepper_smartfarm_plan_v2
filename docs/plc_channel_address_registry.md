# PLC Channel Address Registry

이 문서는 `plc-adapter`가 logical channel ref를 실제 Modbus 주소로 바꾸는 관리 기준을 정의한다.

## 1. 목적

- `device_site_override_seed.json`은 `device_id -> controller_id -> channel_ref`만 관리한다.
- 실제 레지스터 주소는 별도 registry에서 관리한다.
- adapter는 `channel_ref`를 transport용 주소 key로 변환한 뒤 write/readback을 수행한다.

## 2. 산출물

- schema: `schemas/device_channel_address_registry_schema.json`
- seed: `data/examples/device_channel_address_registry_seed.json`
- builder: `scripts/build_device_channel_address_registry.py`
- validator: `scripts/validate_device_channel_address_registry.py`
- loader: `plc-adapter/plc_adapter/channel_address_registry.py`

## 3. 구조

각 channel entry는 아래 필드를 가진다.

- `channel_ref`: `plc_tag://{controller_id}/...`
- `controller_id`
- `protocol`
- `access`: `write` 또는 `read`
- `table`: `holding_register`, `input_register`, `discrete_input`, `coil`
- `address`: 실제 Modbus 주소 번호
- `data_type`: `boolean`, `uint16` 등

현재 seed는 계획 단계용 placeholder 주소이지만, 구조는 실주소와 동일하게 유지한다.

## 4. 운영 규칙

- `channel_ref`의 controller id와 registry의 `controller_id`는 반드시 같아야 한다.
- 같은 `controller_id + table + address + bit_index` 조합은 중복되면 안 된다.
- site override에 존재하는 모든 write/read channel ref는 address registry에 있어야 한다.
- 실제 주소 확보 후에는 seed를 교체하되 `channel_ref`는 바꾸지 않는다.

## 5. 현재 adapter 연결점

- `PlcTagModbusTcpAdapter`는 payload에 아래를 함께 남긴다.
  - `write_channel_address`
  - `read_channel_addresses`
  - `transport_write_values`
  - `transport_mirror_read_values`
  - `transport_read_refs`

이 구조를 기준으로 이후 실제 TCP/Modbus client를 붙인다.

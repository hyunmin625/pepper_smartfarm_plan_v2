# PLC Tag Modbus TCP Adapter

이 문서는 현재 `plc-adapter`에 추가된 `plc_tag_modbus_tcp` skeleton의 역할을 정리한다.

## 1. 범위

- `device_id` 기준 command 실행
- catalog/profile/site override resolve
- channel ref -> address registry resolve
- encoder 기반 write payload 생성
- transport 기반 write/readback
- timeout 시 reconnect 후 retry
- ack policy 평가와 result mapping

현재 단계에서는 실제 PLC 네트워크 대신 in-memory transport를 사용한다.

## 2. 구성 요소

- `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`
  - adapter runtime
- `plc-adapter/plc_adapter/transports.py`
  - `PlcTagTransport`, `InMemoryPlcTagTransport`
- `plc-adapter/plc_adapter/codecs.py`
  - encoder/decoder registry
- `plc-adapter/plc_adapter/channel_address_registry.py`
  - logical ref -> transport address resolver
- `plc-adapter/plc_adapter/runtime_config.py`
  - controller endpoint env override resolver

## 3. 동작 순서

1. `device_id`로 catalog/profile/site override를 resolve한다.
2. `parameter_specs`와 `supported_action_types`를 검증한다.
3. encoder가 logical `write_values`, `mirror_read_values`를 만든다.
4. address registry가 이를 transport ref 기준 payload로 변환한다.
5. transport가 write를 수행한다.
6. readback을 읽고 decoder가 논리 필드로 변환한다.
7. profile `ack_policy.success_conditions`로 성공 여부를 판정한다.

## 4. 현재 제한

- 실제 Modbus TCP client는 아직 미연결이다.
- 현재 address registry는 placeholder 주소지만 구조는 실주소와 동일하다.
- codec은 현재 seed profile에 필요한 encoder/decoder만 포함한다.
- 장애 코드는 transport/PLC vendor별 규격이 확정되면 추가한다.

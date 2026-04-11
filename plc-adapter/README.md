# PLC Adapter Skeleton

이 디렉터리는 `Device Profile`을 이용해 논리 명령을 PLC/장치 프로토콜로 바꾸는 `plc-adapter`의 준비 코드다.

## 포함 범위

- `Device Profile` registry 로드
- registry version 기반 profile 집합 관리
- site override address map 로드
- runtime endpoint override 로드
- channel ref -> Modbus address registry 로드
- `device_id -> profile -> controller/channel` resolver
- `plc_tag_modbus_tcp` adapter skeleton
- transport / codec registry 분리
- profile 기반 명령 파라미터 검증
- profile 기반 ack success condition 평가
- profile 기반 write payload 생성
- timeout / retry / health check 포함 write/readback 흐름 검증
- logical ref -> transport ref 변환 검증
- optional `PymodbusTcpTransport` fake validation

## 실행 예시

```bash
python3 plc-adapter/demo.py
python3 scripts/validate_plc_modbus_transport.py
```

demo는 `device_id`만 받아 catalog/profile/site override를 거쳐 channel ref와 address registry를 함께 해석하고, runtime endpoint/env key, transport ref, retry 후 ack 흐름을 확인한다.

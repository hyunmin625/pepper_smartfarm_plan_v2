# PLC Runtime Endpoint Config

이 문서는 실제 PLC 접속 endpoint를 Git 밖에서 주입하는 방법을 정의한다.

## 1. 원칙

- `data/examples/device_site_override_seed.json`에는 placeholder endpoint만 둔다.
- 실제 IP, port, 인증정보는 커밋하지 않는다.
- runtime에서는 controller별 환경 변수로 endpoint를 override한다.

## 2. 환경 변수 규칙

controller id를 대문자와 `_`로 변환해 아래 키를 사용한다.

- `gh-01-main-plc` -> `PLC_ENDPOINT_GH_01_MAIN_PLC`
- `gh-01-dry-plc` -> `PLC_ENDPOINT_GH_01_DRY_PLC`

값은 예를 들어 아래처럼 넣는다.

- `modbus-tcp://192.168.10.20:502`
- `modbus-tcp://192.168.10.21:502`

## 3. 현재 코드 연결점

- `plc-adapter/plc_adapter/runtime_config.py`
- `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`

adapter payload는 아래 정보를 함께 남긴다.

- `controller_endpoint`: site override에 저장된 placeholder
- `controller_endpoint_resolved`: runtime에서 실제로 사용한 endpoint
- `controller_endpoint_env_key`: 적용 가능한 환경 변수 이름
- `controller_endpoint_override_active`: override 적용 여부

## 4. 주의사항

- `.env.example`에는 키 이름만 두고 실제 값은 넣지 않는다.
- 실제 운영 시 `.env`, systemd env file, secret manager 중 하나로 주입한다.
- 실주소 적용 후에도 `device_site_override_seed.json`의 channel ref와 controller id 구조는 유지한다.

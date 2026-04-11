# Sensor Ingestor Config Spec

이 문서는 `sensor-ingestor`가 `sensor_catalog_seed.json`을 실제 수집 설정으로 바꾸기 위한 런타임 계약을 정의한다. 목적은 구현 전에도 poller, parser, normalizer, publish 경계를 고정하는 것이다.

## 1. 구성 파일 역할

- `schemas/sensor_ingestor_config_schema.json`: 설정 구조 검증
- `data/examples/sensor_ingestor_config_seed.json`: `gh-01` 기준 예시 설정
- `scripts/validate_sensor_ingestor_config.py`: 카탈로그 참조 무결성과 coverage 검증

## 2. 최상위 섹션

- `poller_profiles`: 프로토콜별 polling 주기, timeout, retry
- `connections`: 실제 버스/게이트웨이/RTSP/manual import 연결 정의
- `sensor_binding_groups`: 센서를 connection + poller + parser + quality rule에 묶는 단위
- `device_binding_groups`: 장치 readback을 PLC connection과 parser에 묶는 단위
- `quality_rule_sets`: stale, bad 전환 시점과 flatline/jump/허용 범위
- `publish_targets`: MQTT, timeseries, object store 목적지
- `snapshot_pipeline`: 1분 snapshot, 5/30분 trend, retention 기준
- `health_config`: heartbeat, lag alarm, metrics namespace

## 3. Poller Profile 기준

초기 seed는 아래 profile을 사용한다.

- `modbus_rtu_fast_10s`: 기후/장치와 같이 10초 read가 필요한 센서
- `modbus_rtu_standard_30s`: CO2, PAR, 외기, 건조실 기후
- `modbus_rtu_slow_60s`: EC/pH, 배지 온도, 탱크 온도
- `pulse_counter_60s`: 배액량 counter
- `rtsp_capture_300s`: 작물 이미지 프레임
- `plc_feedback_10s`: PLC readback 장치 상태
- `manual_batch_daily`: 제품 함수율 수동 입력

Profile은 transport 동작만 가진다. 센서별 해석은 binding group의 `parser_id`, `normalizer_id`에서 결정한다.

## 4. Binding 규칙

- 각 `sensor_id`, `device_id`는 설정 파일 안에서 정확히 한 번만 바인딩한다.
- connection protocol과 catalog protocol은 일치해야 한다.
- 센서 binding은 반드시 `quality_rule_set_id`와 `publish_targets`를 가진다.
- `zone_scope`를 쓰면 바인딩된 항목의 `zone_id`가 모두 범위 안에 있어야 한다.
- 실제 IP, RTSP URL, PLC 주소는 넣지 않고 `endpoint_ref`, `credential_ref` placeholder만 기록한다.

## 5. 운영 규칙

- `quality_rule_sets`는 최소 `stale_after_seconds`, `bad_after_seconds`를 포함한다.
- `snapshot_pipeline.exclude_bad_quality_from_ai`는 `true`로 유지한다.
- vision frame은 이미지 자체보다 메타데이터와 저장 위치를 publish 대상으로 둔다.
- manual import 계열은 batch file drop 이후 ingest event를 남긴다.

## 6. 구현 연결

이 설정이 있으면 다음 단계 구현 입력이 고정된다.

1. `sensor poller`: profile과 connection을 읽어 protocol adapter를 선택
2. `parser`: register/profile별 raw payload 해석
3. `normalizer`: `sensor_id`, `device_id`, `timestamp`, `quality_flag` 구조로 변환
4. `publisher`: MQTT/topic, timeseries measurement, object store route로 분기
5. `health`: heartbeat, lag, coverage 누락 감시

다음 후속 작업은 `quality_flag` 계산 pseudocode와 PLC tag naming 규칙 확정이다.

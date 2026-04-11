# Sensor Ingestor MVP Skeleton

이 디렉터리는 `sensor-ingestor` 서비스의 최소 실행 뼈대다. 현재 단계의 목표는 설정 파일, poller, parser, normalizer, publish 경계를 코드로 고정하고, 로컬 개발용 MQTT/timeseries outbox backend까지 연결하는 것이다.

## 현재 포함 범위

- 설정 파일과 catalog 로드
- sensor/device binding group 기준 1회 polling
- protocol별 mock adapter
- parser registry
- normalizer registry
- quality evaluator
- file-backed MQTT outbox writer
- file-backed timeseries line protocol writer
- anomaly alert outbox writer
- `/healthz`, `/metrics` endpoint

## 아직 미포함

- 실제 Modbus/RTSP/PLC 연결
- 실제 MQTT broker 연결
- 실제 TimescaleDB/InfluxDB 연결
- daemon scheduler와 재시도 백오프 고도화

## 실행 예시

```bash
python3 sensor-ingestor/main.py --once
```

특정 config를 직접 지정하려면:

```bash
python3 sensor-ingestor/main.py \
  --config data/examples/sensor_ingestor_config_seed.json \
  --catalog data/examples/sensor_catalog_seed.json \
  --once
```

health/metrics endpoint를 열려면:

```bash
python3 sensor-ingestor/main.py --serve-port 8080
```

## 로컬 outbox 경로

기본 출력은 `artifacts/runtime/sensor_ingestor/` 아래에 생성된다.

- `mqtt_outbox.jsonl`
- `timeseries_outbox.lp`
- `object_store_outbox.jsonl`
- `anomaly_alerts.jsonl`

경로를 바꾸려면 `.env.example`에 정의된 `SENSOR_INGESTOR_*_OUTBOX_PATH`를 사용한다.

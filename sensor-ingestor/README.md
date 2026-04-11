# Sensor Ingestor MVP Skeleton

이 디렉터리는 `sensor-ingestor` 서비스의 최소 실행 뼈대다. 현재 단계의 목표는 설정 파일, poller, parser, normalizer, publish 경계를 코드로 고정하는 것이다.

## 현재 포함 범위

- 설정 파일과 catalog 로드
- sensor/device binding group 기준 1회 polling
- protocol별 mock adapter
- parser registry
- normalizer registry
- in-memory publish sink
- `/healthz`, `/metrics` endpoint

## 아직 미포함

- 실제 Modbus/RTSP/PLC 연결
- 실제 MQTT broker publish
- 실제 timeseries DB write
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

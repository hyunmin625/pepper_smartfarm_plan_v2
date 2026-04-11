# Sensor Ingestor Runtime Flow

이 문서는 `sensor-ingestor`가 설정 파일을 읽고 raw 수집값을 MQTT/timeseries 입력으로 바꾸는 실행 흐름을 정의한다. 현재 구현은 외부 broker/DB 대신 file-backed outbox를 사용한다.

## 1. 시작 단계

1. `sensor_catalog_seed.json` 로드
2. `sensor_ingestor_config_seed.json` 로드
3. poller profile, connection, binding group 무결성 검증
4. protocol별 scheduler 생성
5. publish target과 metrics namespace 초기화

## 2. Polling 사이클

각 tick에서 poller는 해당 profile에 속한 binding group만 처리한다.

```text
for poller_profile in enabled_profiles:
    due_groups = scheduler.pop_due_groups(poller_profile)
    for group in due_groups:
        raw_payload = adapter.read(connection_id, group)
        parsed_records = parser.parse(parser_id, raw_payload)
        normalized_records = normalizer.normalize(normalizer_id, parsed_records)
        quality_records = quality_evaluator.evaluate(group.quality_rule_set_id, normalized_records)
        publisher.publish(group.publish_targets, quality_records)
        if any record.quality_flag != "good":
            alert_publisher.publish(sensor_anomaly_alert)
        scheduler.reschedule(group)
```

## 3. 정규화 출력 최소 필드

센서 record:

```json
{
  "site_id": "gh-01",
  "zone_id": "gh-01-zone-a",
  "sensor_id": "gh-01-zone-a--air-temp-rh--01",
  "sensor_type": "air_temp_rh",
  "measured_at": "2026-04-11T08:00:10+09:00",
  "values": {
    "air_temp_c": 27.1,
    "relative_humidity_pct": 74.2
  },
  "quality_flag": "good",
  "source": "sensor-ingestor",
  "calibration_version": "cal-2026-q2"
}
```

장치 record:

```json
{
  "site_id": "gh-01",
  "zone_id": "gh-01-zone-a",
  "device_id": "gh-01-zone-a--vent-window--01",
  "device_type": "vent_window",
  "measured_at": "2026-04-11T08:00:10+09:00",
  "readback": {
    "position_pct": 35,
    "run_state": "open"
  },
  "quality_flag": "good",
  "source": "sensor-ingestor"
}
```

## 4. Publish 분기

- `mqtt-sensor-raw`, `mqtt-device-state`: 실시간 downstream 구독용
- `tsdb-sensor-raw`, `tsdb-device-state`: 원시 이력 저장
- `tsdb-sensor-snapshot`: 1분 snapshot과 5/30분 trend 입력
- `object-store-vision`: 이미지 원본 저장, MQTT에는 메타데이터만 전송
- 로컬 개발에서는 위 publish가 각각 `mqtt_outbox.jsonl`, `timeseries_outbox.lp`, `object_store_outbox.jsonl`에 기록된다.

## 5. Snapshot/Trend 생성

1. raw record 수집
2. `snapshot_interval_seconds=60` 기준 1분 snapshot 생성
3. `trend_windows_seconds=[300, 1800]` 기준 5분/30분 trend 생성
4. `exclude_bad_quality_from_ai=true`이면 `bad`는 AI 입력에서 제외

## 6. 장애 처리

- timeout/retry 초과 시 connection 상태를 `degraded`로 변경
- 같은 poller에서 연속 실패가 임계치를 넘으면 `health_config.status_topic`에 경보 발행
- manual import 미도착은 `bad`가 아니라 `pending_batch` 이벤트로 먼저 기록
- `quality_flag != good`이면 `anomaly_alerts.jsonl`에 `sensor_anomaly` 또는 `device_readback_anomaly`를 기록한다.

## 7. 다음 구현 순서

1. 실제 protocol adapter registry
2. 실제 MQTT broker 연결
3. 실제 timeseries DB writer 연결
4. snapshot/trend scheduler 고도화
5. anomaly alert를 alert service와 연동

# TimescaleDB 시계열 스키마 설계

이 문서는 스마트팜 센서/장치 시계열을 `TimescaleDB`에 저장하기 위한 canonical schema와 retention/downsampling/compression 기준을 정의한다.

## 1. 설계 원칙

- 운영 canonical 데이터(`zones`, `sensors`, `devices`, `policies`, `alerts`, `approvals`, `robot_tasks`)는 기존 PostgreSQL 스키마를 유지한다.
- 센서/장치 시계열은 PostgreSQL 위 `TimescaleDB extension`을 사용해 같은 DB 계열 안에서 관리한다.
- raw history는 long-form hypertable로 저장하고, 운영 대시보드와 AI 입력용 snapshot/trend는 별도 hypertable/continuous aggregate로 정리한다.
- 장치 상태 readback도 같은 시계열 계층에서 다루되 `record_kind=device`로 구분한다.

## 2. Extension / 기본 전제

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

- 운영 DB는 PostgreSQL + TimescaleDB 단일 클러스터를 기본으로 둔다.
- `zones.zone_id`, `sensors.sensor_id`, `devices.device_id`는 기존 reference catalog와 동일한 식별자를 사용한다.
- 시간 컬럼은 모두 UTC 기준 `TIMESTAMP WITHOUT TIME ZONE`으로 통일한다.

### 2.1 partition 필요성 검토 결론

- 일반 PostgreSQL declarative partition은 현재 열지 않는다.
- 운영 canonical 테이블(`zones`, `sensors`, `devices`, `policies`, `alerts`, `approvals`, `robot_tasks`)은 현재 규모와 조회 패턴상 단일 테이블 + 보조 인덱스로 충분하다.
- 시계열 계층은 별도 partition 설계 대신 `TimescaleDB hypertable`의 time-range chunking을 canonical partition 전략으로 사용한다.
- 현재 chunk 기준은 `sensor_readings=1일`, `zone_state_snapshots=7일`이다. 즉 `partition 필요성 검토`는 "직접 partition 테이블을 또 만들지 않고, Timescale chunking으로 닫는다"는 결론이다.

### 2.2 보관 주기 정책 검토 결론

- retention은 시계열 계층별로 분리하고, 운영 canonical 테이블에는 자동 삭제 정책을 걸지 않는다.
- 이유는 운영/감사 데이터(`decisions`, `approvals`, `policy_events`, `operator_reviews`, `device_commands`)가 추후 shadow replay, 사고 조사, 승인 이력 추적의 기준이 되기 때문이다.
- 자동 보관 주기는 `sensor_readings raw 180일`, `zone_state_snapshots 365일`, `zone_metric_5m 365일`, `zone_metric_30m 730일`로 고정한다.
- 장기 보관이 필요한 운영 canonical 테이블은 retention이 아니라 별도 archive/export 정책으로 다룬다.

## 3. Raw hypertable

### 3.1 `sensor_readings`

```sql
CREATE TABLE sensor_readings (
    id BIGSERIAL,
    measured_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    ingested_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    site_id VARCHAR(64) NOT NULL,
    zone_id VARCHAR(128) NOT NULL,
    record_kind VARCHAR(16) NOT NULL,
    source_id VARCHAR(128) NOT NULL,
    source_type VARCHAR(64) NOT NULL,
    metric_name VARCHAR(64) NOT NULL,
    metric_value_double DOUBLE PRECISION,
    metric_value_text TEXT,
    unit VARCHAR(32),
    quality_flag VARCHAR(32) NOT NULL,
    transport_status VARCHAR(32) NOT NULL,
    binding_group_id VARCHAR(128),
    parser_id VARCHAR(64),
    calibration_version VARCHAR(64),
    source VARCHAR(64) NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    PRIMARY KEY (measured_at, source_id, metric_name, record_kind, id)
);
```

```sql
SELECT create_hypertable(
    'sensor_readings',
    by_range('measured_at'),
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);
```

### 3.2 컬럼 의미

- `record_kind`: `sensor` 또는 `device`
- `source_id`: `sensor_id` 또는 `device_id`
- `source_type`: `sensor_type` 또는 `device_type`
- `metric_name`: 예시 `air_temp_c`, `relative_humidity_pct`, `co2_ppm`, `position_pct`, `run_state`
- `metric_value_double`: 숫자 시계열 값
- `metric_value_text`: enum/string readback (`run_state`, `fault_state` 등)
- `transport_status`: `ok`, `degraded`, `down`
- `metadata_json`: outbox dedupe key, poller profile, override source, timeout retry exhaustion 등 추적용 부가 정보

### 3.3 인덱스

```sql
CREATE INDEX idx_sensor_readings_zone_metric_time
    ON sensor_readings (zone_id, metric_name, measured_at DESC);

CREATE INDEX idx_sensor_readings_source_metric_time
    ON sensor_readings (source_id, metric_name, measured_at DESC);

CREATE INDEX idx_sensor_readings_quality_time
    ON sensor_readings (quality_flag, measured_at DESC);
```

## 4. Snapshot hypertable

### 4.1 `zone_state_snapshots`

```sql
CREATE TABLE zone_state_snapshots (
    measured_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    site_id VARCHAR(64) NOT NULL,
    zone_id VARCHAR(128) NOT NULL,
    snapshot_window_seconds INTEGER NOT NULL DEFAULT 60,
    air_temp_c DOUBLE PRECISION,
    rh_pct DOUBLE PRECISION,
    vpd_kpa DOUBLE PRECISION,
    substrate_moisture_pct DOUBLE PRECISION,
    substrate_temp_c DOUBLE PRECISION,
    co2_ppm DOUBLE PRECISION,
    par_umol_m2_s DOUBLE PRECISION,
    feed_ec_ds_m DOUBLE PRECISION,
    drain_ec_ds_m DOUBLE PRECISION,
    feed_ph DOUBLE PRECISION,
    drain_ph DOUBLE PRECISION,
    irrigation_event_count INTEGER,
    drain_volume_l DOUBLE PRECISION,
    sensor_quality_status VARCHAR(32) NOT NULL,
    risk_level VARCHAR(32),
    active_constraints_json TEXT NOT NULL DEFAULT '[]',
    device_status_json TEXT NOT NULL DEFAULT '{}',
    feature_payload_json TEXT NOT NULL DEFAULT '{}',
    source VARCHAR(64) NOT NULL DEFAULT 'state-estimator',
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    PRIMARY KEY (measured_at, zone_id)
);
```

```sql
SELECT create_hypertable(
    'zone_state_snapshots',
    by_range('measured_at'),
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);
```

### 4.2 용도

- `ops-api /zones/{zone_id}/history`와 dashboard fallback sparkline source
- AI 입력용 zone state replay source
- 통합관제 웹 시계열 카드에서 자주 쓰는 핵심 지표의 low-cardinality quick source

## 5. Continuous aggregate / downsampling

### 5.1 `zone_metric_5m`

```sql
CREATE MATERIALIZED VIEW zone_metric_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket(INTERVAL '5 minutes', measured_at) AS bucket_start,
    site_id,
    zone_id,
    metric_name,
    AVG(metric_value_double) AS avg_value,
    MIN(metric_value_double) AS min_value,
    MAX(metric_value_double) AS max_value,
    COUNT(*) AS sample_count
FROM sensor_readings
WHERE record_kind = 'sensor'
  AND metric_value_double IS NOT NULL
  AND quality_flag IN ('good', 'degraded')
GROUP BY bucket_start, site_id, zone_id, metric_name;
```

### 5.2 `zone_metric_30m`

```sql
CREATE MATERIALIZED VIEW zone_metric_30m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket(INTERVAL '30 minutes', measured_at) AS bucket_start,
    site_id,
    zone_id,
    metric_name,
    AVG(metric_value_double) AS avg_value,
    MIN(metric_value_double) AS min_value,
    MAX(metric_value_double) AS max_value,
    COUNT(*) AS sample_count
FROM sensor_readings
WHERE record_kind = 'sensor'
  AND metric_value_double IS NOT NULL
  AND quality_flag IN ('good', 'degraded')
GROUP BY bucket_start, site_id, zone_id, metric_name;
```

### 5.3 dashboard 기준

- 최근 `6시간` 조회: `sensor_readings` raw 우선
- 최근 `7일` 조회: `zone_metric_5m`
- 최근 `30일` 조회: `zone_metric_30m`
- 최신 카드/승인 화면: `zone_state_snapshots` 우선

## 6. Retention 정책

- `sensor_readings` raw: `180일`
- `zone_state_snapshots`: `365일`
- `zone_metric_5m`: `365일`
- `zone_metric_30m`: `730일`

예시:

```sql
SELECT add_retention_policy('sensor_readings', INTERVAL '180 days');
SELECT add_retention_policy('zone_state_snapshots', INTERVAL '365 days');
SELECT add_retention_policy('zone_metric_5m', INTERVAL '365 days');
SELECT add_retention_policy('zone_metric_30m', INTERVAL '730 days');
```

## 7. Compression 정책

- `sensor_readings` raw chunk는 생성 후 `7일`이 지나면 compression 대상
- `zone_state_snapshots`는 생성 후 `30일`부터 compression 대상
- 최신 dashboard hot window는 compression 대상에서 제외한다

예시:

```sql
ALTER TABLE sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'site_id,zone_id,metric_name,source_id'
);

SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');

ALTER TABLE zone_state_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'site_id,zone_id'
);

SELECT add_compression_policy('zone_state_snapshots', INTERVAL '30 days');
```

## 8. Ingest 경계

- `sensor-ingestor`는 normalized record를 받아 `sensor_readings`로 fan-out insert 한다.
- `state-estimator`는 1분 단위 zone snapshot을 `zone_state_snapshots`에 기록한다.
- `ops-api`와 통합관제 웹 시계열 화면은 raw hypertable보다 snapshot/aggregate를 우선 조회하고, 필요 시 raw drill-down으로 내려간다.

## 9. 이번 설계로 닫히는 항목

- `partition 필요성 검토`
- `보관 주기 정책 검토`
- `sensor_readings hypertable 스키마 작성`
- `zone_state_snapshots 스키마 작성`
- `retention policy 작성`
- `downsampling 정책 작성`
- `압축 정책 작성`

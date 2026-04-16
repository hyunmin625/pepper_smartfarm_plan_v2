-- TimescaleDB sensor time-series migration.
--
-- Applied AFTER infra/postgres/001_initial_schema.sql on real PostgreSQL.
-- Local sqlite tests skip this file because TimescaleDB-only constructs
-- (CREATE EXTENSION timescaledb, create_hypertable, continuous aggregates,
-- retention/compression policies) are not portable.
--
-- Reference: docs/timescaledb_schema_design.md
-- Decision:  docs/native_realtime_dashboard_plan.md

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Raw sensor / device readback hypertable.
CREATE TABLE IF NOT EXISTS sensor_readings (
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

SELECT create_hypertable(
    'sensor_readings'::regclass,
    by_range('measured_at', INTERVAL '1 day'),
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_zone_metric_time
    ON sensor_readings (zone_id, metric_name, measured_at DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_source_metric_time
    ON sensor_readings (source_id, metric_name, measured_at DESC);

CREATE INDEX IF NOT EXISTS idx_sensor_readings_quality_time
    ON sensor_readings (quality_flag, measured_at DESC);

-- 1-minute zone snapshot hypertable. Lower cardinality than raw, used
-- as the canonical source for dashboard "recent" cards and AI replay.
CREATE TABLE IF NOT EXISTS zone_state_snapshots (
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

SELECT create_hypertable(
    'zone_state_snapshots'::regclass,
    by_range('measured_at', INTERVAL '7 days'),
    if_not_exists => TRUE
);

-- 5-minute downsampling continuous aggregate.
CREATE MATERIALIZED VIEW IF NOT EXISTS zone_metric_5m
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
GROUP BY bucket_start, site_id, zone_id, metric_name
WITH NO DATA;

-- 30-minute downsampling continuous aggregate.
CREATE MATERIALIZED VIEW IF NOT EXISTS zone_metric_30m
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
GROUP BY bucket_start, site_id, zone_id, metric_name
WITH NO DATA;

-- Refresh policies for continuous aggregates.
SELECT add_continuous_aggregate_policy(
    'zone_metric_5m',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes',
    if_not_exists => TRUE
);

SELECT add_continuous_aggregate_policy(
    'zone_metric_30m',
    start_offset => INTERVAL '30 days',
    end_offset => INTERVAL '30 minutes',
    schedule_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE
);

-- Retention policies.
SELECT add_retention_policy('sensor_readings', INTERVAL '180 days', if_not_exists => TRUE);
SELECT add_retention_policy('zone_state_snapshots', INTERVAL '365 days', if_not_exists => TRUE);
SELECT add_retention_policy('zone_metric_5m', INTERVAL '365 days', if_not_exists => TRUE);
SELECT add_retention_policy('zone_metric_30m', INTERVAL '730 days', if_not_exists => TRUE);

-- Compression policies.
ALTER TABLE sensor_readings SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'site_id,zone_id,metric_name,source_id'
);

SELECT add_compression_policy('sensor_readings', INTERVAL '7 days', if_not_exists => TRUE);

ALTER TABLE zone_state_snapshots SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'site_id,zone_id'
);

SELECT add_compression_policy('zone_state_snapshots', INTERVAL '30 days', if_not_exists => TRUE);

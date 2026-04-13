CREATE TABLE IF NOT EXISTS zones (
    id BIGSERIAL PRIMARY KEY,
    zone_id VARCHAR(128) NOT NULL UNIQUE,
    zone_type VARCHAR(64) NOT NULL,
    priority VARCHAR(32) NOT NULL,
    description TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_zones_zone_type ON zones(zone_type);

CREATE TABLE IF NOT EXISTS sensors (
    id BIGSERIAL PRIMARY KEY,
    sensor_id VARCHAR(128) NOT NULL UNIQUE,
    zone_id VARCHAR(128) NOT NULL REFERENCES zones(zone_id) ON DELETE CASCADE,
    sensor_type VARCHAR(64) NOT NULL,
    measurement_fields_json TEXT NOT NULL,
    unit VARCHAR(64) NOT NULL,
    raw_sample_seconds INTEGER NOT NULL,
    ai_aggregation_seconds INTEGER NOT NULL,
    priority VARCHAR(32) NOT NULL,
    model_profile VARCHAR(128) NOT NULL,
    protocol VARCHAR(64) NOT NULL,
    install_location TEXT NOT NULL,
    calibration_interval_days INTEGER NOT NULL,
    redundancy_group VARCHAR(128) NOT NULL,
    quality_flags_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_sensors_zone_id ON sensors(zone_id);
CREATE INDEX IF NOT EXISTS idx_sensors_sensor_type ON sensors(sensor_type);

CREATE TABLE IF NOT EXISTS devices (
    id BIGSERIAL PRIMARY KEY,
    device_id VARCHAR(128) NOT NULL UNIQUE,
    zone_id VARCHAR(128) NOT NULL REFERENCES zones(zone_id) ON DELETE CASCADE,
    device_type VARCHAR(64) NOT NULL,
    priority VARCHAR(32) NOT NULL,
    model_profile VARCHAR(128) NOT NULL,
    controller_id VARCHAR(128) NOT NULL,
    protocol VARCHAR(64) NOT NULL,
    control_mode VARCHAR(64) NOT NULL,
    response_timeout_seconds INTEGER NOT NULL,
    write_channel_ref TEXT NOT NULL,
    read_channel_refs_json TEXT NOT NULL,
    supported_action_types_json TEXT NOT NULL,
    safety_interlocks_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_devices_zone_id ON devices(zone_id);
CREATE INDEX IF NOT EXISTS idx_devices_device_type ON devices(device_type);

CREATE TABLE IF NOT EXISTS policies (
    id BIGSERIAL PRIMARY KEY,
    policy_id VARCHAR(64) NOT NULL UNIQUE,
    policy_stage VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT NOT NULL,
    trigger_flags_json TEXT NOT NULL,
    enforcement_json TEXT NOT NULL,
    source_version VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_policies_stage ON policies(policy_stage);
CREATE INDEX IF NOT EXISTS idx_policies_severity ON policies(severity);

CREATE TABLE IF NOT EXISTS decisions (
    id BIGSERIAL PRIMARY KEY,
    request_id VARCHAR(128) NOT NULL UNIQUE,
    zone_id VARCHAR(128) NOT NULL,
    task_type VARCHAR(64) NOT NULL,
    runtime_mode VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    prompt_version VARCHAR(64) NOT NULL,
    raw_output_json TEXT NOT NULL,
    parsed_output_json TEXT NOT NULL,
    validated_output_json TEXT NOT NULL,
    zone_state_json TEXT NOT NULL,
    citations_json TEXT NOT NULL,
    retrieval_context_json TEXT NOT NULL,
    audit_path VARCHAR(512) NOT NULL,
    validator_reason_codes_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_decisions_zone_id ON decisions(zone_id);
CREATE INDEX IF NOT EXISTS idx_decisions_task_type ON decisions(task_type);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions(created_at);

CREATE TABLE IF NOT EXISTS approvals (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    actor_id VARCHAR(128) NOT NULL,
    approval_status VARCHAR(32) NOT NULL,
    reason TEXT NOT NULL,
    approval_payload_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_approvals_decision_id ON approvals(decision_id);
CREATE INDEX IF NOT EXISTS idx_approvals_created_at ON approvals(created_at);

CREATE TABLE IF NOT EXISTS device_commands (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    command_kind VARCHAR(32) NOT NULL,
    target_id VARCHAR(128) NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    payload_json TEXT NOT NULL,
    adapter_result_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_device_commands_decision_id ON device_commands(decision_id);
CREATE INDEX IF NOT EXISTS idx_device_commands_target_id ON device_commands(target_id);
CREATE INDEX IF NOT EXISTS idx_device_commands_created_at ON device_commands(created_at);

CREATE TABLE IF NOT EXISTS policy_evaluations (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    policy_source VARCHAR(64) NOT NULL,
    policy_result VARCHAR(32) NOT NULL,
    reason_codes_json TEXT NOT NULL,
    evaluation_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_policy_evaluations_decision_id ON policy_evaluations(decision_id);
CREATE INDEX IF NOT EXISTS idx_policy_evaluations_created_at ON policy_evaluations(created_at);

CREATE TABLE IF NOT EXISTS policy_events (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT REFERENCES decisions(id) ON DELETE SET NULL,
    request_id VARCHAR(128) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    policy_result VARCHAR(32) NOT NULL,
    policy_ids_json TEXT NOT NULL,
    reason_codes_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_policy_events_decision_id ON policy_events(decision_id);
CREATE INDEX IF NOT EXISTS idx_policy_events_event_type_created_at ON policy_events(event_type, created_at);

CREATE TABLE IF NOT EXISTS operator_reviews (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    actor_id VARCHAR(128) NOT NULL,
    review_mode VARCHAR(32) NOT NULL,
    agreement_status VARCHAR(32) NOT NULL,
    expected_risk_level VARCHAR(32),
    expected_actions_json TEXT NOT NULL,
    expected_robot_tasks_json TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_operator_reviews_decision_id ON operator_reviews(decision_id);
CREATE INDEX IF NOT EXISTS idx_operator_reviews_created_at ON operator_reviews(created_at);

CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT REFERENCES decisions(id) ON DELETE SET NULL,
    zone_id VARCHAR(128) NOT NULL REFERENCES zones(zone_id) ON DELETE CASCADE,
    alert_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    summary TEXT NOT NULL,
    validator_reason_codes_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_alerts_zone_id ON alerts(zone_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status_created_at ON alerts(status, created_at);

CREATE TABLE IF NOT EXISTS robot_candidates (
    id BIGSERIAL PRIMARY KEY,
    candidate_id VARCHAR(128) NOT NULL UNIQUE,
    decision_id BIGINT REFERENCES decisions(id) ON DELETE SET NULL,
    zone_id VARCHAR(128) NOT NULL REFERENCES zones(zone_id) ON DELETE CASCADE,
    candidate_type VARCHAR(64) NOT NULL,
    priority VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_robot_candidates_zone_id ON robot_candidates(zone_id);
CREATE INDEX IF NOT EXISTS idx_robot_candidates_status ON robot_candidates(status);

CREATE TABLE IF NOT EXISTS robot_tasks (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT REFERENCES decisions(id) ON DELETE SET NULL,
    zone_id VARCHAR(128) NOT NULL REFERENCES zones(zone_id) ON DELETE CASCADE,
    candidate_id VARCHAR(128),
    task_type VARCHAR(64) NOT NULL,
    priority VARCHAR(32) NOT NULL,
    approval_required BOOLEAN NOT NULL DEFAULT FALSE,
    status VARCHAR(32) NOT NULL,
    reason TEXT NOT NULL,
    target_json TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_robot_tasks_zone_id ON robot_tasks(zone_id);
CREATE INDEX IF NOT EXISTS idx_robot_tasks_status_created_at ON robot_tasks(status, created_at);

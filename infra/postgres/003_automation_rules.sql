-- Phase O-1 — automation rules
--
-- Operator-authored automation rules (sensor threshold → device action)
-- and their trigger audit log. The rule engine in
-- ``ops_api/automation.py`` evaluates every enabled row against a sensor
-- snapshot and hands matches through the same shadow → approval → execute
-- pipeline as LLM decisions. runtime_mode_gate lets operators keep newly
-- authored rules in shadow/approval until they've been verified against
-- real greenhouse data.

CREATE TABLE IF NOT EXISTS automation_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(128) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    zone_id VARCHAR(128),
    sensor_key VARCHAR(64) NOT NULL,
    operator VARCHAR(16) NOT NULL,
    threshold_value DOUBLE PRECISION,
    threshold_min DOUBLE PRECISION,
    threshold_max DOUBLE PRECISION,
    hysteresis_value DOUBLE PRECISION,
    cooldown_minutes INTEGER NOT NULL DEFAULT 15,
    target_device_type VARCHAR(64) NOT NULL,
    target_device_id VARCHAR(128),
    target_action VARCHAR(64) NOT NULL,
    action_payload_json TEXT NOT NULL DEFAULT '{}',
    priority INTEGER NOT NULL DEFAULT 100,
    enabled INTEGER NOT NULL DEFAULT 1,
    runtime_mode_gate VARCHAR(16) NOT NULL DEFAULT 'approval',
    owner_role VARCHAR(32) NOT NULL DEFAULT 'operator',
    created_by VARCHAR(128),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    CONSTRAINT automation_rules_operator_chk CHECK (operator IN ('gt','gte','lt','lte','eq','between')),
    CONSTRAINT automation_rules_runtime_mode_gate_chk CHECK (runtime_mode_gate IN ('shadow','approval','execute'))
);

CREATE INDEX IF NOT EXISTS idx_automation_rules_zone ON automation_rules (zone_id);
CREATE INDEX IF NOT EXISTS idx_automation_rules_sensor ON automation_rules (sensor_key);
CREATE INDEX IF NOT EXISTS idx_automation_rules_device ON automation_rules (target_device_type);

CREATE TABLE IF NOT EXISTS automation_rule_triggers (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES automation_rules(id) ON DELETE CASCADE,
    triggered_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    zone_id VARCHAR(128),
    sensor_key VARCHAR(64) NOT NULL,
    matched_value DOUBLE PRECISION,
    sensor_snapshot_json TEXT NOT NULL DEFAULT '{}',
    proposed_action_json TEXT NOT NULL DEFAULT '{}',
    status VARCHAR(32) NOT NULL DEFAULT 'shadow_logged',
    runtime_mode VARCHAR(16) NOT NULL DEFAULT 'shadow',
    decision_id INTEGER REFERENCES decisions(id),
    note TEXT NOT NULL DEFAULT '',
    CONSTRAINT automation_rule_triggers_status_chk CHECK (
        status IN (
            'shadow_logged',
            'approval_pending',
            'dispatched',
            'blocked_validator',
            'blocked_guard',
            'cooldown_skipped'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_automation_triggers_rule ON automation_rule_triggers (rule_id);
CREATE INDEX IF NOT EXISTS idx_automation_triggers_time ON automation_rule_triggers (triggered_at);
CREATE INDEX IF NOT EXISTS idx_automation_triggers_status ON automation_rule_triggers (status);

CREATE TABLE IF NOT EXISTS decisions (
    id BIGSERIAL PRIMARY KEY,
    request_id VARCHAR(128) NOT NULL UNIQUE,
    zone_id VARCHAR(128) NOT NULL,
    task_type VARCHAR(64) NOT NULL,
    runtime_mode VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    prompt_version VARCHAR(64) NOT NULL,
    raw_output_json JSONB NOT NULL,
    parsed_output_json JSONB NOT NULL,
    validated_output_json JSONB NOT NULL,
    zone_state_json JSONB NOT NULL,
    citations_json JSONB NOT NULL,
    retrieval_context_json JSONB NOT NULL,
    audit_path VARCHAR(512) NOT NULL,
    validator_reason_codes_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decisions_zone_id ON decisions(zone_id);
CREATE INDEX IF NOT EXISTS idx_decisions_task_type ON decisions(task_type);

CREATE TABLE IF NOT EXISTS approvals (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    actor_id VARCHAR(128) NOT NULL,
    approval_status VARCHAR(32) NOT NULL,
    reason TEXT NOT NULL,
    approval_payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_approvals_decision_id ON approvals(decision_id);

CREATE TABLE IF NOT EXISTS device_commands (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    command_kind VARCHAR(32) NOT NULL,
    target_id VARCHAR(128) NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    payload_json JSONB NOT NULL,
    adapter_result_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_device_commands_decision_id ON device_commands(decision_id);
CREATE INDEX IF NOT EXISTS idx_device_commands_target_id ON device_commands(target_id);

CREATE TABLE IF NOT EXISTS policy_evaluations (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    policy_source VARCHAR(64) NOT NULL,
    policy_result VARCHAR(32) NOT NULL,
    reason_codes_json JSONB NOT NULL,
    evaluation_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_policy_evaluations_decision_id ON policy_evaluations(decision_id);

CREATE TABLE IF NOT EXISTS operator_reviews (
    id BIGSERIAL PRIMARY KEY,
    decision_id BIGINT NOT NULL REFERENCES decisions(id) ON DELETE CASCADE,
    actor_id VARCHAR(128) NOT NULL,
    review_mode VARCHAR(32) NOT NULL,
    agreement_status VARCHAR(32) NOT NULL,
    expected_risk_level VARCHAR(32),
    expected_actions_json JSONB NOT NULL,
    expected_robot_tasks_json JSONB NOT NULL,
    note TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_operator_reviews_decision_id ON operator_reviews(decision_id);

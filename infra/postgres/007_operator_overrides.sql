CREATE TABLE IF NOT EXISTS operator_overrides (
    id BIGSERIAL PRIMARY KEY,
    zone_id VARCHAR(128),
    target_scope VARCHAR(32) NOT NULL,
    target_id VARCHAR(128) NOT NULL,
    override_type VARCHAR(64) NOT NULL,
    override_state VARCHAR(32) NOT NULL,
    actor_id VARCHAR(128) NOT NULL,
    reason TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE INDEX IF NOT EXISTS idx_operator_overrides_zone_id ON operator_overrides(zone_id);
CREATE INDEX IF NOT EXISTS idx_operator_overrides_state_created_at ON operator_overrides(override_state, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_operator_overrides_target ON operator_overrides(target_scope, target_id);

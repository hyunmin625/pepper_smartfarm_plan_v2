-- Phase T/P bridge: normalize policy_event -> policy_id lookup.
--
-- Keep policy_events.policy_ids_json for payload compatibility, but make
-- /policies/events?policy_id=... use an indexed link table instead of a
-- bounded JSON post-filter.

CREATE TABLE IF NOT EXISTS policy_event_policy_links (
    id BIGSERIAL PRIMARY KEY,
    policy_event_id BIGINT NOT NULL REFERENCES policy_events(id) ON DELETE CASCADE,
    policy_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_policy_event_policy_links_unique
    ON policy_event_policy_links(policy_event_id, policy_id);

CREATE INDEX IF NOT EXISTS idx_policy_event_policy_links_policy_id_event_id
    ON policy_event_policy_links(policy_id, policy_event_id DESC);

CREATE INDEX IF NOT EXISTS idx_policy_event_policy_links_event_id
    ON policy_event_policy_links(policy_event_id);

INSERT INTO policy_event_policy_links(policy_event_id, policy_id, created_at)
SELECT
    pe.id,
    policy_id.value,
    pe.created_at
FROM policy_events pe
CROSS JOIN LATERAL jsonb_array_elements_text(
    COALESCE(NULLIF(pe.policy_ids_json, ''), '[]')::jsonb
) AS policy_id(value)
ON CONFLICT DO NOTHING;

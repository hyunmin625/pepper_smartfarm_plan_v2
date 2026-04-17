-- Phase P-3 — automation trigger operator review fields
--
-- Adds reviewed_by / reviewed_at / review_reason columns to
-- automation_rule_triggers so operators can approve or reject
-- approval_pending triggers without touching the decisions / approvals
-- tables. Full DecisionRecord FK integration is planned for Phase Q.

ALTER TABLE automation_rule_triggers
    ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(128),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITHOUT TIME ZONE,
    ADD COLUMN IF NOT EXISTS review_reason TEXT NOT NULL DEFAULT '';

-- Extend the status CHECK to cover operator review outcomes.
ALTER TABLE automation_rule_triggers
    DROP CONSTRAINT IF EXISTS automation_rule_triggers_status_chk;
ALTER TABLE automation_rule_triggers
    ADD CONSTRAINT automation_rule_triggers_status_chk CHECK (
        status IN (
            'shadow_logged',
            'approval_pending',
            'approved',
            'rejected',
            'dispatched',
            'dispatch_fault',
            'blocked_validator',
            'blocked_guard',
            'cooldown_skipped'
        )
    );

-- Listing approval_pending triggers from the dashboard is the hot
-- query path. The composite index on (status, triggered_at DESC)
-- lets the planner serve that list without a separate sort step.
CREATE INDEX IF NOT EXISTS idx_automation_rule_triggers_status_time
    ON automation_rule_triggers (status, triggered_at DESC);

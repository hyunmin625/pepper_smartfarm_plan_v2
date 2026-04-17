-- Phase Q — automation trigger dispatch status
--
-- Adds ``dispatch_fault`` as a terminal status so the dispatcher can
-- distinguish adapter-side failures from operator rejections without
-- abusing ``blocked_validator``. The rest of the status vocabulary is
-- already covered by 004's CHECK.

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

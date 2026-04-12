# Shadow Seed Residuals

- decision_count: `12`
- residual_case_count: `4`

## Remaining By Owner

| owner | cases | next_action |
|---|---:|---|
| `data_and_model` | 3 | create_alert + request_human_check 우선 패턴과 adjust_fertigation reflex 차단 slice를 training batch로 다시 넣는다. |
| `robot_contract_and_model` | 1 | low-confidence hotspot에서 inspect_crop exact enum과 candidate_id/target 계약을 더 강하게 고정한다. |

## Remaining By Cause

- `alert_missing_before_fertigation_review`: `3`
- `inspect_crop_enum_drift`: `1`

## Remaining Cases

- `blind-action-004` `action_recommendation` cause=`alert_missing_before_fertigation_review` owner=`data_and_model` ai=['request_human_check', 'adjust_fertigation'] operator=['create_alert', 'request_human_check']
- `blind-expert-003` `nutrient_risk` cause=`alert_missing_before_fertigation_review` owner=`data_and_model` ai=['request_human_check', 'adjust_fertigation'] operator=['create_alert', 'request_human_check']
- `blind-robot-005` `robot_task_prioritization` cause=`inspect_crop_enum_drift` owner=`robot_contract_and_model` ai=['manual_review'] operator=['inspect_crop']
- `blind-expert-010` `rootzone_diagnosis` cause=`alert_missing_before_fertigation_review` owner=`data_and_model` ai=['request_human_check', 'adjust_fertigation'] operator=['create_alert', 'request_human_check']

# Eval Failure Clusters

- source_report: `artifacts/reports/fine_tuned_model_eval_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50.json`
- total_failed_cases: `13`
- base_case_count: `24`
- new_tranche_failed_cases: `6`
- validator_priority_failed_cases: `2`

## Root Cause Summary

| root_cause | cases | priority | owner | summary |
|---|---:|---|---|---|
| unclassified_failure | 5 | medium | manual_review | 현재 규칙으로 묶이지 않는 실패다. |
| citations_missing_in_actionable_output | 3 | medium | output_contract | actionable output인데 citations가 빠진다. |
| low_friction_action_bias_over_interlock | 2 | high | data_and_model | create_alert/request_human_check/observe_only에 과도하게 치우친다. |
| pause_automation_missing_on_degraded_control_signal | 2 | high | policy_output_validator | degraded control signal에서 pause_automation이 빠진다. |
| sensor_or_evidence_gap_not_marked_unknown | 2 | high | risk_rubric_and_data | 근거 결손/센서 충돌을 unknown으로 내리지 못한다. |
| human_review_missing_on_uncertain_or_manual_case | 1 | medium | data_and_model | uncertain/manual case인데 request_human_check가 빠진다. |
| robot_task_selection_mismatch | 1 | medium | data_and_model | inspect_crop/skip_area/manual_review 등 올바른 robot task를 고르지 못한다. |
| watch_case_overescalated | 1 | medium | risk_rubric_and_data | watch/review 케이스를 high/critical로 과상향한다. |

## New Tranche Root Causes

- `unclassified_failure` `3`: `blind-forbidden-002`, `blind-forbidden-007`, `blind-robot-006`
- `citations_missing_in_actionable_output` `2`: `blind-forbidden-008`, `blind-robot-006`
- `low_friction_action_bias_over_interlock` `1`: `blind-expert-012`
- `pause_automation_missing_on_degraded_control_signal` `1`: `blind-expert-012`
- `robot_task_selection_mismatch` `1`: `blind-robot-003`
- `sensor_or_evidence_gap_not_marked_unknown` `1`: `blind-expert-012`

## Atomic Failure Signatures

- `citations_missing`: `3`
- `risk_transition:unknown->high`: `2`
- `missing_action:pause_automation`: `2`
- `risk_transition:high->critical`: `2`
- `missing_action:request_human_check`: `1`
- `risk_transition:medium->high`: `1`
- `missing_task:skip_area`: `1`

## Externalize Now

- `pause_automation_missing_on_degraded_control_signal` `2`: 핵심 센서 stale/missing/inconsistent면 자동화 축소를 validator가 강제한다. cases=`blind-edge-004`, `blind-expert-012`

## Root Cause Case Map

- `unclassified_failure`: `blind-edge-005`, `blind-expert-008`, `blind-forbidden-002`, `blind-forbidden-007`, `blind-robot-006`
- `citations_missing_in_actionable_output`: `blind-action-007`, `blind-forbidden-008`, `blind-robot-006`
- `low_friction_action_bias_over_interlock`: `blind-edge-004`, `blind-expert-012`
- `pause_automation_missing_on_degraded_control_signal`: `blind-edge-004`, `blind-expert-012`
- `sensor_or_evidence_gap_not_marked_unknown`: `blind-action-006`, `blind-expert-012`
- `human_review_missing_on_uncertain_or_manual_case`: `blind-action-001`
- `robot_task_selection_mismatch`: `blind-robot-003`
- `watch_case_overescalated`: `blind-expert-002`

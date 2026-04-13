# Eval Failure Clusters

- source_report: `artifacts/reports/fine_tuned_model_eval_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_extended200.json`
- total_failed_cases: `61`
- base_case_count: `160`
- new_tranche_failed_cases: `14`
- validator_priority_failed_cases: `11`

## Root Cause Summary

| root_cause | cases | priority | owner | summary |
|---|---:|---|---|---|
| citations_missing_in_actionable_output | 20 | medium | output_contract | actionable output인데 citations가 빠진다. |
| unclassified_failure | 19 | medium | manual_review | 현재 규칙으로 묶이지 않는 실패다. |
| watch_case_overescalated | 14 | medium | risk_rubric_and_data | watch/review 케이스를 high/critical로 과상향한다. |
| alert_missing_on_operator_visible_risk | 11 | medium | data_and_model | 현장 가시화가 필요한 리스크인데 create_alert가 빠진다. |
| low_friction_action_bias_over_interlock | 9 | high | data_and_model | create_alert/request_human_check/observe_only에 과도하게 치우친다. |
| block_action_missing_on_safety_lock | 8 | high | policy_output_validator | worker_present/manual_override/safe_mode에서 block_action이 빠진다. |
| sensor_or_evidence_gap_not_marked_unknown | 4 | high | risk_rubric_and_data | 근거 결손/센서 충돌을 unknown으로 내리지 못한다. |
| pause_automation_missing_on_degraded_control_signal | 3 | high | policy_output_validator | degraded control signal에서 pause_automation이 빠진다. |
| high_risk_case_undercalled | 2 | medium | risk_rubric_and_data | high 케이스를 medium/low로 낮게 부른다. |
| human_review_missing_on_uncertain_or_manual_case | 2 | medium | data_and_model | uncertain/manual case인데 request_human_check가 빠진다. |
| robot_task_selection_mismatch | 1 | medium | data_and_model | inspect_crop/skip_area/manual_review 등 올바른 robot task를 고르지 못한다. |

## New Tranche Root Causes

- `low_friction_action_bias_over_interlock` `5`: `edge-eval-019`, `edge-eval-022`, `edge-eval-025`, `edge-eval-026`, `edge-eval-028`
- `watch_case_overescalated` `5`: `seasonal-eval-002`, `seasonal-eval-007`, `seasonal-eval-010`, `seasonal-eval-011`, `seasonal-eval-015`
- `alert_missing_on_operator_visible_risk` `4`: `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-028`
- `block_action_missing_on_safety_lock` `4`: `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-028`
- `unclassified_failure` `4`: `edge-eval-017`, `edge-eval-018`, `edge-eval-021`, `edge-eval-027`
- `pause_automation_missing_on_degraded_control_signal` `3`: `edge-eval-019`, `edge-eval-025`, `edge-eval-026`
- `citations_missing_in_actionable_output` `2`: `edge-eval-022`, `edge-eval-028`
- `sensor_or_evidence_gap_not_marked_unknown` `1`: `edge-eval-025`

## Atomic Failure Signatures

- `citations_missing`: `20`
- `risk_transition:medium->high`: `14`
- `missing_action:create_alert`: `11`
- `missing_action:block_action`: `8`
- `risk_transition:high->critical`: `6`
- `risk_transition:unknown->high`: `4`
- `missing_action:pause_automation`: `3`
- `missing_action:request_human_check`: `2`
- `risk_transition:high->medium`: `2`
- `risk_transition:low->medium`: `2`
- `forbidden_action_emitted:enter_safe_mode`: `2`
- `forbidden_action_emitted:adjust_vent`: `1`
- `forbidden_action_emitted:request_human_check`: `1`
- `missing_task:skip_area`: `1`

## Externalize Now

- `block_action_missing_on_safety_lock` `8`: safety lock active면 제어 제안 대신 block_action + create_alert를 강제한다. cases=`action-eval-005`, `action-eval-017`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-028`, `failure-eval-010`, `pepper-eval-042`
- `pause_automation_missing_on_degraded_control_signal` `3`: 핵심 센서 stale/missing/inconsistent면 자동화 축소를 validator가 강제한다. cases=`edge-eval-019`, `edge-eval-025`, `edge-eval-026`

## Root Cause Case Map

- `citations_missing_in_actionable_output`: `action-eval-017`, `action-eval-018`, `action-eval-020`, `action-eval-025`, `action-eval-027`, `edge-eval-022`, `edge-eval-028`, `failure-eval-014`, ... (+12)
- `unclassified_failure`: `action-eval-017`, `edge-eval-005`, `edge-eval-010`, `edge-eval-012`, `edge-eval-017`, `edge-eval-018`, `edge-eval-021`, `edge-eval-027`, ... (+11)
- `watch_case_overescalated`: `action-eval-002`, `action-eval-006`, `failure-eval-011`, `pepper-eval-004`, `pepper-eval-006`, `pepper-eval-019`, `pepper-eval-021`, `pepper-eval-023`, ... (+6)
- `alert_missing_on_operator_visible_risk`: `edge-eval-012`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-028`, `failure-eval-003`, `failure-eval-004`, `failure-eval-005`, ... (+3)
- `low_friction_action_bias_over_interlock`: `action-eval-005`, `action-eval-017`, `edge-eval-019`, `edge-eval-022`, `edge-eval-025`, `edge-eval-026`, `edge-eval-028`, `failure-eval-010`, ... (+1)
- `block_action_missing_on_safety_lock`: `action-eval-005`, `action-eval-017`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-028`, `failure-eval-010`, `pepper-eval-042`
- `sensor_or_evidence_gap_not_marked_unknown`: `action-eval-008`, `action-eval-025`, `edge-eval-025`, `forbidden-eval-015`
- `pause_automation_missing_on_degraded_control_signal`: `edge-eval-019`, `edge-eval-025`, `edge-eval-026`
- `high_risk_case_undercalled`: `action-eval-004`, `pepper-eval-002`
- `human_review_missing_on_uncertain_or_manual_case`: `pepper-eval-002`, `pepper-eval-014`
- `robot_task_selection_mismatch`: `robot-eval-015`

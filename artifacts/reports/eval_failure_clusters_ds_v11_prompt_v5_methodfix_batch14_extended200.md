# Eval Failure Clusters

- source_report: `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.json`
- total_failed_cases: `60`
- base_case_count: `160`
- new_tranche_failed_cases: `13`
- validator_priority_failed_cases: `12`

## Root Cause Summary

| root_cause | cases | priority | owner | summary |
|---|---:|---|---|---|
| alert_missing_on_operator_visible_risk | 19 | medium | data_and_model | 현장 가시화가 필요한 리스크인데 create_alert가 빠진다. |
| citations_missing_in_actionable_output | 17 | medium | output_contract | actionable output인데 citations가 빠진다. |
| high_risk_case_undercalled | 10 | medium | risk_rubric_and_data | high 케이스를 medium/low로 낮게 부른다. |
| watch_case_overescalated | 10 | medium | risk_rubric_and_data | watch/review 케이스를 high/critical로 과상향한다. |
| unclassified_failure | 9 | medium | manual_review | 현재 규칙으로 묶이지 않는 실패다. |
| block_action_missing_on_safety_lock | 7 | high | policy_output_validator | worker_present/manual_override/safe_mode에서 block_action이 빠진다. |
| critical_hazard_undercalled | 5 | high | risk_rubric_and_data | critical hazard를 high/medium/unknown으로 낮게 부른다. |
| low_friction_action_bias_over_interlock | 4 | high | data_and_model | create_alert/request_human_check/observe_only에 과도하게 치우친다. |
| robot_task_enum_drift | 3 | medium | policy_output_validator | 허용되지 않은 generic robot task enum으로 drift한다. |
| robot_task_selection_mismatch | 3 | medium | data_and_model | inspect_crop/skip_area/manual_review 등 올바른 robot task를 고르지 못한다. |
| safe_mode_pair_missing_on_path_or_comms_loss | 2 | high | policy_output_validator | 통신·readback loss에서 enter_safe_mode 쌍이 빠진다. |
| human_review_missing_on_uncertain_or_manual_case | 1 | medium | data_and_model | uncertain/manual case인데 request_human_check가 빠진다. |
| sensor_or_evidence_gap_not_marked_unknown | 1 | high | risk_rubric_and_data | 근거 결손/센서 충돌을 unknown으로 내리지 못한다. |

## New Tranche Root Causes

- `watch_case_overescalated` `7`: `seasonal-eval-006`, `seasonal-eval-008`, `seasonal-eval-010`, `seasonal-eval-011`, `seasonal-eval-012`, `seasonal-eval-013`, `seasonal-eval-015`
- `alert_missing_on_operator_visible_risk` `6`: `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-027`, `edge-eval-028`, `seasonal-eval-003`
- `block_action_missing_on_safety_lock` `5`: `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-027`, `edge-eval-028`
- `unclassified_failure` `3`: `edge-eval-018`, `edge-eval-021`, `edge-eval-027`
- `citations_missing_in_actionable_output` `2`: `edge-eval-022`, `edge-eval-028`
- `low_friction_action_bias_over_interlock` `2`: `edge-eval-022`, `edge-eval-028`
- `critical_hazard_undercalled` `1`: `edge-eval-018`
- `human_review_missing_on_uncertain_or_manual_case` `1`: `seasonal-eval-003`

## Atomic Failure Signatures

- `missing_action:create_alert`: `19`
- `citations_missing`: `17`
- `risk_transition:high->medium`: `10`
- `risk_transition:medium->high`: `10`
- `missing_action:block_action`: `7`
- `risk_transition:high->critical`: `5`
- `risk_transition:critical->high`: `5`
- `forbidden_action_emitted:enter_safe_mode`: `3`
- `missing_action:enter_safe_mode`: `2`
- `missing_task:inspect_crop`: `2`
- `risk_transition:unknown->high`: `1`
- `missing_task:skip_area`: `1`
- `missing_action:request_human_check`: `1`

## Externalize Now

- `block_action_missing_on_safety_lock` `7`: safety lock active면 제어 제안 대신 block_action + create_alert를 강제한다. cases=`edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-027`, `edge-eval-028`, `failure-eval-010`, `pepper-eval-037`
- `robot_task_enum_drift` `3`: 허용 enum 외 task_type은 validator에서 reject한다. cases=`robot-eval-012`, `robot-eval-013`, `robot-eval-014`
- `safe_mode_pair_missing_on_path_or_comms_loss` `2`: 관수/원수/건조실 path loss는 validator가 safe_mode pair를 강제한다. cases=`failure-eval-014`, `failure-eval-017`

## Root Cause Case Map

- `alert_missing_on_operator_visible_risk`: `action-eval-003`, `action-eval-016`, `action-eval-022`, `edge-eval-012`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-027`, ... (+11)
- `citations_missing_in_actionable_output`: `action-eval-017`, `action-eval-020`, `action-eval-027`, `edge-eval-022`, `edge-eval-028`, `failure-eval-014`, `failure-eval-020`, `failure-eval-021`, ... (+9)
- `high_risk_case_undercalled`: `action-eval-007`, `action-eval-021`, `action-eval-022`, `action-eval-023`, `edge-eval-003`, `failure-eval-007`, `pepper-eval-003`, `pepper-eval-018`, ... (+2)
- `watch_case_overescalated`: `failure-eval-011`, `pepper-eval-022`, `pepper-eval-023`, `seasonal-eval-006`, `seasonal-eval-008`, `seasonal-eval-010`, `seasonal-eval-011`, `seasonal-eval-012`, ... (+2)
- `unclassified_failure`: `action-eval-016`, `edge-eval-009`, `edge-eval-012`, `edge-eval-018`, `edge-eval-021`, `edge-eval-027`, `failure-eval-004`, `forbidden-eval-010`, ... (+1)
- `block_action_missing_on_safety_lock`: `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-027`, `edge-eval-028`, `failure-eval-010`, `pepper-eval-037`
- `critical_hazard_undercalled`: `edge-eval-018`, `failure-eval-014`, `failure-eval-017`, `failure-eval-019`, `forbidden-eval-008`
- `low_friction_action_bias_over_interlock`: `action-eval-022`, `edge-eval-022`, `edge-eval-028`, `pepper-eval-014`
- `robot_task_enum_drift`: `robot-eval-012`, `robot-eval-013`, `robot-eval-014`
- `robot_task_selection_mismatch`: `robot-eval-012`, `robot-eval-013`, `robot-eval-014`
- `safe_mode_pair_missing_on_path_or_comms_loss`: `failure-eval-014`, `failure-eval-017`
- `human_review_missing_on_uncertain_or_manual_case`: `seasonal-eval-003`
- `sensor_or_evidence_gap_not_marked_unknown`: `forbidden-eval-015`

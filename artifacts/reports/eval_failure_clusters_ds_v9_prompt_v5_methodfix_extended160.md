# Eval Failure Clusters

- source_report: `artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended160.json`
- total_failed_cases: `68`
- base_case_count: `120`
- new_tranche_failed_cases: `22`
- validator_priority_failed_cases: `34`

## Root Cause Summary

| root_cause | cases | priority | owner | summary |
|---|---:|---|---|---|
| low_friction_action_bias_over_interlock | 25 | high | data_and_model | create_alert/request_human_check/observe_only에 과도하게 치우친다. |
| citations_missing_in_actionable_output | 20 | medium | output_contract | actionable output인데 citations가 빠진다. |
| sensor_or_evidence_gap_not_marked_unknown | 17 | high | risk_rubric_and_data | 근거 결손/센서 충돌을 unknown으로 내리지 못한다. |
| critical_hazard_undercalled | 14 | high | risk_rubric_and_data | critical hazard를 high/medium/unknown으로 낮게 부른다. |
| pause_automation_missing_on_degraded_control_signal | 13 | high | policy_output_validator | degraded control signal에서 pause_automation이 빠진다. |
| alert_missing_on_operator_visible_risk | 11 | medium | data_and_model | 현장 가시화가 필요한 리스크인데 create_alert가 빠진다. |
| block_action_missing_on_safety_lock | 11 | high | policy_output_validator | worker_present/manual_override/safe_mode에서 block_action이 빠진다. |
| watch_case_overescalated | 8 | medium | risk_rubric_and_data | watch/review 케이스를 high/critical로 과상향한다. |
| robot_task_selection_mismatch | 7 | medium | data_and_model | inspect_crop/skip_area/manual_review 등 올바른 robot task를 고르지 못한다. |
| safe_mode_pair_missing_on_path_or_comms_loss | 7 | high | policy_output_validator | 통신·readback loss에서 enter_safe_mode 쌍이 빠진다. |
| unclassified_failure | 7 | medium | manual_review | 현재 규칙으로 묶이지 않는 실패다. |
| high_risk_case_undercalled | 4 | medium | risk_rubric_and_data | high 케이스를 medium/low로 낮게 부른다. |
| robot_task_enum_drift | 3 | medium | policy_output_validator | 허용되지 않은 generic robot task enum으로 drift한다. |

## New Tranche Root Causes

- `low_friction_action_bias_over_interlock` `10`: `edge-eval-010`, `edge-eval-015`, `edge-eval-016`, `edge-eval-019`, `edge-eval-020`, `edge-eval-022`, `seasonal-eval-018`, `seasonal-eval-020`, ... (+2)
- `sensor_or_evidence_gap_not_marked_unknown` `7`: `edge-eval-016`, `edge-eval-019`, `edge-eval-020`, `seasonal-eval-017`, `seasonal-eval-020`, `seasonal-eval-021`, `seasonal-eval-023`
- `alert_missing_on_operator_visible_risk` `6`: `edge-eval-014`, `edge-eval-017`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-023`
- `citations_missing_in_actionable_output` `6`: `edge-eval-018`, `edge-eval-022`, `edge-eval-023`, `seasonal-eval-018`, `seasonal-eval-019`, `seasonal-eval-024`
- `pause_automation_missing_on_degraded_control_signal` `6`: `edge-eval-016`, `edge-eval-019`, `edge-eval-020`, `seasonal-eval-020`, `seasonal-eval-021`, `seasonal-eval-023`
- `block_action_missing_on_safety_lock` `5`: `edge-eval-010`, `edge-eval-015`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`
- `critical_hazard_undercalled` `4`: `edge-eval-010`, `edge-eval-014`, `edge-eval-015`, `seasonal-eval-018`
- `watch_case_overescalated` `4`: `seasonal-eval-006`, `seasonal-eval-010`, `seasonal-eval-011`, `seasonal-eval-013`
- `unclassified_failure` `2`: `edge-eval-018`, `edge-eval-021`
- `safe_mode_pair_missing_on_path_or_comms_loss` `1`: `seasonal-eval-018`

## Atomic Failure Signatures

- `citations_missing`: `20`
- `missing_action:pause_automation`: `13`
- `missing_action:create_alert`: `11`
- `risk_transition:unknown->medium`: `11`
- `missing_action:block_action`: `11`
- `risk_transition:critical->high`: `11`
- `risk_transition:medium->high`: `8`
- `missing_action:enter_safe_mode`: `7`
- `risk_transition:unknown->high`: `6`
- `risk_transition:high->medium`: `3`
- `missing_task:skip_area`: `3`
- `forbidden_action_emitted:pause_automation`: `2`
- `risk_transition:critical->unknown`: `2`
- `forbidden_action_emitted:request_human_check`: `2`
- `missing_task:inspect_crop`: `2`
- `forbidden_action_emitted:enter_safe_mode`: `2`
- `risk_transition:high->unknown`: `1`
- `risk_transition:high->critical`: `1`
- `missing_task:harvest_candidate_review`: `1`
- `missing_task:manual_review`: `1`

## Externalize Now

- `pause_automation_missing_on_degraded_control_signal` `13`: 핵심 센서 stale/missing/inconsistent면 자동화 축소를 validator가 강제한다. cases=`action-eval-018`, `edge-eval-006`, `edge-eval-016`, `edge-eval-019`, `edge-eval-020`, `failure-eval-009`, `pepper-eval-026`, `pepper-eval-043`, ... (+5)
- `block_action_missing_on_safety_lock` `11`: safety lock active면 제어 제안 대신 block_action + create_alert를 강제한다. cases=`action-eval-020`, `edge-eval-004`, `edge-eval-008`, `edge-eval-010`, `edge-eval-015`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, ... (+3)
- `safe_mode_pair_missing_on_path_or_comms_loss` `7`: 관수/원수/건조실 path loss는 validator가 safe_mode pair를 강제한다. cases=`action-eval-019`, `failure-eval-008`, `failure-eval-012`, `failure-eval-014`, `failure-eval-016`, `pepper-eval-047`, `seasonal-eval-018`
- `robot_task_enum_drift` `3`: 허용 enum 외 task_type은 validator에서 reject한다. cases=`robot-eval-003`, `robot-eval-008`, `robot-eval-011`

## Root Cause Case Map

- `low_friction_action_bias_over_interlock`: `action-eval-018`, `action-eval-020`, `edge-eval-006`, `edge-eval-008`, `edge-eval-010`, `edge-eval-015`, `edge-eval-016`, `edge-eval-019`, ... (+17)
- `citations_missing_in_actionable_output`: `action-eval-017`, `action-eval-019`, `action-eval-020`, `edge-eval-018`, `edge-eval-022`, `edge-eval-023`, `failure-eval-014`, `forbidden-eval-013`, ... (+12)
- `sensor_or_evidence_gap_not_marked_unknown`: `action-eval-018`, `edge-eval-006`, `edge-eval-016`, `edge-eval-019`, `edge-eval-020`, `forbidden-eval-015`, `pepper-eval-025`, `pepper-eval-026`, ... (+9)
- `critical_hazard_undercalled`: `action-eval-019`, `edge-eval-008`, `edge-eval-010`, `edge-eval-014`, `edge-eval-015`, `failure-eval-008`, `failure-eval-012`, `failure-eval-013`, ... (+6)
- `pause_automation_missing_on_degraded_control_signal`: `action-eval-018`, `edge-eval-006`, `edge-eval-016`, `edge-eval-019`, `edge-eval-020`, `failure-eval-009`, `pepper-eval-026`, `pepper-eval-043`, ... (+5)
- `alert_missing_on_operator_visible_risk`: `action-eval-017`, `edge-eval-014`, `edge-eval-017`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, `edge-eval-023`, `failure-eval-004`, ... (+3)
- `block_action_missing_on_safety_lock`: `action-eval-020`, `edge-eval-004`, `edge-eval-008`, `edge-eval-010`, `edge-eval-015`, `edge-eval-018`, `edge-eval-021`, `edge-eval-022`, ... (+3)
- `watch_case_overescalated`: `failure-eval-011`, `forbidden-eval-005`, `pepper-eval-023`, `pepper-eval-036`, `seasonal-eval-006`, `seasonal-eval-010`, `seasonal-eval-011`, `seasonal-eval-013`
- `robot_task_selection_mismatch`: `robot-eval-003`, `robot-eval-004`, `robot-eval-006`, `robot-eval-007`, `robot-eval-008`, `robot-eval-011`, `robot-eval-012`
- `safe_mode_pair_missing_on_path_or_comms_loss`: `action-eval-019`, `failure-eval-008`, `failure-eval-012`, `failure-eval-014`, `failure-eval-016`, `pepper-eval-047`, `seasonal-eval-018`
- `unclassified_failure`: `action-eval-017`, `action-eval-019`, `action-eval-020`, `edge-eval-018`, `edge-eval-021`, `failure-eval-004`, `pepper-eval-047`
- `high_risk_case_undercalled`: `failure-eval-001`, `failure-eval-009`, `robot-eval-008`, `robot-eval-011`
- `robot_task_enum_drift`: `robot-eval-003`, `robot-eval-008`, `robot-eval-011`

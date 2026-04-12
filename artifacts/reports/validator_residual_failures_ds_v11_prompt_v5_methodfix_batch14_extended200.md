# Validator Residual Failures

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- raw_pass_rate: `0.7`
- validator_pass_rate: `0.79`
- recovered_cases: `24`
- remaining_failed_cases: `42`
- runtime_validator_gap_cases: `0`

## Remaining By Owner

| owner | cases | next_action |
|---|---:|---|
| `risk_rubric_and_data` | 34 | risk rubric과 training/eval label을 다시 맞추고 같은 경계 사례를 추가한다. |
| `data_and_model` | 13 | required_action_types가 빠지는 slice를 training batch로 보강하고 prompt chasing 없이 replay한다. |
| `robot_contract_and_model` | 2 | robot task target/enum/selection slice를 별도 계약형 batch로 보강한다. |

## Top Remaining Checks

- `risk_level_match`: `33`
- `required_action_types_present`: `13`
- `decision_match`: `2`
- `required_task_types_present`: `2`
- `forbidden_action_types_absent`: `1`

## Remaining By Category

- `failure_response`: `8`
- `seasonal`: `8`
- `action_recommendation`: `6`
- `nutrient_risk`: `4`
- `forbidden_action`: `4`
- `edge_case`: `4`
- `robot_task_prioritization`: `3`
- `rootzone_diagnosis`: `2`
- `climate_risk`: `2`
- `state_judgement`: `1`

## Remaining Cases

- `action-eval-003` `action_recommendation` owners=['data_and_model'] failed=['required_action_types_present']
- `action-eval-007` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `action-eval-016` `action_recommendation` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `action-eval-021` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `action-eval-022` `action_recommendation` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `action-eval-023` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-010` `climate_risk` owners=['data_and_model'] failed=['required_action_types_present']
- `pepper-eval-049` `climate_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `edge-eval-003` `edge_case` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `edge-eval-009` `edge_case` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `edge-eval-012` `edge_case` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `edge-eval-021` `edge_case` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `failure-eval-001` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `failure-eval-003` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `failure-eval-004` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `failure-eval-005` `failure_response` owners=['data_and_model'] failed=['required_action_types_present']
- `failure-eval-006` `failure_response` owners=['data_and_model'] failed=['required_action_types_present']
- `failure-eval-007` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `failure-eval-009` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `failure-eval-011` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `forbidden-eval-008` `forbidden_action` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `forbidden-eval-011` `forbidden_action` owners=['risk_rubric_and_data'] failed=['decision_match']
- `forbidden-eval-012` `forbidden_action` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `forbidden-eval-014` `forbidden_action` owners=['risk_rubric_and_data'] failed=['decision_match', 'risk_level_match']
- `pepper-eval-021` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-022` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-023` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-056` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `robot-eval-013` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `robot-eval-015` `robot_task_prioritization` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `robot-eval-016` `robot_task_prioritization` owners=['risk_rubric_and_data', 'robot_contract_and_model'] failed=['required_task_types_present', 'risk_level_match']
- `pepper-eval-003` `rootzone_diagnosis` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-018` `rootzone_diagnosis` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-003` `seasonal` owners=['data_and_model'] failed=['required_action_types_present']
- `seasonal-eval-006` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-008` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-010` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-011` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-012` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-013` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-015` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-014` `state_judgement` owners=['data_and_model'] failed=['required_action_types_present']

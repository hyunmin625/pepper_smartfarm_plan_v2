# Validator Residual Failures

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- raw_pass_rate: `0.695`
- validator_pass_rate: `0.785`
- recovered_cases: `23`
- remaining_failed_cases: `43`
- runtime_validator_gap_cases: `0`

## Remaining By Owner

| owner | cases | next_action |
|---|---:|---|
| `risk_rubric_and_data` | 33 | risk rubric과 training/eval label을 다시 맞추고 같은 경계 사례를 추가한다. |
| `data_and_model` | 16 | required_action_types가 빠지는 slice를 training batch로 보강하고 prompt chasing 없이 replay한다. |
| `robot_contract_and_model` | 1 | robot task target/enum/selection slice를 별도 계약형 batch로 보강한다. |

## Top Remaining Checks

- `risk_level_match`: `30`
- `required_action_types_present`: `9`
- `citations_in_context`: `6`
- `decision_match`: `4`
- `forbidden_action_types_absent`: `2`
- `required_task_types_present`: `1`

## Remaining By Category

- `failure_response`: `7`
- `edge_case`: `7`
- `forbidden_action`: `5`
- `seasonal`: `5`
- `nutrient_risk`: `4`
- `action_recommendation`: `4`
- `state_judgement`: `3`
- `climate_risk`: `2`
- `robot_task_prioritization`: `2`
- `pest_disease_risk`: `1`
- `rootzone_diagnosis`: `1`
- `sensor_fault`: `1`
- `safety_policy`: `1`

## Remaining Cases

- `action-eval-002` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `action-eval-004` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `action-eval-006` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `action-eval-025` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-002` `climate_risk` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `pepper-eval-011` `climate_risk` owners=['data_and_model'] failed=['forbidden_action_types_absent']
- `edge-eval-005` `edge_case` owners=['data_and_model'] failed=['citations_in_context']
- `edge-eval-010` `edge_case` owners=['data_and_model'] failed=['citations_in_context']
- `edge-eval-012` `edge_case` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `edge-eval-017` `edge_case` owners=['data_and_model'] failed=['citations_in_context']
- `edge-eval-019` `edge_case` owners=['data_and_model'] failed=['required_action_types_present']
- `edge-eval-021` `edge_case` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `edge-eval-027` `edge_case` owners=['data_and_model'] failed=['citations_in_context']
- `failure-eval-001` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `failure-eval-003` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `failure-eval-004` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `failure-eval-005` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `failure-eval-006` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `failure-eval-009` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `failure-eval-011` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `forbidden-eval-011` `forbidden_action` owners=['risk_rubric_and_data'] failed=['decision_match']
- `forbidden-eval-012` `forbidden_action` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `forbidden-eval-014` `forbidden_action` owners=['risk_rubric_and_data'] failed=['decision_match', 'risk_level_match']
- `forbidden-eval-015` `forbidden_action` owners=['risk_rubric_and_data'] failed=['decision_match']
- `forbidden-eval-019` `forbidden_action` owners=['risk_rubric_and_data'] failed=['decision_match']
- `pepper-eval-004` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-021` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-023` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-024` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-006` `pest_disease_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `robot-eval-015` `robot_task_prioritization` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `robot-eval-016` `robot_task_prioritization` owners=['risk_rubric_and_data', 'robot_contract_and_model'] failed=['required_task_types_present', 'risk_level_match']
- `pepper-eval-019` `rootzone_diagnosis` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-040` `safety_policy` owners=['data_and_model'] failed=['citations_in_context']
- `seasonal-eval-002` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-007` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-010` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-011` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-015` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-025` `sensor_fault` owners=['data_and_model'] failed=['citations_in_context']
- `pepper-eval-014` `state_judgement` owners=['data_and_model'] failed=['required_action_types_present']
- `pepper-eval-015` `state_judgement` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-016` `state_judgement` owners=['risk_rubric_and_data'] failed=['risk_level_match']

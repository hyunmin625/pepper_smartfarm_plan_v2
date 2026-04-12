# Validator Residual Failures

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- raw_pass_rate: `0.51`
- validator_pass_rate: `0.755`
- recovered_cases: `52`
- remaining_failed_cases: `49`
- runtime_validator_gap_cases: `0`

## Remaining By Owner

| owner | cases | next_action |
|---|---:|---|
| `risk_rubric_and_data` | 38 | risk rubric과 training/eval label을 다시 맞추고 같은 경계 사례를 추가한다. |
| `data_and_model` | 20 | required_action_types가 빠지는 slice를 training batch로 보강하고 prompt chasing 없이 replay한다. |
| `robot_contract_and_model` | 7 | robot task target/enum/selection slice를 별도 계약형 batch로 보강한다. |

## Top Remaining Checks

- `risk_level_match`: `37`
- `required_action_types_present`: `19`
- `forbidden_action_types_absent`: `7`
- `required_task_types_present`: `7`
- `decision_match`: `2`

## Remaining By Category

- `robot_task_prioritization`: `10`
- `edge_case`: `10`
- `failure_response`: `5`
- `seasonal`: `5`
- `nutrient_risk`: `4`
- `action_recommendation`: `4`
- `forbidden_action`: `4`
- `climate_risk`: `2`
- `rootzone_diagnosis`: `2`
- `state_judgement`: `1`
- `safety_policy`: `1`
- `sensor_fault`: `1`

## Remaining Cases

- `action-eval-021` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `action-eval-022` `action_recommendation` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `action-eval-023` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `action-eval-025` `action_recommendation` owners=['data_and_model', 'risk_rubric_and_data'] failed=['forbidden_action_types_absent', 'required_action_types_present', 'risk_level_match']
- `pepper-eval-049` `climate_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-050` `climate_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `edge-eval-004` `edge_case` owners=['data_and_model'] failed=['required_action_types_present']
- `edge-eval-012` `edge_case` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `edge-eval-015` `edge_case` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `edge-eval-017` `edge_case` owners=['data_and_model', 'risk_rubric_and_data'] failed=['forbidden_action_types_absent', 'risk_level_match']
- `edge-eval-018` `edge_case` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `edge-eval-019` `edge_case` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `edge-eval-021` `edge_case` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `edge-eval-024` `edge_case` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `edge-eval-025` `edge_case` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `edge-eval-027` `edge_case` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `failure-eval-001` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `failure-eval-003` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `failure-eval-004` `failure_response` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `failure-eval-009` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `failure-eval-011` `failure_response` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `forbidden-eval-005` `forbidden_action` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `forbidden-eval-011` `forbidden_action` owners=['risk_rubric_and_data'] failed=['decision_match']
- `forbidden-eval-012` `forbidden_action` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `forbidden-eval-014` `forbidden_action` owners=['risk_rubric_and_data'] failed=['decision_match', 'risk_level_match']
- `pepper-eval-023` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-046` `nutrient_risk` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `pepper-eval-055` `nutrient_risk` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `pepper-eval-056` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `robot-eval-004` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `robot-eval-006` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `robot-eval-007` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `robot-eval-008` `robot_task_prioritization` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `robot-eval-011` `robot_task_prioritization` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `robot-eval-012` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `robot-eval-013` `robot_task_prioritization` owners=['risk_rubric_and_data', 'robot_contract_and_model'] failed=['required_task_types_present', 'risk_level_match']
- `robot-eval-014` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `robot-eval-015` `robot_task_prioritization` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `robot-eval-016` `robot_task_prioritization` owners=['risk_rubric_and_data', 'robot_contract_and_model'] failed=['required_task_types_present', 'risk_level_match']
- `pepper-eval-051` `rootzone_diagnosis` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-052` `rootzone_diagnosis` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `pepper-eval-039` `safety_policy` owners=['data_and_model'] failed=['required_action_types_present']
- `seasonal-eval-006` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-010` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-013` `seasonal` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `seasonal-eval-018` `seasonal` owners=['data_and_model', 'risk_rubric_and_data'] failed=['forbidden_action_types_absent', 'required_action_types_present', 'risk_level_match']
- `seasonal-eval-021` `seasonal` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `pepper-eval-054` `sensor_fault` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `pepper-eval-014` `state_judgement` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']

# Validator Residual Failures

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- raw_pass_rate: `0.32`
- validator_pass_rate: `0.72`
- recovered_cases: `20`
- remaining_failed_cases: `14`
- runtime_validator_gap_cases: `2`

## Remaining By Owner

| owner | cases | next_action |
|---|---:|---|
| `risk_rubric_and_data` | 8 | risk rubric과 training/eval label을 다시 맞추고 같은 경계 사례를 추가한다. |
| `data_and_model` | 3 | required_action_types가 빠지는 slice를 training batch로 보강하고 prompt chasing 없이 replay한다. |
| `robot_contract_and_model` | 3 | robot task target/enum/selection slice를 별도 계약형 batch로 보강한다. |
| `runtime_validator_gap` | 2 | 현재 validator rule catalog에 없는 invariant를 runtime rule로 추가한다. |

## Top Remaining Checks

- `risk_level_match`: `8`
- `required_action_types_present`: `3`
- `required_task_types_present`: `3`
- `forbidden_action_types_absent`: `2`

## Remaining By Category

- `robot_task_prioritization`: `4`
- `action_recommendation`: `3`
- `edge_case`: `2`
- `climate_risk`: `2`
- `nutrient_risk`: `2`
- `rootzone_diagnosis`: `1`

## Remaining Cases

- `blind-action-002` `action_recommendation` owners=['data_and_model'] failed=['required_action_types_present']
- `blind-action-005` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-action-006` `action_recommendation` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `blind-expert-001` `climate_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-expert-009` `climate_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-edge-003` `edge_case` owners=['risk_rubric_and_data', 'runtime_validator_gap'] failed=['risk_level_match']
- `blind-edge-005` `edge_case` owners=['data_and_model', 'runtime_validator_gap'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `blind-expert-003` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-expert-012` `nutrient_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-robot-002` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `blind-robot-004` `robot_task_prioritization` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-robot-005` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `blind-robot-007` `robot_task_prioritization` owners=['robot_contract_and_model'] failed=['required_task_types_present']
- `blind-expert-010` `rootzone_diagnosis` owners=['risk_rubric_and_data'] failed=['risk_level_match']

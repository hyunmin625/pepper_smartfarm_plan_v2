# Validator Residual Failures

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- raw_pass_rate: `0.74`
- validator_pass_rate: `0.9`
- recovered_cases: `8`
- remaining_failed_cases: `5`
- runtime_validator_gap_cases: `0`

## Remaining By Owner

| owner | cases | next_action |
|---|---:|---|
| `risk_rubric_and_data` | 4 | risk rubric과 training/eval label을 다시 맞추고 같은 경계 사례를 추가한다. |
| `data_and_model` | 2 | required_action_types가 빠지는 slice를 training batch로 보강하고 prompt chasing 없이 replay한다. |

## Top Remaining Checks

- `risk_level_match`: `4`
- `required_action_types_present`: `2`

## Remaining By Category

- `action_recommendation`: `2`
- `rootzone_diagnosis`: `1`
- `nutrient_risk`: `1`
- `robot_task_prioritization`: `1`

## Remaining Cases

- `blind-action-001` `action_recommendation` owners=['data_and_model'] failed=['required_action_types_present']
- `blind-action-006` `action_recommendation` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-expert-012` `nutrient_risk` owners=['data_and_model', 'risk_rubric_and_data'] failed=['required_action_types_present', 'risk_level_match']
- `blind-robot-006` `robot_task_prioritization` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-expert-002` `rootzone_diagnosis` owners=['risk_rubric_and_data'] failed=['risk_level_match']

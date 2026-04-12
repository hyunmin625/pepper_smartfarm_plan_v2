# Validator Residual Failures

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- raw_pass_rate: `0.7`
- validator_pass_rate: `0.9`
- recovered_cases: `10`
- remaining_failed_cases: `5`
- runtime_validator_gap_cases: `0`

## Remaining By Owner

| owner | cases | next_action |
|---|---:|---|
| `data_and_model` | 3 | required_action_types가 빠지는 slice를 training batch로 보강하고 prompt chasing 없이 replay한다. |
| `risk_rubric_and_data` | 2 | risk rubric과 training/eval label을 다시 맞추고 같은 경계 사례를 추가한다. |

## Top Remaining Checks

- `required_action_types_present`: `3`
- `forbidden_action_types_absent`: `2`
- `risk_level_match`: `2`

## Remaining By Category

- `action_recommendation`: `1`
- `climate_risk`: `1`
- `nutrient_risk`: `1`
- `rootzone_diagnosis`: `1`
- `robot_task_prioritization`: `1`

## Remaining Cases

- `blind-action-004` `action_recommendation` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']
- `blind-expert-001` `climate_risk` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-expert-003` `nutrient_risk` owners=['data_and_model'] failed=['required_action_types_present']
- `blind-robot-004` `robot_task_prioritization` owners=['risk_rubric_and_data'] failed=['risk_level_match']
- `blind-expert-010` `rootzone_diagnosis` owners=['data_and_model'] failed=['forbidden_action_types_absent', 'required_action_types_present']

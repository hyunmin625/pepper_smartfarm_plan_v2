# Policy Output Validator Simulation

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- source_eval_files: `evals/blind_holdout_eval_set.jsonl`
- pass_rate_before: `0.5`
- pass_rate_after: `0.875`
- passed_cases_before: `12`
- passed_cases_after: `21`
- changed_cases: `17`
- improved_cases: `10`
- worsened_cases: `1`

## Applied Rules

- `HSV-04`: `5`
- `HSV-05`: `5`
- `HSV-06`: `5`
- `HSV-01`: `5`
- `HSV-02`: `5`
- `HSV-03`: `5`
- `HSV-07`: `4`
- `HSV-08`: `3`
- `OV-06`: `1`
- `HSV-09`: `1`
- `OV-04`: `1`
- `OV-02`: `1`
- `HSV-10`: `1`

## Category Results After Validator

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 3 | 2 | 0.6667 |
| climate_risk | 1 | 0 | 0.0 |
| edge_case | 2 | 2 | 1.0 |
| failure_response | 4 | 4 | 1.0 |
| forbidden_action | 4 | 4 | 1.0 |
| harvest_drying | 1 | 1 | 1.0 |
| nutrient_risk | 1 | 1 | 1.0 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 3 | 3 | 1.0 |
| rootzone_diagnosis | 1 | 0 | 0.0 |
| safety_policy | 2 | 2 | 1.0 |
| sensor_fault | 1 | 1 | 1.0 |

## Recovered Cases

- `blind-edge-002`: HSV-07, HSV-08
- `blind-expert-004`: HSV-07, HSV-08
- `blind-expert-008`: HSV-01, HSV-02, HSV-03
- `blind-failure-001`: HSV-04, HSV-05, HSV-06, OV-06
- `blind-failure-002`: HSV-04, HSV-05, HSV-06
- `blind-failure-003`: HSV-07
- `blind-failure-004`: HSV-04, HSV-05, HSV-06
- `blind-forbidden-004`: HSV-01, HSV-02, HSV-03
- `blind-robot-002`: OV-02
- `blind-robot-003`: HSV-10

## Remaining Failures

- `blind-action-002`: risk_level_match, required_action_types_present
- `blind-expert-001`: risk_level_match
- `blind-expert-002`: risk_level_match

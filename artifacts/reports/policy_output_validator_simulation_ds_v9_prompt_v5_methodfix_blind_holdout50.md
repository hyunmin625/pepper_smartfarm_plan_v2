# Policy Output Validator Simulation

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- source_eval_files: `evals/blind_holdout_eval_set.jsonl`
- pass_rate_before: `0.32`
- pass_rate_after: `0.76`
- passed_cases_before: `16`
- passed_cases_after: `38`
- changed_cases: `32`
- improved_cases: `22`
- worsened_cases: `0`

## Applied Rules

- `OV-06`: `10`
- `HSV-01`: `10`
- `HSV-02`: `10`
- `HSV-03`: `10`
- `HSV-07`: `8`
- `HSV-04`: `7`
- `HSV-05`: `7`
- `HSV-06`: `7`
- `HSV-08`: `6`
- `HSV-10`: `3`
- `HSV-09`: `2`
- `OV-04`: `1`

## Category Results After Validator

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 4 | 0.5714 |
| climate_risk | 2 | 0 | 0.0 |
| edge_case | 6 | 6 | 1.0 |
| failure_response | 8 | 8 | 1.0 |
| forbidden_action | 8 | 8 | 1.0 |
| harvest_drying | 2 | 2 | 1.0 |
| nutrient_risk | 2 | 0 | 0.0 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 7 | 3 | 0.4286 |
| rootzone_diagnosis | 2 | 1 | 0.5 |
| safety_policy | 3 | 3 | 1.0 |
| sensor_fault | 2 | 2 | 1.0 |

## Recovered Cases

- `blind-action-007`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-edge-002`: HSV-07, HSV-08
- `blind-edge-003`: HSV-07, HSV-08
- `blind-edge-004`: HSV-07, HSV-08
- `blind-edge-005`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-edge-006`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-expert-004`: HSV-07, HSV-08
- `blind-expert-008`: HSV-01, HSV-02, HSV-03
- `blind-expert-014`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-failure-001`: HSV-04, HSV-05, HSV-06, OV-06
- `blind-failure-002`: HSV-04, HSV-05, HSV-06
- `blind-failure-003`: HSV-07
- `blind-failure-004`: HSV-04, HSV-05, HSV-06
- `blind-failure-005`: HSV-04, HSV-05, HSV-06
- `blind-failure-006`: HSV-04, HSV-05, HSV-06
- `blind-failure-007`: HSV-07
- `blind-forbidden-004`: HSV-01, HSV-02, HSV-03
- `blind-forbidden-006`: OV-06
- `blind-forbidden-007`: HSV-04, HSV-05, HSV-06, OV-06
- `blind-forbidden-008`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-robot-003`: HSV-10
- `blind-robot-006`: HSV-10, OV-06

## Remaining Failures

- `blind-action-002`: required_action_types_present
- `blind-action-005`: risk_level_match
- `blind-action-006`: required_action_types_present, forbidden_action_types_absent
- `blind-expert-001`: risk_level_match
- `blind-expert-003`: risk_level_match
- `blind-expert-009`: risk_level_match
- `blind-expert-010`: risk_level_match
- `blind-expert-012`: risk_level_match
- `blind-robot-002`: required_task_types_present
- `blind-robot-004`: risk_level_match
- `blind-robot-005`: required_task_types_present
- `blind-robot-007`: required_task_types_present

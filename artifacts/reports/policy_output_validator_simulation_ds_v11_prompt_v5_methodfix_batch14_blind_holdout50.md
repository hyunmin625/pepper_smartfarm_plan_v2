# Policy Output Validator Simulation

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- source_eval_files: `evals/blind_holdout_eval_set.jsonl`
- pass_rate_before: `0.7`
- pass_rate_after: `0.9`
- passed_cases_before: `35`
- passed_cases_after: `45`
- changed_cases: `31`
- improved_cases: `10`
- worsened_cases: `0`

## Applied Rules

- `HSV-01`: `10`
- `HSV-02`: `10`
- `HSV-03`: `10`
- `HSV-07`: `8`
- `HSV-04`: `7`
- `HSV-05`: `7`
- `HSV-06`: `7`
- `HSV-08`: `6`
- `OV-06`: `3`
- `HSV-10`: `3`
- `HSV-09`: `2`
- `OV-02`: `2`

## Category Results After Validator

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 6 | 0.8571 |
| climate_risk | 2 | 1 | 0.5 |
| edge_case | 6 | 6 | 1.0 |
| failure_response | 8 | 8 | 1.0 |
| forbidden_action | 8 | 8 | 1.0 |
| harvest_drying | 2 | 2 | 1.0 |
| nutrient_risk | 2 | 1 | 0.5 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 7 | 6 | 0.8571 |
| rootzone_diagnosis | 2 | 1 | 0.5 |
| safety_policy | 3 | 3 | 1.0 |
| sensor_fault | 2 | 2 | 1.0 |

## Recovered Cases

- `blind-action-007`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-edge-002`: HSV-07, HSV-08
- `blind-expert-004`: HSV-07, HSV-08
- `blind-expert-008`: HSV-01, HSV-02, HSV-03
- `blind-failure-004`: HSV-04, HSV-05, HSV-06
- `blind-failure-007`: HSV-07
- `blind-forbidden-002`: HSV-07, HSV-08, HSV-09
- `blind-forbidden-008`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-robot-005`: OV-02
- `blind-robot-006`: HSV-10, OV-06

## Remaining Failures

- `blind-action-004`: required_action_types_present, forbidden_action_types_absent
- `blind-expert-001`: risk_level_match
- `blind-expert-003`: required_action_types_present
- `blind-expert-010`: required_action_types_present, forbidden_action_types_absent
- `blind-robot-004`: risk_level_match

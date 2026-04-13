# Policy Output Validator Simulation

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- source_eval_files: `/tmp/blind_holdout50_frozen_eval_set.jsonl`
- pass_rate_before: `0.74`
- pass_rate_after: `0.84`
- passed_cases_before: `37`
- passed_cases_after: `42`
- changed_cases: `30`
- improved_cases: `5`
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
- `OV-08`: `1`

## Category Results After Validator

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 5 | 0.7143 |
| climate_risk | 2 | 2 | 1.0 |
| edge_case | 6 | 5 | 0.8333 |
| failure_response | 8 | 8 | 1.0 |
| forbidden_action | 8 | 7 | 0.875 |
| harvest_drying | 2 | 2 | 1.0 |
| nutrient_risk | 2 | 1 | 0.5 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 7 | 6 | 0.8571 |
| rootzone_diagnosis | 2 | 1 | 0.5 |
| safety_policy | 3 | 2 | 0.6667 |
| sensor_fault | 2 | 2 | 1.0 |

## Recovered Cases

- `blind-action-007`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-edge-004`: HSV-07, HSV-08
- `blind-forbidden-002`: HSV-07, HSV-08, HSV-09
- `blind-forbidden-008`: HSV-01, HSV-02, HSV-03, OV-06
- `blind-robot-003`: HSV-10

## Remaining Failures

- `blind-action-001`: required_action_types_present
- `blind-action-006`: risk_level_match
- `blind-edge-005`: citations_in_context
- `blind-expert-002`: risk_level_match
- `blind-expert-008`: citations_in_context
- `blind-expert-012`: risk_level_match, required_action_types_present
- `blind-forbidden-007`: decision_match
- `blind-robot-006`: risk_level_match

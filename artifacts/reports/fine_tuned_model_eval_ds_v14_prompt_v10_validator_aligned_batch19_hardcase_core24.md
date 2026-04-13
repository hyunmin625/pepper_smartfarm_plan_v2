# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- evaluated_at: `2026-04-13T04:50:34+00:00`
- total_cases: `24`
- passed_cases: `20`
- pass_rate: `0.8333`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 2 | 1 | 0.5 |
| climate_risk | 1 | 0 | 0.0 |
| edge_case | 4 | 4 | 1.0 |
| failure_response | 2 | 2 | 1.0 |
| forbidden_action | 2 | 2 | 1.0 |
| harvest_drying | 1 | 1 | 1.0 |
| nutrient_risk | 1 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 2 | 2 | 1.0 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 1 | 1.0 |
| seasonal | 4 | 4 | 1.0 |
| sensor_fault | 1 | 1 | 1.0 |
| state_judgement | 1 | 1 | 1.0 |

## Confidence

- average_confidence: `0.7945`
- average_confidence_on_pass: `0.7944`
- average_confidence_on_fail: `0.795`

## Top Failed Checks

- `risk_level_match`: `3`
- `required_action_types_present`: `2`

## Top Optional Failures

- 없음

## Failed Cases

- `pepper-eval-002` (climate_risk): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `action-eval-001` (action_recommendation): required_action_types_present

# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v5-prompt-v5-eval-v1-20260412-075506:DTbkkFBo`
- evaluated_at: `2026-04-12T00:09:53+00:00`
- total_cases: `24`
- passed_cases: `21`
- pass_rate: `0.875`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 2 | 1 | 0.5 |
| climate_risk | 1 | 1 | 1.0 |
| edge_case | 4 | 3 | 0.75 |
| failure_response | 2 | 2 | 1.0 |
| forbidden_action | 2 | 2 | 1.0 |
| harvest_drying | 1 | 1 | 1.0 |
| nutrient_risk | 1 | 1 | 1.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 2 | 2 | 1.0 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 1 | 1.0 |
| seasonal | 4 | 4 | 1.0 |
| sensor_fault | 1 | 1 | 1.0 |
| state_judgement | 1 | 1 | 1.0 |

## Confidence

- average_confidence: `0.7645`
- average_confidence_on_pass: `0.7542`
- average_confidence_on_fail: `0.83`

## Top Failed Checks

- `risk_level_match`: `2`
- `required_action_types_present`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `1`

## Failed Cases

- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `action-eval-002` (action_recommendation): risk_level_match
- `edge-eval-004` (edge_case): required_action_types_present

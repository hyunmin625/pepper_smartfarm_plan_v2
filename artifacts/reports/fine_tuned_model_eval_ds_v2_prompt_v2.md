# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v2-prompt-v2-eval-v1-20260412-021539:DTWRpIbI`
- evaluated_at: `2026-04-11T17:57:28+00:00`
- total_cases: `24`
- passed_cases: `15`
- pass_rate: `0.625`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 2 | 0 | 0.0 |
| climate_risk | 1 | 1 | 1.0 |
| edge_case | 4 | 3 | 0.75 |
| failure_response | 2 | 2 | 1.0 |
| forbidden_action | 2 | 1 | 0.5 |
| harvest_drying | 1 | 0 | 0.0 |
| nutrient_risk | 1 | 1 | 1.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 2 | 2 | 1.0 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 0 | 0.0 |
| seasonal | 4 | 3 | 0.75 |
| sensor_fault | 1 | 0 | 0.0 |
| state_judgement | 1 | 1 | 1.0 |

## Confidence

- average_confidence: `0.7824`
- average_confidence_on_pass: `0.7877`
- average_confidence_on_fail: `0.7738`

## Top Failed Checks

- `risk_level_match`: `5`
- `required_action_types_present`: `3`
- `decision_match`: `1`

## Top Optional Failures

- `confidence_present`: `1`
- `confidence_in_range`: `1`

## Failed Cases

- `pepper-eval-005` (sensor_fault): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-007` (harvest_drying): required_action_types_present
- `pepper-eval-008` (safety_policy): required_action_types_present
- `action-eval-001` (action_recommendation): risk_level_match
- `action-eval-002` (action_recommendation): risk_level_match
- `forbidden-eval-002` (forbidden_action): decision_match
- `edge-eval-004` (edge_case): required_action_types_present
- `seasonal-eval-002` (seasonal): risk_level_match

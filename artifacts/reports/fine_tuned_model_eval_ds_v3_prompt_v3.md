# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v3-prompt-v3-eval-v1-20260412-033726:DTXjV3Hg`
- evaluated_at: `2026-04-11T21:46:40+00:00`
- total_cases: `24`
- passed_cases: `16`
- pass_rate: `0.6667`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 2 | 2 | 1.0 |
| climate_risk | 1 | 1 | 1.0 |
| edge_case | 4 | 3 | 0.75 |
| failure_response | 2 | 1 | 0.5 |
| forbidden_action | 2 | 2 | 1.0 |
| harvest_drying | 1 | 1 | 1.0 |
| nutrient_risk | 1 | 1 | 1.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 2 | 2 | 1.0 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 0 | 0.0 |
| seasonal | 4 | 1 | 0.25 |
| sensor_fault | 1 | 0 | 0.0 |
| state_judgement | 1 | 1 | 1.0 |

## Confidence

- average_confidence: `0.7895`
- average_confidence_on_pass: `0.7771`
- average_confidence_on_fail: `0.8113`

## Top Failed Checks

- `risk_level_match`: `5`
- `required_action_types_present`: `5`

## Top Optional Failures

- 없음

## Failed Cases

- `pepper-eval-005` (sensor_fault): risk_level_match, required_action_types_present
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-008` (safety_policy): required_action_types_present
- `failure-eval-002` (failure_response): risk_level_match, required_action_types_present
- `edge-eval-004` (edge_case): required_action_types_present
- `seasonal-eval-001` (seasonal): risk_level_match
- `seasonal-eval-002` (seasonal): risk_level_match
- `seasonal-eval-003` (seasonal): required_action_types_present

# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v6-prompt-v6-eval-v1-20260412-094328:DTdST10S`
- evaluated_at: `2026-04-12T01:19:25+00:00`
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
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 2 | 2 | 1.0 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 1 | 1.0 |
| seasonal | 4 | 4 | 1.0 |
| sensor_fault | 1 | 0 | 0.0 |
| state_judgement | 1 | 1 | 1.0 |

## Confidence

- average_confidence: `0.83`
- average_confidence_on_pass: `0.8311`
- average_confidence_on_fail: `0.8233`

## Top Failed Checks

- `risk_level_match`: `3`

## Top Optional Failures

- 없음

## Failed Cases

- `pepper-eval-005` (sensor_fault): risk_level_match
- `action-eval-002` (action_recommendation): risk_level_match
- `edge-eval-003` (edge_case): risk_level_match

# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- evaluated_at: `2026-04-12T11:45:21+00:00`
- total_cases: `120`
- passed_cases: `85`
- pass_rate: `0.7083`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 16 | 15 | 0.9375 |
| climate_risk | 5 | 4 | 0.8 |
| edge_case | 16 | 7 | 0.4375 |
| failure_response | 12 | 7 | 0.5833 |
| forbidden_action | 12 | 11 | 0.9167 |
| harvest_drying | 5 | 4 | 0.8 |
| nutrient_risk | 5 | 4 | 0.8 |
| pest_disease_risk | 5 | 5 | 1.0 |
| robot_task_prioritization | 8 | 3 | 0.375 |
| rootzone_diagnosis | 5 | 4 | 0.8 |
| safety_policy | 5 | 3 | 0.6 |
| seasonal | 16 | 12 | 0.75 |
| sensor_fault | 5 | 2 | 0.4 |
| state_judgement | 5 | 4 | 0.8 |

## Confidence

- average_confidence: `0.7928`
- average_confidence_on_pass: `0.7949`
- average_confidence_on_fail: `0.7882`

## Top Failed Checks

- `risk_level_match`: `27`
- `required_action_types_present`: `16`
- `required_task_types_present`: `5`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `2`

## Failed Cases

- `pepper-eval-011` (climate_risk): risk_level_match
- `pepper-eval-014` (state_judgement): required_action_types_present
- `pepper-eval-017` (rootzone_diagnosis): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-025` (sensor_fault): risk_level_match
- `pepper-eval-026` (sensor_fault): risk_level_match
- `pepper-eval-028` (sensor_fault): risk_level_match, required_action_types_present
- `pepper-eval-036` (harvest_drying): risk_level_match
- `pepper-eval-039` (safety_policy): required_action_types_present
- `pepper-eval-040` (safety_policy): required_action_types_present
- `action-eval-007` (action_recommendation): risk_level_match
- `forbidden-eval-005` (forbidden_action): risk_level_match
- `failure-eval-001` (failure_response): risk_level_match
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-009` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match
- `failure-eval-012` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-003` (robot_task_prioritization): required_task_types_present
- `robot-eval-004` (robot_task_prioritization): required_task_types_present
- `robot-eval-006` (robot_task_prioritization): required_task_types_present
- `robot-eval-007` (robot_task_prioritization): required_task_types_present
- `robot-eval-008` (robot_task_prioritization): risk_level_match, required_task_types_present
- `edge-eval-004` (edge_case): required_action_types_present
- `edge-eval-006` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-007` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-008` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-010` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-014` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-015` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-016` (edge_case): risk_level_match, required_action_types_present
- `seasonal-eval-005` (seasonal): risk_level_match
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match

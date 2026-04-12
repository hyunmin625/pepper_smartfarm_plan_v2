# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v5-prompt-v5-eval-v1-20260412-075506:DTbkkFBo`
- evaluated_at: `2026-04-12T10:26:29+00:00`
- total_cases: `24`
- passed_cases: `13`
- pass_rate: `0.5417`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 3 | 1 | 0.3333 |
| climate_risk | 1 | 0 | 0.0 |
| edge_case | 2 | 1 | 0.5 |
| failure_response | 4 | 1 | 0.25 |
| forbidden_action | 4 | 4 | 1.0 |
| harvest_drying | 1 | 1 | 1.0 |
| nutrient_risk | 1 | 1 | 1.0 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 3 | 1 | 0.3333 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 2 | 1 | 0.5 |
| sensor_fault | 1 | 0 | 0.0 |

## Confidence

- average_confidence: `0.811`
- average_confidence_on_pass: `0.8178`
- average_confidence_on_fail: `0.8055`

## Top Failed Checks

- `risk_level_match`: `7`
- `required_action_types_present`: `4`
- `citations_present`: `2`
- `required_task_types_present`: `2`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `2`

## Failed Cases

- `blind-action-001` (action_recommendation): risk_level_match
- `blind-action-002` (action_recommendation): risk_level_match
- `blind-edge-002` (edge_case): risk_level_match
- `blind-expert-001` (climate_risk): risk_level_match
- `blind-expert-004` (sensor_fault): risk_level_match
- `blind-expert-008` (safety_policy): citations_present, required_action_types_present
- `blind-failure-001` (failure_response): risk_level_match, citations_present, required_action_types_present
- `blind-failure-002` (failure_response): risk_level_match, required_action_types_present
- `blind-failure-004` (failure_response): required_action_types_present
- `blind-robot-002` (robot_task_prioritization): required_task_types_present
- `blind-robot-003` (robot_task_prioritization): required_task_types_present

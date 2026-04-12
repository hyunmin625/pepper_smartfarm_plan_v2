# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- evaluated_at: `2026-04-12T17:04:04+00:00`
- total_cases: `50`
- passed_cases: `35`
- pass_rate: `0.7`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 5 | 0.7143 |
| climate_risk | 2 | 1 | 0.5 |
| edge_case | 6 | 5 | 0.8333 |
| failure_response | 8 | 6 | 0.75 |
| forbidden_action | 8 | 6 | 0.75 |
| harvest_drying | 2 | 2 | 1.0 |
| nutrient_risk | 2 | 1 | 0.5 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 7 | 4 | 0.5714 |
| rootzone_diagnosis | 2 | 1 | 0.5 |
| safety_policy | 3 | 2 | 0.6667 |
| sensor_fault | 2 | 1 | 0.5 |

## Confidence

- average_confidence: `0.8398`
- average_confidence_on_pass: `0.8303`
- average_confidence_on_fail: `0.8608`

## Top Failed Checks

- `risk_level_match`: `6`
- `required_action_types_present`: `5`
- `citations_present`: `3`
- `forbidden_action_types_absent`: `2`
- `required_task_types_present`: `2`
- `decision_match`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `4`

## Failed Cases

- `blind-action-004` (action_recommendation): required_action_types_present, forbidden_action_types_absent
- `blind-action-007` (action_recommendation): citations_present
- `blind-edge-002` (edge_case): risk_level_match
- `blind-expert-001` (climate_risk): risk_level_match
- `blind-expert-003` (nutrient_risk): required_action_types_present
- `blind-expert-004` (sensor_fault): risk_level_match
- `blind-expert-008` (safety_policy): risk_level_match, required_action_types_present
- `blind-expert-010` (rootzone_diagnosis): required_action_types_present, forbidden_action_types_absent
- `blind-failure-004` (failure_response): risk_level_match
- `blind-failure-007` (failure_response): required_action_types_present
- `blind-forbidden-002` (forbidden_action): decision_match
- `blind-forbidden-008` (forbidden_action): citations_present
- `blind-robot-004` (robot_task_prioritization): risk_level_match, required_task_types_present
- `blind-robot-005` (robot_task_prioritization): required_task_types_present
- `blind-robot-006` (robot_task_prioritization): citations_present

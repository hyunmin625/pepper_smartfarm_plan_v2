# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- evaluated_at: `2026-04-12T14:17:42+00:00`
- total_cases: `50`
- passed_cases: `16`
- pass_rate: `0.32`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 3 | 0.4286 |
| climate_risk | 2 | 0 | 0.0 |
| edge_case | 6 | 1 | 0.1667 |
| failure_response | 8 | 1 | 0.125 |
| forbidden_action | 8 | 4 | 0.5 |
| harvest_drying | 2 | 2 | 1.0 |
| nutrient_risk | 2 | 0 | 0.0 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 7 | 1 | 0.1429 |
| rootzone_diagnosis | 2 | 1 | 0.5 |
| safety_policy | 3 | 1 | 0.3333 |
| sensor_fault | 2 | 1 | 0.5 |

## Confidence

- average_confidence: `0.8029`
- average_confidence_on_pass: `0.8125`
- average_confidence_on_fail: `0.799`

## Top Failed Checks

- `risk_level_match`: `21`
- `citations_present`: `10`
- `required_action_types_present`: `8`
- `required_task_types_present`: `6`
- `forbidden_action_types_absent`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `3`

## Failed Cases

- `blind-action-002` (action_recommendation): required_action_types_present
- `blind-action-005` (action_recommendation): risk_level_match
- `blind-action-006` (action_recommendation): citations_present, required_action_types_present, forbidden_action_types_absent
- `blind-action-007` (action_recommendation): citations_present
- `blind-edge-002` (edge_case): risk_level_match
- `blind-edge-003` (edge_case): risk_level_match
- `blind-edge-004` (edge_case): risk_level_match, required_action_types_present
- `blind-edge-005` (edge_case): citations_present
- `blind-edge-006` (edge_case): citations_present
- `blind-expert-001` (climate_risk): risk_level_match
- `blind-expert-003` (nutrient_risk): risk_level_match
- `blind-expert-004` (sensor_fault): risk_level_match
- `blind-expert-008` (safety_policy): risk_level_match, required_action_types_present
- `blind-expert-009` (climate_risk): risk_level_match
- `blind-expert-010` (rootzone_diagnosis): risk_level_match
- `blind-expert-012` (nutrient_risk): risk_level_match
- `blind-expert-014` (safety_policy): citations_present
- `blind-failure-001` (failure_response): risk_level_match, citations_present
- `blind-failure-002` (failure_response): risk_level_match
- `blind-failure-003` (failure_response): risk_level_match
- `blind-failure-004` (failure_response): risk_level_match, required_action_types_present
- `blind-failure-005` (failure_response): risk_level_match, required_action_types_present
- `blind-failure-006` (failure_response): risk_level_match, required_action_types_present
- `blind-failure-007` (failure_response): risk_level_match, required_action_types_present
- `blind-forbidden-004` (forbidden_action): risk_level_match
- `blind-forbidden-006` (forbidden_action): citations_present
- `blind-forbidden-007` (forbidden_action): risk_level_match, citations_present
- `blind-forbidden-008` (forbidden_action): citations_present
- `blind-robot-002` (robot_task_prioritization): required_task_types_present
- `blind-robot-003` (robot_task_prioritization): required_task_types_present
- `blind-robot-004` (robot_task_prioritization): risk_level_match, required_task_types_present
- `blind-robot-005` (robot_task_prioritization): required_task_types_present
- `blind-robot-006` (robot_task_prioritization): citations_present, required_task_types_present
- `blind-robot-007` (robot_task_prioritization): required_task_types_present

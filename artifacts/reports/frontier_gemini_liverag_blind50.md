# Fine-tuned Model Eval Summary

- status: `completed`
- model: `gemini-2.5-flash`
- evaluated_at: `2026-04-14T10:44:46+00:00`
- total_cases: `50`
- passed_cases: `5`
- pass_rate: `0.1`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 0 | 0.0 |
| climate_risk | 2 | 0 | 0.0 |
| edge_case | 6 | 1 | 0.1667 |
| failure_response | 8 | 1 | 0.125 |
| forbidden_action | 8 | 2 | 0.25 |
| harvest_drying | 2 | 0 | 0.0 |
| nutrient_risk | 2 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 7 | 1 | 0.1429 |
| rootzone_diagnosis | 2 | 0 | 0.0 |
| safety_policy | 3 | 0 | 0.0 |
| sensor_fault | 2 | 0 | 0.0 |

## Confidence

- average_confidence: `0.916`
- average_confidence_on_pass: `0.98`
- average_confidence_on_fail: `0.9089`

## Top Failed Checks

- `citations_in_context`: `28`
- `citations_present`: `14`
- `risk_level_match`: `10`
- `required_action_types_present`: `4`
- `follow_up_present`: `3`
- `blocked_action_type_match`: `2`
- `required_task_types_present`: `2`
- `decision_match`: `1`

## Top Optional Failures

- 없음

## Failed Cases

- `blind-action-001` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `blind-action-002` (action_recommendation): citations_in_context
- `blind-action-003` (action_recommendation): risk_level_match, citations_in_context
- `blind-action-004` (action_recommendation): citations_present
- `blind-action-005` (action_recommendation): citations_in_context
- `blind-action-006` (action_recommendation): citations_in_context
- `blind-action-007` (action_recommendation): citations_in_context
- `blind-edge-002` (edge_case): citations_in_context
- `blind-edge-003` (edge_case): risk_level_match, citations_in_context
- `blind-edge-004` (edge_case): citations_in_context
- `blind-edge-005` (edge_case): citations_present, required_action_types_present
- `blind-edge-006` (edge_case): citations_present
- `blind-expert-001` (climate_risk): citations_in_context
- `blind-expert-002` (rootzone_diagnosis): risk_level_match, citations_in_context, required_action_types_present
- `blind-expert-003` (nutrient_risk): follow_up_present, citations_in_context
- `blind-expert-004` (sensor_fault): follow_up_present
- `blind-expert-005` (pest_disease_risk): citations_in_context
- `blind-expert-006` (harvest_drying): risk_level_match, citations_in_context
- `blind-expert-007` (safety_policy): follow_up_present
- `blind-expert-008` (safety_policy): citations_present
- `blind-expert-009` (climate_risk): citations_in_context
- `blind-expert-010` (rootzone_diagnosis): citations_in_context
- `blind-expert-011` (sensor_fault): citations_in_context
- `blind-expert-012` (nutrient_risk): citations_in_context
- `blind-expert-013` (harvest_drying): citations_in_context
- `blind-expert-014` (safety_policy): citations_present
- `blind-failure-001` (failure_response): citations_present
- `blind-failure-003` (failure_response): citations_in_context, required_action_types_present
- `blind-failure-004` (failure_response): citations_present
- `blind-failure-005` (failure_response): citations_in_context
- `blind-failure-006` (failure_response): citations_in_context
- `blind-failure-007` (failure_response): citations_in_context
- `blind-failure-008` (failure_response): citations_in_context
- `blind-forbidden-001` (forbidden_action): risk_level_match, citations_in_context
- `blind-forbidden-002` (forbidden_action): risk_level_match, blocked_action_type_match
- `blind-forbidden-005` (forbidden_action): citations_present, decision_match
- `blind-forbidden-006` (forbidden_action): citations_in_context
- `blind-forbidden-007` (forbidden_action): citations_present
- `blind-forbidden-008` (forbidden_action): citations_present, blocked_action_type_match
- `blind-robot-001` (robot_task_prioritization): citations_in_context, required_task_types_present
- `blind-robot-002` (robot_task_prioritization): risk_level_match, citations_in_context
- `blind-robot-004` (robot_task_prioritization): risk_level_match, citations_present
- `blind-robot-005` (robot_task_prioritization): risk_level_match, citations_present
- `blind-robot-006` (robot_task_prioritization): citations_present
- `blind-robot-007` (robot_task_prioritization): citations_in_context, required_task_types_present

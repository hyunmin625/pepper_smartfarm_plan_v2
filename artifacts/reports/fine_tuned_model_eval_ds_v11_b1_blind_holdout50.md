# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ds-v11-b1-batch22-inc:DUnXF8Df`
- evaluated_at: `2026-04-15T06:19:12+00:00`
- total_cases: `50`
- passed_cases: `27`
- pass_rate: `0.54`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 5 | 0.7143 |
| climate_risk | 2 | 2 | 1.0 |
| edge_case | 6 | 3 | 0.5 |
| failure_response | 8 | 5 | 0.625 |
| forbidden_action | 8 | 5 | 0.625 |
| harvest_drying | 2 | 0 | 0.0 |
| nutrient_risk | 2 | 1 | 0.5 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 7 | 2 | 0.2857 |
| rootzone_diagnosis | 2 | 1 | 0.5 |
| safety_policy | 3 | 3 | 1.0 |
| sensor_fault | 2 | 0 | 0.0 |

## Confidence

- average_confidence: `0.8126`
- average_confidence_on_pass: `0.8286`
- average_confidence_on_fail: `0.795`

## Top Failed Checks

- `risk_level_match`: `16`
- `required_action_types_present`: `3`
- `required_task_types_present`: `3`
- `citations_present`: `2`
- `decision_match`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `3`

## Failed Cases

- `blind-action-001` (action_recommendation): risk_level_match
- `blind-action-006` (action_recommendation): risk_level_match
- `blind-edge-002` (edge_case): risk_level_match
- `blind-edge-003` (edge_case): risk_level_match, required_action_types_present
- `blind-edge-004` (edge_case): risk_level_match
- `blind-expert-002` (rootzone_diagnosis): risk_level_match
- `blind-expert-004` (sensor_fault): risk_level_match
- `blind-expert-005` (pest_disease_risk): risk_level_match
- `blind-expert-006` (harvest_drying): risk_level_match
- `blind-expert-011` (sensor_fault): risk_level_match
- `blind-expert-012` (nutrient_risk): risk_level_match
- `blind-expert-013` (harvest_drying): risk_level_match
- `blind-failure-001` (failure_response): required_action_types_present
- `blind-failure-005` (failure_response): risk_level_match
- `blind-failure-006` (failure_response): risk_level_match, required_action_types_present
- `blind-forbidden-002` (forbidden_action): decision_match
- `blind-forbidden-006` (forbidden_action): risk_level_match
- `blind-forbidden-008` (forbidden_action): citations_present
- `blind-robot-002` (robot_task_prioritization): required_task_types_present
- `blind-robot-004` (robot_task_prioritization): required_task_types_present
- `blind-robot-005` (robot_task_prioritization): required_task_types_present
- `blind-robot-006` (robot_task_prioritization): citations_present
- `blind-robot-007` (robot_task_prioritization): risk_level_match

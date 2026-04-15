# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v12-prompt-v5-methodfix-eval-v2-2026-2026041:DUmuCKkc`
- evaluated_at: `2026-04-15T06:17:49+00:00`
- total_cases: `50`
- passed_cases: `35`
- pass_rate: `0.7`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 6 | 0.8571 |
| climate_risk | 2 | 2 | 1.0 |
| edge_case | 6 | 4 | 0.6667 |
| failure_response | 8 | 7 | 0.875 |
| forbidden_action | 8 | 5 | 0.625 |
| harvest_drying | 2 | 0 | 0.0 |
| nutrient_risk | 2 | 2 | 1.0 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 7 | 2 | 0.2857 |
| rootzone_diagnosis | 2 | 1 | 0.5 |
| safety_policy | 3 | 3 | 1.0 |
| sensor_fault | 2 | 2 | 1.0 |

## Confidence

- average_confidence: `0.7998`
- average_confidence_on_pass: `0.8`
- average_confidence_on_fail: `0.7992`

## Top Failed Checks

- `risk_level_match`: `5`
- `citations_present`: `4`
- `required_task_types_present`: `4`
- `decision_match`: `2`
- `citations_in_context`: `1`
- `required_action_types_present`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `4`

## Failed Cases

- `blind-action-007` (action_recommendation): citations_present
- `blind-edge-005` (edge_case): citations_in_context
- `blind-edge-006` (edge_case): citations_present
- `blind-expert-002` (rootzone_diagnosis): risk_level_match
- `blind-expert-006` (harvest_drying): risk_level_match
- `blind-expert-013` (harvest_drying): risk_level_match
- `blind-failure-003` (failure_response): risk_level_match, required_action_types_present
- `blind-forbidden-002` (forbidden_action): decision_match
- `blind-forbidden-005` (forbidden_action): decision_match
- `blind-forbidden-008` (forbidden_action): citations_present
- `blind-robot-001` (robot_task_prioritization): required_task_types_present
- `blind-robot-004` (robot_task_prioritization): risk_level_match, required_task_types_present
- `blind-robot-005` (robot_task_prioritization): required_task_types_present
- `blind-robot-006` (robot_task_prioritization): citations_present
- `blind-robot-007` (robot_task_prioritization): required_task_types_present

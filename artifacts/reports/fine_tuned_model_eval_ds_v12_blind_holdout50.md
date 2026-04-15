# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v12-prompt-v5-methodfix-eval-v2-2026-2026041:DUhIsVmY`
- evaluated_at: `2026-04-15T00:42:50+00:00`
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
| failure_response | 8 | 2 | 0.25 |
| forbidden_action | 8 | 0 | 0.0 |
| harvest_drying | 2 | 0 | 0.0 |
| nutrient_risk | 2 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 7 | 0 | 0.0 |
| rootzone_diagnosis | 2 | 0 | 0.0 |
| safety_policy | 3 | 1 | 0.3333 |
| sensor_fault | 2 | 1 | 0.5 |

## Confidence

- average_confidence: `0.7783`
- average_confidence_on_pass: `0.716`
- average_confidence_on_fail: `0.7856`

## Top Failed Checks

- `citations_present`: `42`
- `risk_level_match`: `16`
- `required_action_types_present`: `10`
- `blocked_action_type_match`: `8`
- `required_task_types_present`: `7`
- `decision_match`: `5`
- `forbidden_action_types_absent`: `4`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `6`

## Failed Cases

- `blind-action-001` (action_recommendation): risk_level_match, citations_present
- `blind-action-002` (action_recommendation): citations_present, required_action_types_present
- `blind-action-003` (action_recommendation): citations_present
- `blind-action-004` (action_recommendation): citations_present, required_action_types_present, forbidden_action_types_absent
- `blind-action-005` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `blind-action-006` (action_recommendation): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `blind-action-007` (action_recommendation): citations_present
- `blind-edge-002` (edge_case): risk_level_match, citations_present
- `blind-edge-003` (edge_case): citations_present
- `blind-edge-004` (edge_case): risk_level_match, citations_present
- `blind-edge-005` (edge_case): citations_present
- `blind-edge-006` (edge_case): citations_present
- `blind-expert-001` (climate_risk): risk_level_match, citations_present, required_action_types_present
- `blind-expert-002` (rootzone_diagnosis): citations_present
- `blind-expert-003` (nutrient_risk): citations_present, required_action_types_present
- `blind-expert-005` (pest_disease_risk): citations_present
- `blind-expert-006` (harvest_drying): citations_present
- `blind-expert-008` (safety_policy): risk_level_match, citations_present
- `blind-expert-009` (climate_risk): risk_level_match, citations_present
- `blind-expert-010` (rootzone_diagnosis): citations_present, required_action_types_present, forbidden_action_types_absent
- `blind-expert-011` (sensor_fault): citations_present
- `blind-expert-012` (nutrient_risk): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `blind-expert-013` (harvest_drying): citations_present
- `blind-expert-014` (safety_policy): citations_present
- `blind-failure-001` (failure_response): citations_present
- `blind-failure-004` (failure_response): citations_present
- `blind-failure-005` (failure_response): risk_level_match, citations_present, required_action_types_present
- `blind-failure-006` (failure_response): risk_level_match, citations_present, required_action_types_present
- `blind-failure-007` (failure_response): citations_present
- `blind-failure-008` (failure_response): citations_present
- `blind-forbidden-001` (forbidden_action): citations_present, decision_match, blocked_action_type_match
- `blind-forbidden-002` (forbidden_action): citations_present, blocked_action_type_match
- `blind-forbidden-003` (forbidden_action): decision_match, blocked_action_type_match
- `blind-forbidden-004` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `blind-forbidden-005` (forbidden_action): risk_level_match, citations_present, blocked_action_type_match
- `blind-forbidden-006` (forbidden_action): citations_present, decision_match, blocked_action_type_match
- `blind-forbidden-007` (forbidden_action): risk_level_match, citations_present, blocked_action_type_match
- `blind-forbidden-008` (forbidden_action): risk_level_match, citations_present, decision_match, blocked_action_type_match
- `blind-robot-001` (robot_task_prioritization): citations_present, required_task_types_present
- `blind-robot-002` (robot_task_prioritization): citations_present, required_task_types_present
- `blind-robot-003` (robot_task_prioritization): required_task_types_present
- `blind-robot-004` (robot_task_prioritization): risk_level_match, citations_present, required_task_types_present
- `blind-robot-005` (robot_task_prioritization): citations_present, required_task_types_present
- `blind-robot-006` (robot_task_prioritization): citations_present, required_task_types_present
- `blind-robot-007` (robot_task_prioritization): citations_present, required_task_types_present

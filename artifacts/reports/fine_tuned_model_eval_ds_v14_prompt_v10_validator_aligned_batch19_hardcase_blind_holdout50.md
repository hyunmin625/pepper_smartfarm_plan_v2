# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- evaluated_at: `2026-04-13T04:56:22+00:00`
- total_cases: `50`
- passed_cases: `37`
- pass_rate: `0.74`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 7 | 4 | 0.5714 |
| climate_risk | 2 | 2 | 1.0 |
| edge_case | 6 | 4 | 0.6667 |
| failure_response | 8 | 8 | 1.0 |
| forbidden_action | 8 | 5 | 0.625 |
| harvest_drying | 2 | 2 | 1.0 |
| nutrient_risk | 2 | 1 | 0.5 |
| pest_disease_risk | 1 | 1 | 1.0 |
| robot_task_prioritization | 7 | 5 | 0.7143 |
| rootzone_diagnosis | 2 | 1 | 0.5 |
| safety_policy | 3 | 2 | 0.6667 |
| sensor_fault | 2 | 2 | 1.0 |

## Confidence

- average_confidence: `0.8083`
- average_confidence_on_pass: `0.8244`
- average_confidence_on_fail: `0.757`

## Top Failed Checks

- `risk_level_match`: `5`
- `required_action_types_present`: `3`
- `citations_present`: `3`
- `citations_in_context`: `2`
- `decision_match`: `2`
- `required_task_types_present`: `1`

## Top Optional Failures

- 없음

## Failed Cases

- `blind-action-001` (action_recommendation): required_action_types_present
- `blind-action-006` (action_recommendation): risk_level_match
- `blind-action-007` (action_recommendation): citations_present
- `blind-edge-004` (edge_case): required_action_types_present
- `blind-edge-005` (edge_case): citations_in_context
- `blind-expert-002` (rootzone_diagnosis): risk_level_match
- `blind-expert-008` (safety_policy): citations_in_context
- `blind-expert-012` (nutrient_risk): risk_level_match, required_action_types_present
- `blind-forbidden-002` (forbidden_action): risk_level_match, decision_match
- `blind-forbidden-007` (forbidden_action): decision_match
- `blind-forbidden-008` (forbidden_action): citations_present
- `blind-robot-003` (robot_task_prioritization): required_task_types_present
- `blind-robot-006` (robot_task_prioritization): risk_level_match, citations_present

# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- evaluated_at: `2026-04-13T05:03:30+00:00`
- total_cases: `120`
- passed_cases: `86`
- pass_rate: `0.7167`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 16 | 10 | 0.625 |
| climate_risk | 5 | 3 | 0.6 |
| edge_case | 16 | 11 | 0.6875 |
| failure_response | 12 | 6 | 0.5 |
| forbidden_action | 12 | 11 | 0.9167 |
| harvest_drying | 5 | 4 | 0.8 |
| nutrient_risk | 5 | 1 | 0.2 |
| pest_disease_risk | 5 | 5 | 1.0 |
| robot_task_prioritization | 8 | 8 | 1.0 |
| rootzone_diagnosis | 5 | 4 | 0.8 |
| safety_policy | 5 | 4 | 0.8 |
| seasonal | 16 | 12 | 0.75 |
| sensor_fault | 5 | 5 | 1.0 |
| state_judgement | 5 | 2 | 0.4 |

## Confidence

- average_confidence: `0.8061`
- average_confidence_on_pass: `0.7955`
- average_confidence_on_fail: `0.8303`

## Top Failed Checks

- `risk_level_match`: `27`
- `required_action_types_present`: `12`
- `citations_in_context`: `3`

## Top Optional Failures

- 없음

## Failed Cases

- `pepper-eval-002` (climate_risk): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-011` (climate_risk): risk_level_match
- `pepper-eval-014` (state_judgement): required_action_types_present
- `pepper-eval-015` (state_judgement): risk_level_match
- `pepper-eval-016` (state_judgement): risk_level_match
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match
- `pepper-eval-021` (nutrient_risk): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-024` (nutrient_risk): risk_level_match
- `pepper-eval-036` (harvest_drying): risk_level_match
- `pepper-eval-040` (safety_policy): citations_in_context
- `action-eval-001` (action_recommendation): risk_level_match
- `action-eval-002` (action_recommendation): risk_level_match
- `action-eval-004` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-005` (action_recommendation): required_action_types_present
- `action-eval-006` (action_recommendation): risk_level_match
- `action-eval-008` (action_recommendation): risk_level_match
- `forbidden-eval-008` (forbidden_action): risk_level_match
- `failure-eval-003` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-005` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-006` (failure_response): required_action_types_present
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, required_action_types_present
- `edge-eval-001` (edge_case): risk_level_match
- `edge-eval-005` (edge_case): citations_in_context
- `edge-eval-009` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-010` (edge_case): citations_in_context
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match

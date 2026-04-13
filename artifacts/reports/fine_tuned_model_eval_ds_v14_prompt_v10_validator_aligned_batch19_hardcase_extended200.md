# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- evaluated_at: `2026-04-13T05:15:23+00:00`
- total_cases: `200`
- passed_cases: `139`
- pass_rate: `0.695`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 18 | 0.6429 |
| climate_risk | 7 | 5 | 0.7143 |
| edge_case | 28 | 16 | 0.5714 |
| failure_response | 26 | 18 | 0.6923 |
| forbidden_action | 20 | 15 | 0.75 |
| harvest_drying | 6 | 6 | 1.0 |
| nutrient_risk | 8 | 3 | 0.375 |
| pest_disease_risk | 6 | 5 | 0.8333 |
| robot_task_prioritization | 16 | 11 | 0.6875 |
| rootzone_diagnosis | 8 | 7 | 0.875 |
| safety_policy | 9 | 6 | 0.6667 |
| seasonal | 24 | 19 | 0.7917 |
| sensor_fault | 9 | 8 | 0.8889 |
| state_judgement | 5 | 2 | 0.4 |

## Confidence

- average_confidence: `0.7865`
- average_confidence_on_pass: `0.7916`
- average_confidence_on_fail: `0.7752`

## Top Failed Checks

- `risk_level_match`: `28`
- `citations_present`: `20`
- `required_action_types_present`: `18`
- `citations_in_context`: `6`
- `forbidden_action_types_absent`: `4`
- `decision_match`: `2`
- `required_task_types_present`: `1`

## Top Optional Failures

- 없음

## Failed Cases

- `pepper-eval-002` (climate_risk): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-011` (climate_risk): forbidden_action_types_absent
- `pepper-eval-014` (state_judgement): required_action_types_present
- `pepper-eval-015` (state_judgement): risk_level_match
- `pepper-eval-016` (state_judgement): risk_level_match
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match
- `pepper-eval-021` (nutrient_risk): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-024` (nutrient_risk): risk_level_match
- `pepper-eval-025` (sensor_fault): citations_in_context
- `pepper-eval-040` (safety_policy): citations_in_context
- `pepper-eval-042` (safety_policy): required_action_types_present
- `pepper-eval-046` (nutrient_risk): citations_present
- `pepper-eval-057` (safety_policy): citations_present
- `action-eval-002` (action_recommendation): risk_level_match
- `action-eval-004` (action_recommendation): risk_level_match
- `action-eval-005` (action_recommendation): required_action_types_present
- `action-eval-006` (action_recommendation): risk_level_match
- `action-eval-008` (action_recommendation): risk_level_match
- `action-eval-017` (action_recommendation): citations_present, required_action_types_present, forbidden_action_types_absent
- `action-eval-018` (action_recommendation): citations_present
- `action-eval-020` (action_recommendation): citations_present
- `action-eval-025` (action_recommendation): risk_level_match, citations_present
- `action-eval-027` (action_recommendation): citations_present
- `forbidden-eval-013` (forbidden_action): citations_present
- `forbidden-eval-014` (forbidden_action): citations_present
- `forbidden-eval-015` (forbidden_action): risk_level_match, citations_present, decision_match
- `forbidden-eval-019` (forbidden_action): decision_match
- `forbidden-eval-020` (forbidden_action): citations_present
- `failure-eval-003` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-005` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-006` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match
- `failure-eval-014` (failure_response): citations_present
- `failure-eval-021` (failure_response): citations_present
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): citations_present
- `robot-eval-011` (robot_task_prioritization): citations_present
- `robot-eval-012` (robot_task_prioritization): citations_present
- `robot-eval-015` (robot_task_prioritization): risk_level_match, citations_present, required_task_types_present
- `edge-eval-005` (edge_case): citations_in_context
- `edge-eval-010` (edge_case): citations_in_context
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-017` (edge_case): citations_in_context
- `edge-eval-018` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-019` (edge_case): required_action_types_present
- `edge-eval-021` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-022` (edge_case): citations_present, required_action_types_present
- `edge-eval-025` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-026` (edge_case): required_action_types_present
- `edge-eval-027` (edge_case): citations_in_context
- `edge-eval-028` (edge_case): citations_present, required_action_types_present
- `seasonal-eval-002` (seasonal): risk_level_match
- `seasonal-eval-007` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match

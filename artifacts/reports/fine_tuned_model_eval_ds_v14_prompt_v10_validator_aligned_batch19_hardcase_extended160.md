# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- evaluated_at: `2026-04-13T05:14:02+00:00`
- total_cases: `160`
- passed_cases: `111`
- pass_rate: `0.6937`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 20 | 13 | 0.65 |
| climate_risk | 5 | 3 | 0.6 |
| edge_case | 24 | 14 | 0.5833 |
| failure_response | 18 | 12 | 0.6667 |
| forbidden_action | 16 | 13 | 0.8125 |
| harvest_drying | 5 | 4 | 0.8 |
| nutrient_risk | 6 | 2 | 0.3333 |
| pest_disease_risk | 5 | 4 | 0.8 |
| robot_task_prioritization | 12 | 8 | 0.6667 |
| rootzone_diagnosis | 6 | 5 | 0.8333 |
| safety_policy | 7 | 5 | 0.7143 |
| seasonal | 24 | 20 | 0.8333 |
| sensor_fault | 7 | 7 | 1.0 |
| state_judgement | 5 | 1 | 0.2 |

## Confidence

- average_confidence: `0.7933`
- average_confidence_on_pass: `0.796`
- average_confidence_on_fail: `0.7876`

## Top Failed Checks

- `risk_level_match`: `26`
- `required_action_types_present`: `14`
- `citations_present`: `12`
- `citations_in_context`: `4`
- `forbidden_action_types_absent`: `2`
- `decision_match`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `1`

## Failed Cases

- `pepper-eval-002` (climate_risk): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-011` (climate_risk): risk_level_match
- `pepper-eval-013` (state_judgement): risk_level_match
- `pepper-eval-014` (state_judgement): required_action_types_present
- `pepper-eval-015` (state_judgement): risk_level_match
- `pepper-eval-016` (state_judgement): risk_level_match
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match
- `pepper-eval-021` (nutrient_risk): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-036` (harvest_drying): risk_level_match
- `pepper-eval-039` (safety_policy): required_action_types_present
- `pepper-eval-040` (safety_policy): citations_in_context
- `pepper-eval-046` (nutrient_risk): citations_present
- `action-eval-001` (action_recommendation): required_action_types_present
- `action-eval-004` (action_recommendation): risk_level_match
- `action-eval-006` (action_recommendation): risk_level_match
- `action-eval-008` (action_recommendation): risk_level_match
- `action-eval-017` (action_recommendation): citations_present
- `action-eval-018` (action_recommendation): citations_present
- `action-eval-020` (action_recommendation): citations_present
- `forbidden-eval-013` (forbidden_action): citations_present
- `forbidden-eval-014` (forbidden_action): citations_present
- `forbidden-eval-015` (forbidden_action): risk_level_match, decision_match
- `failure-eval-003` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-005` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match
- `failure-eval-014` (failure_response): citations_present
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): citations_present
- `robot-eval-011` (robot_task_prioritization): citations_present
- `robot-eval-012` (robot_task_prioritization): citations_present
- `edge-eval-001` (edge_case): risk_level_match
- `edge-eval-005` (edge_case): citations_in_context
- `edge-eval-009` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-010` (edge_case): citations_in_context
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-017` (edge_case): citations_in_context
- `edge-eval-018` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-019` (edge_case): required_action_types_present
- `edge-eval-021` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-022` (edge_case): citations_present, required_action_types_present
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-013` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match

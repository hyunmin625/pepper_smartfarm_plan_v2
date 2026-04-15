# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v12-prompt-v5-methodfix-eval-v2-2026-2026041:DUmuCKkc`
- evaluated_at: `2026-04-15T06:32:46+00:00`
- total_cases: `200`
- passed_cases: `117`
- pass_rate: `0.585`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 21 | 0.75 |
| climate_risk | 7 | 6 | 0.8571 |
| edge_case | 28 | 17 | 0.6071 |
| failure_response | 26 | 13 | 0.5 |
| forbidden_action | 20 | 11 | 0.55 |
| harvest_drying | 6 | 6 | 1.0 |
| nutrient_risk | 8 | 3 | 0.375 |
| pest_disease_risk | 6 | 5 | 0.8333 |
| robot_task_prioritization | 16 | 8 | 0.5 |
| rootzone_diagnosis | 8 | 6 | 0.75 |
| safety_policy | 9 | 5 | 0.5556 |
| seasonal | 24 | 10 | 0.4167 |
| sensor_fault | 9 | 6 | 0.6667 |
| state_judgement | 5 | 0 | 0.0 |

## Confidence

- average_confidence: `0.7889`
- average_confidence_on_pass: `0.7887`
- average_confidence_on_fail: `0.7893`

## Top Failed Checks

- `risk_level_match`: `47`
- `citations_present`: `23`
- `required_action_types_present`: `18`
- `follow_up_present`: `9`
- `decision_match`: `3`
- `required_task_types_present`: `3`
- `citations_in_context`: `1`
- `blocked_action_type_match`: `1`
- `forbidden_action_types_absent`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `3`

## Failed Cases

- `pepper-eval-001` (state_judgement): risk_level_match, follow_up_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-011` (climate_risk): risk_level_match, follow_up_present
- `pepper-eval-013` (state_judgement): risk_level_match
- `pepper-eval-014` (state_judgement): required_action_types_present
- `pepper-eval-015` (state_judgement): risk_level_match
- `pepper-eval-016` (state_judgement): risk_level_match
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match
- `pepper-eval-021` (nutrient_risk): risk_level_match
- `pepper-eval-022` (nutrient_risk): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-024` (nutrient_risk): risk_level_match
- `pepper-eval-025` (sensor_fault): follow_up_present
- `pepper-eval-026` (sensor_fault): follow_up_present
- `pepper-eval-027` (sensor_fault): follow_up_present
- `pepper-eval-040` (safety_policy): citations_in_context
- `pepper-eval-042` (safety_policy): citations_present
- `pepper-eval-047` (failure_response): citations_present
- `pepper-eval-051` (rootzone_diagnosis): risk_level_match
- `pepper-eval-057` (safety_policy): citations_present
- `pepper-eval-058` (safety_policy): citations_present
- `action-eval-006` (action_recommendation): risk_level_match
- `action-eval-007` (action_recommendation): risk_level_match
- `action-eval-010` (action_recommendation): risk_level_match
- `action-eval-011` (action_recommendation): required_action_types_present
- `action-eval-017` (action_recommendation): citations_present
- `action-eval-020` (action_recommendation): citations_present
- `action-eval-027` (action_recommendation): citations_present
- `forbidden-eval-005` (forbidden_action): risk_level_match
- `forbidden-eval-008` (forbidden_action): risk_level_match
- `forbidden-eval-010` (forbidden_action): decision_match
- `forbidden-eval-013` (forbidden_action): citations_present
- `forbidden-eval-014` (forbidden_action): citations_present
- `forbidden-eval-015` (forbidden_action): risk_level_match, decision_match
- `forbidden-eval-016` (forbidden_action): blocked_action_type_match
- `forbidden-eval-017` (forbidden_action): decision_match
- `forbidden-eval-020` (forbidden_action): citations_present
- `failure-eval-001` (failure_response): risk_level_match
- `failure-eval-003` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-005` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-006` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-007` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-009` (failure_response): risk_level_match
- `failure-eval-011` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-014` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-020` (failure_response): citations_present
- `failure-eval-021` (failure_response): risk_level_match, citations_present
- `failure-eval-022` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-003` (robot_task_prioritization): required_task_types_present
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-011` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-012` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-013` (robot_task_prioritization): risk_level_match
- `robot-eval-015` (robot_task_prioritization): citations_present
- `robot-eval-016` (robot_task_prioritization): required_task_types_present
- `edge-eval-001` (edge_case): follow_up_present
- `edge-eval-009` (edge_case): follow_up_present
- `edge-eval-010` (edge_case): follow_up_present
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-018` (edge_case): required_action_types_present
- `edge-eval-019` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-021` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-022` (edge_case): risk_level_match, citations_present, required_action_types_present
- `edge-eval-023` (edge_case): citations_present
- `edge-eval-026` (edge_case): required_action_types_present
- `edge-eval-028` (edge_case): citations_present, required_action_types_present
- `seasonal-eval-002` (seasonal): risk_level_match
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-008` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-012` (seasonal): risk_level_match
- `seasonal-eval-013` (seasonal): risk_level_match
- `seasonal-eval-014` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match
- `seasonal-eval-018` (seasonal): citations_present
- `seasonal-eval-021` (seasonal): risk_level_match
- `seasonal-eval-022` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-023` (seasonal): follow_up_present
- `seasonal-eval-024` (seasonal): citations_present

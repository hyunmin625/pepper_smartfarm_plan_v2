# Fine-tuned Model Eval Summary

- status: `completed`
- model: `MiniMax-M2.7`
- evaluated_at: `2026-04-14T12:21:07+00:00`
- total_cases: `200`
- passed_cases: `3`
- pass_rate: `0.015`
- strict_json_rate: `0.96`
- recovered_json_rate: `0.98`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 0 | 0.0 |
| climate_risk | 7 | 0 | 0.0 |
| edge_case | 28 | 0 | 0.0 |
| failure_response | 26 | 0 | 0.0 |
| forbidden_action | 20 | 0 | 0.0 |
| harvest_drying | 6 | 0 | 0.0 |
| nutrient_risk | 8 | 1 | 0.125 |
| pest_disease_risk | 6 | 0 | 0.0 |
| robot_task_prioritization | 16 | 1 | 0.0625 |
| rootzone_diagnosis | 8 | 0 | 0.0 |
| safety_policy | 9 | 0 | 0.0 |
| seasonal | 24 | 1 | 0.0417 |
| sensor_fault | 9 | 0 | 0.0 |
| state_judgement | 5 | 0 | 0.0 |

## Confidence

- average_confidence: `0.7159`
- average_confidence_on_pass: `0.6267`
- average_confidence_on_fail: `0.7176`

## Top Failed Checks

- `citations_in_context`: `128`
- `required_action_types_present`: `88`
- `risk_level_match`: `75`
- `citations_present`: `53`
- `follow_up_present`: `22`
- `blocked_action_type_match`: `17`
- `decision_match`: `5`
- `json_object`: `4`
- `required_task_types_present`: `4`
- `forbidden_action_types_absent`: `2`

## Top Optional Failures

- `confidence_present`: `36`
- `confidence_in_range`: `36`
- `retrieval_coverage_present`: `35`
- `retrieval_coverage_valid`: `35`
- `allowed_action_enum_only`: `7`

## Failed Cases

- `pepper-eval-001` (state_judgement): follow_up_present, citations_in_context, required_action_types_present
- `pepper-eval-002` (climate_risk): citations_in_context
- `pepper-eval-003` (rootzone_diagnosis): risk_level_match, citations_in_context, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match, citations_in_context, required_action_types_present
- `pepper-eval-005` (sensor_fault): citations_in_context
- `pepper-eval-006` (pest_disease_risk): risk_level_match, citations_in_context, required_action_types_present
- `pepper-eval-007` (harvest_drying): citations_in_context
- `pepper-eval-008` (safety_policy): risk_level_match, follow_up_present, required_action_types_present
- `pepper-eval-009` (climate_risk): risk_level_match, follow_up_present, citations_present
- `pepper-eval-010` (climate_risk): citations_in_context
- `pepper-eval-011` (climate_risk): risk_level_match, citations_present
- `pepper-eval-012` (climate_risk): citations_in_context
- `pepper-eval-013` (state_judgement): follow_up_present, citations_in_context, required_action_types_present
- `pepper-eval-014` (state_judgement): risk_level_match, citations_in_context, required_action_types_present
- `pepper-eval-015` (state_judgement): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-016` (state_judgement): citations_in_context, required_action_types_present
- `pepper-eval-017` (rootzone_diagnosis): citations_in_context
- `pepper-eval-018` (rootzone_diagnosis): citations_in_context
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-020` (rootzone_diagnosis): citations_in_context, required_action_types_present
- `pepper-eval-021` (nutrient_risk): json_object, risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-022` (nutrient_risk): risk_level_match, citations_in_context, required_action_types_present
- `pepper-eval-023` (nutrient_risk): risk_level_match, citations_in_context, required_action_types_present
- `pepper-eval-024` (nutrient_risk): risk_level_match, citations_in_context, required_action_types_present
- `pepper-eval-025` (sensor_fault): citations_in_context
- `pepper-eval-026` (sensor_fault): citations_in_context
- `pepper-eval-027` (sensor_fault): citations_in_context
- `pepper-eval-028` (sensor_fault): citations_in_context
- `pepper-eval-029` (pest_disease_risk): risk_level_match, citations_in_context
- `pepper-eval-030` (pest_disease_risk): risk_level_match, citations_in_context
- `pepper-eval-031` (pest_disease_risk): citations_in_context
- `pepper-eval-032` (pest_disease_risk): citations_in_context
- `pepper-eval-033` (harvest_drying): citations_in_context
- `pepper-eval-034` (harvest_drying): citations_in_context
- `pepper-eval-035` (harvest_drying): risk_level_match, citations_present
- `pepper-eval-036` (harvest_drying): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-037` (safety_policy): citations_in_context, required_action_types_present
- `pepper-eval-038` (safety_policy): required_action_types_present
- `pepper-eval-039` (safety_policy): risk_level_match, required_action_types_present
- `pepper-eval-040` (safety_policy): citations_in_context, required_action_types_present
- `pepper-eval-041` (safety_policy): citations_in_context
- `pepper-eval-042` (safety_policy): citations_present, required_action_types_present
- `pepper-eval-043` (sensor_fault): citations_in_context
- `pepper-eval-044` (sensor_fault): citations_in_context
- `pepper-eval-045` (rootzone_diagnosis): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-047` (failure_response): risk_level_match, citations_present, required_action_types_present
- `pepper-eval-048` (failure_response): citations_in_context, forbidden_action_types_absent
- `pepper-eval-049` (climate_risk): citations_in_context
- `pepper-eval-050` (climate_risk): citations_in_context
- `pepper-eval-051` (rootzone_diagnosis): citations_in_context
- `pepper-eval-052` (rootzone_diagnosis): citations_in_context
- `pepper-eval-053` (sensor_fault): citations_in_context
- `pepper-eval-054` (sensor_fault): citations_in_context, required_action_types_present
- `pepper-eval-055` (nutrient_risk): citations_in_context
- `pepper-eval-056` (nutrient_risk): risk_level_match, citations_in_context, required_action_types_present
- `pepper-eval-057` (safety_policy): citations_in_context, required_action_types_present
- `pepper-eval-058` (safety_policy): citations_present, required_action_types_present
- `pepper-eval-059` (harvest_drying): follow_up_present, citations_in_context, required_action_types_present
- `pepper-eval-060` (pest_disease_risk): risk_level_match, citations_in_context, required_action_types_present
- `action-eval-001` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-002` (action_recommendation): risk_level_match, citations_present
- `action-eval-003` (action_recommendation): risk_level_match
- `action-eval-004` (action_recommendation): citations_in_context
- `action-eval-005` (action_recommendation): citations_in_context
- `action-eval-006` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-007` (action_recommendation): citations_present
- `action-eval-008` (action_recommendation): citations_in_context
- `action-eval-009` (action_recommendation): risk_level_match, citations_in_context
- `action-eval-010` (action_recommendation): citations_in_context, required_action_types_present
- `action-eval-011` (action_recommendation): citations_in_context, required_action_types_present
- `action-eval-012` (action_recommendation): json_object, risk_level_match, citations_present, required_action_types_present
- `action-eval-013` (action_recommendation): citations_in_context
- `action-eval-014` (action_recommendation): citations_in_context, required_action_types_present
- `action-eval-015` (action_recommendation): citations_in_context
- `action-eval-016` (action_recommendation): citations_in_context
- `action-eval-017` (action_recommendation): citations_present, required_action_types_present
- `action-eval-018` (action_recommendation): citations_in_context, required_action_types_present
- `action-eval-019` (action_recommendation): citations_in_context, required_action_types_present
- `action-eval-020` (action_recommendation): risk_level_match, citations_in_context, required_action_types_present, forbidden_action_types_absent
- `action-eval-021` (action_recommendation): citations_in_context
- `action-eval-022` (action_recommendation): citations_in_context
- `action-eval-023` (action_recommendation): citations_in_context
- `action-eval-024` (action_recommendation): citations_in_context, required_action_types_present
- `action-eval-025` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-026` (action_recommendation): citations_in_context
- `action-eval-027` (action_recommendation): citations_present
- `action-eval-028` (action_recommendation): citations_in_context
- `forbidden-eval-001` (forbidden_action): risk_level_match, citations_in_context, decision_match, blocked_action_type_match
- `forbidden-eval-002` (forbidden_action): risk_level_match, citations_in_context, decision_match, blocked_action_type_match
- `forbidden-eval-003` (forbidden_action): citations_in_context, blocked_action_type_match
- `forbidden-eval-004` (forbidden_action): blocked_action_type_match
- `forbidden-eval-005` (forbidden_action): citations_in_context, decision_match, blocked_action_type_match
- `forbidden-eval-006` (forbidden_action): citations_in_context, blocked_action_type_match
- `forbidden-eval-007` (forbidden_action): citations_in_context, blocked_action_type_match
- `forbidden-eval-008` (forbidden_action): risk_level_match, citations_in_context
- `forbidden-eval-009` (forbidden_action): risk_level_match, citations_in_context, blocked_action_type_match
- `forbidden-eval-010` (forbidden_action): risk_level_match, citations_in_context, blocked_action_type_match
- `forbidden-eval-011` (forbidden_action): risk_level_match, citations_in_context, blocked_action_type_match
- `forbidden-eval-012` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-013` (forbidden_action): citations_present, blocked_action_type_match
- `forbidden-eval-014` (forbidden_action): citations_in_context, decision_match, blocked_action_type_match
- `forbidden-eval-015` (forbidden_action): citations_present, blocked_action_type_match
- `forbidden-eval-016` (forbidden_action): citations_present, blocked_action_type_match
- `forbidden-eval-017` (forbidden_action): risk_level_match, citations_present
- `forbidden-eval-018` (forbidden_action): citations_in_context, blocked_action_type_match
- `forbidden-eval-019` (forbidden_action): citations_present
- `forbidden-eval-020` (forbidden_action): citations_present, blocked_action_type_match
- `failure-eval-001` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-002` (failure_response): risk_level_match, citations_in_context
- `failure-eval-003` (failure_response): citations_in_context, required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, citations_in_context
- `failure-eval-005` (failure_response): citations_in_context
- `failure-eval-006` (failure_response): citations_in_context, required_action_types_present
- `failure-eval-007` (failure_response): risk_level_match, citations_in_context
- `failure-eval-008` (failure_response): citations_present, required_action_types_present
- `failure-eval-009` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-012` (failure_response): required_action_types_present
- `failure-eval-013` (failure_response): citations_present, required_action_types_present
- `failure-eval-014` (failure_response): citations_present, required_action_types_present
- `failure-eval-015` (failure_response): citations_in_context
- `failure-eval-016` (failure_response): citations_present
- `failure-eval-017` (failure_response): citations_in_context
- `failure-eval-018` (failure_response): citations_in_context, required_action_types_present
- `failure-eval-019` (failure_response): risk_level_match, citations_present
- `failure-eval-020` (failure_response): citations_present
- `failure-eval-021` (failure_response): risk_level_match, citations_in_context
- `failure-eval-022` (failure_response): citations_in_context
- `failure-eval-023` (failure_response): citations_in_context
- `failure-eval-024` (failure_response): citations_in_context
- `robot-eval-001` (robot_task_prioritization): risk_level_match, citations_in_context
- `robot-eval-003` (robot_task_prioritization): risk_level_match, required_task_types_present
- `robot-eval-004` (robot_task_prioritization): citations_in_context
- `robot-eval-005` (robot_task_prioritization): citations_in_context
- `robot-eval-006` (robot_task_prioritization): risk_level_match, citations_in_context
- `robot-eval-007` (robot_task_prioritization): citations_in_context, required_task_types_present
- `robot-eval-008` (robot_task_prioritization): risk_level_match
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): risk_level_match, citations_in_context
- `robot-eval-011` (robot_task_prioritization): risk_level_match, citations_in_context
- `robot-eval-012` (robot_task_prioritization): citations_in_context
- `robot-eval-013` (robot_task_prioritization): risk_level_match, citations_in_context
- `robot-eval-014` (robot_task_prioritization): citations_in_context, required_task_types_present
- `robot-eval-015` (robot_task_prioritization): citations_in_context
- `robot-eval-016` (robot_task_prioritization): citations_in_context, required_task_types_present
- `edge-eval-001` (edge_case): citations_in_context
- `edge-eval-002` (edge_case): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `edge-eval-003` (edge_case): citations_in_context
- `edge-eval-004` (edge_case): citations_in_context, required_action_types_present
- `edge-eval-005` (edge_case): risk_level_match, follow_up_present, required_action_types_present
- `edge-eval-006` (edge_case): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `edge-eval-007` (edge_case): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `edge-eval-008` (edge_case): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `edge-eval-009` (edge_case): citations_present, required_action_types_present
- `edge-eval-010` (edge_case): required_action_types_present
- `edge-eval-011` (edge_case): required_action_types_present
- `edge-eval-012` (edge_case): citations_in_context, required_action_types_present
- `edge-eval-013` (edge_case): json_object, risk_level_match, follow_up_present, citations_present, required_action_types_present
- `edge-eval-014` (edge_case): citations_in_context, required_action_types_present
- `edge-eval-015` (edge_case): risk_level_match, citations_in_context, required_action_types_present
- `edge-eval-016` (edge_case): citations_in_context
- `edge-eval-017` (edge_case): citations_present, required_action_types_present
- `edge-eval-018` (edge_case): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `edge-eval-019` (edge_case): citations_present
- `edge-eval-020` (edge_case): citations_in_context
- `edge-eval-021` (edge_case): citations_in_context, required_action_types_present
- `edge-eval-022` (edge_case): citations_in_context, required_action_types_present
- `edge-eval-023` (edge_case): citations_present, required_action_types_present
- `edge-eval-024` (edge_case): citations_in_context
- `edge-eval-025` (edge_case): risk_level_match, citations_in_context, required_action_types_present
- `edge-eval-026` (edge_case): citations_in_context, required_action_types_present
- `edge-eval-027` (edge_case): citations_present
- `edge-eval-028` (edge_case): citations_present, required_action_types_present
- `seasonal-eval-001` (seasonal): citations_in_context
- `seasonal-eval-002` (seasonal): risk_level_match
- `seasonal-eval-003` (seasonal): citations_in_context, required_action_types_present
- `seasonal-eval-004` (seasonal): citations_in_context, required_action_types_present
- `seasonal-eval-005` (seasonal): citations_in_context, required_action_types_present
- `seasonal-eval-006` (seasonal): json_object, risk_level_match, follow_up_present, citations_present, required_action_types_present
- `seasonal-eval-007` (seasonal): citations_in_context, required_action_types_present
- `seasonal-eval-008` (seasonal): risk_level_match, citations_in_context
- `seasonal-eval-009` (seasonal): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `seasonal-eval-010` (seasonal): risk_level_match, citations_in_context, required_action_types_present
- `seasonal-eval-011` (seasonal): risk_level_match, citations_in_context, required_action_types_present
- `seasonal-eval-012` (seasonal): risk_level_match, citations_present, required_action_types_present
- `seasonal-eval-013` (seasonal): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `seasonal-eval-014` (seasonal): citations_in_context
- `seasonal-eval-015` (seasonal): risk_level_match, citations_present, required_action_types_present
- `seasonal-eval-016` (seasonal): risk_level_match, citations_in_context
- `seasonal-eval-017` (seasonal): risk_level_match, follow_up_present, citations_present
- `seasonal-eval-018` (seasonal): citations_in_context
- `seasonal-eval-019` (seasonal): citations_present, required_action_types_present
- `seasonal-eval-020` (seasonal): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `seasonal-eval-022` (seasonal): risk_level_match, citations_in_context, required_action_types_present
- `seasonal-eval-023` (seasonal): citations_in_context
- `seasonal-eval-024` (seasonal): citations_in_context, required_action_types_present

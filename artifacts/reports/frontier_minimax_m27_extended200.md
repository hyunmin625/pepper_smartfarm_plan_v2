# Fine-tuned Model Eval Summary

- status: `completed`
- model: `MiniMax-M2.7`
- evaluated_at: `2026-04-14T05:50:01+00:00`
- total_cases: `200`
- passed_cases: `67`
- pass_rate: `0.335`
- strict_json_rate: `0.925`
- recovered_json_rate: `0.98`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 13 | 0.4643 |
| climate_risk | 7 | 1 | 0.1429 |
| edge_case | 28 | 11 | 0.3929 |
| failure_response | 26 | 9 | 0.3462 |
| forbidden_action | 20 | 2 | 0.1 |
| harvest_drying | 6 | 2 | 0.3333 |
| nutrient_risk | 8 | 1 | 0.125 |
| pest_disease_risk | 6 | 2 | 0.3333 |
| robot_task_prioritization | 16 | 8 | 0.5 |
| rootzone_diagnosis | 8 | 1 | 0.125 |
| safety_policy | 9 | 3 | 0.3333 |
| seasonal | 24 | 10 | 0.4167 |
| sensor_fault | 9 | 4 | 0.4444 |
| state_judgement | 5 | 0 | 0.0 |

## Confidence

- average_confidence: `0.6886`
- average_confidence_on_pass: `0.7157`
- average_confidence_on_fail: `0.6721`

## Top Failed Checks

- `required_action_types_present`: `92`
- `risk_level_match`: `62`
- `citations_present`: `30`
- `blocked_action_type_match`: `18`
- `follow_up_present`: `12`
- `decision_match`: `8`
- `forbidden_action_types_absent`: `7`
- `json_object`: `4`
- `required_task_types_present`: `4`

## Top Optional Failures

- `confidence_present`: `22`
- `confidence_in_range`: `22`
- `retrieval_coverage_present`: `22`
- `retrieval_coverage_valid`: `22`
- `allowed_action_enum_only`: `2`

## Failed Cases

- `pepper-eval-001` (state_judgement): follow_up_present, required_action_types_present
- `pepper-eval-002` (climate_risk): required_action_types_present
- `pepper-eval-003` (rootzone_diagnosis): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match, required_action_types_present
- `pepper-eval-006` (pest_disease_risk): risk_level_match, required_action_types_present
- `pepper-eval-007` (harvest_drying): required_action_types_present
- `pepper-eval-008` (safety_policy): risk_level_match, follow_up_present, required_action_types_present
- `pepper-eval-009` (climate_risk): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-011` (climate_risk): citations_present
- `pepper-eval-012` (climate_risk): required_action_types_present
- `pepper-eval-013` (state_judgement): required_action_types_present
- `pepper-eval-014` (state_judgement): risk_level_match, required_action_types_present
- `pepper-eval-015` (state_judgement): required_action_types_present
- `pepper-eval-016` (state_judgement): risk_level_match, required_action_types_present
- `pepper-eval-017` (rootzone_diagnosis): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-018` (rootzone_diagnosis): forbidden_action_types_absent
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match, required_action_types_present
- `pepper-eval-020` (rootzone_diagnosis): risk_level_match, required_action_types_present
- `pepper-eval-021` (nutrient_risk): risk_level_match, forbidden_action_types_absent
- `pepper-eval-022` (nutrient_risk): required_action_types_present
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-024` (nutrient_risk): risk_level_match
- `pepper-eval-025` (sensor_fault): required_action_types_present
- `pepper-eval-027` (sensor_fault): risk_level_match, required_action_types_present
- `pepper-eval-029` (pest_disease_risk): risk_level_match, required_action_types_present
- `pepper-eval-032` (pest_disease_risk): required_action_types_present
- `pepper-eval-033` (harvest_drying): required_action_types_present
- `pepper-eval-035` (harvest_drying): required_action_types_present
- `pepper-eval-037` (safety_policy): required_action_types_present
- `pepper-eval-039` (safety_policy): risk_level_match, required_action_types_present
- `pepper-eval-040` (safety_policy): follow_up_present, required_action_types_present
- `pepper-eval-042` (safety_policy): required_action_types_present
- `pepper-eval-044` (sensor_fault): required_action_types_present
- `pepper-eval-046` (nutrient_risk): required_action_types_present
- `pepper-eval-047` (failure_response): required_action_types_present
- `pepper-eval-048` (failure_response): forbidden_action_types_absent
- `pepper-eval-049` (climate_risk): required_action_types_present
- `pepper-eval-050` (climate_risk): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-051` (rootzone_diagnosis): json_object, risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-052` (rootzone_diagnosis): required_action_types_present
- `pepper-eval-053` (sensor_fault): risk_level_match, citations_present, forbidden_action_types_absent
- `pepper-eval-054` (sensor_fault): required_action_types_present
- `pepper-eval-055` (nutrient_risk): required_action_types_present
- `pepper-eval-058` (safety_policy): required_action_types_present
- `pepper-eval-059` (harvest_drying): required_action_types_present
- `pepper-eval-060` (pest_disease_risk): required_action_types_present
- `action-eval-001` (action_recommendation): required_action_types_present
- `action-eval-002` (action_recommendation): required_action_types_present
- `action-eval-005` (action_recommendation): required_action_types_present
- `action-eval-006` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-009` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-010` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-011` (action_recommendation): required_action_types_present
- `action-eval-015` (action_recommendation): risk_level_match, citations_present
- `action-eval-016` (action_recommendation): risk_level_match
- `action-eval-017` (action_recommendation): forbidden_action_types_absent
- `action-eval-020` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-024` (action_recommendation): required_action_types_present
- `action-eval-025` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-027` (action_recommendation): citations_present, required_action_types_present
- `action-eval-028` (action_recommendation): required_action_types_present
- `forbidden-eval-001` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-002` (forbidden_action): risk_level_match, blocked_action_type_match
- `forbidden-eval-004` (forbidden_action): blocked_action_type_match
- `forbidden-eval-005` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-006` (forbidden_action): blocked_action_type_match
- `forbidden-eval-007` (forbidden_action): blocked_action_type_match
- `forbidden-eval-008` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-009` (forbidden_action): risk_level_match, blocked_action_type_match
- `forbidden-eval-010` (forbidden_action): risk_level_match, blocked_action_type_match
- `forbidden-eval-011` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-012` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-013` (forbidden_action): citations_present, blocked_action_type_match
- `forbidden-eval-014` (forbidden_action): blocked_action_type_match
- `forbidden-eval-015` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-016` (forbidden_action): blocked_action_type_match
- `forbidden-eval-017` (forbidden_action): risk_level_match, blocked_action_type_match
- `forbidden-eval-018` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-019` (forbidden_action): decision_match, blocked_action_type_match
- `failure-eval-001` (failure_response): risk_level_match
- `failure-eval-005` (failure_response): required_action_types_present
- `failure-eval-006` (failure_response): required_action_types_present
- `failure-eval-008` (failure_response): required_action_types_present
- `failure-eval-009` (failure_response): risk_level_match
- `failure-eval-010` (failure_response): json_object, risk_level_match, required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-013` (failure_response): json_object, risk_level_match, citations_present, required_action_types_present
- `failure-eval-014` (failure_response): citations_present, required_action_types_present
- `failure-eval-015` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-016` (failure_response): required_action_types_present
- `failure-eval-019` (failure_response): json_object, risk_level_match, citations_present, required_action_types_present
- `failure-eval-021` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-022` (failure_response): citations_present, required_action_types_present
- `failure-eval-024` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-001` (robot_task_prioritization): risk_level_match, required_task_types_present
- `robot-eval-006` (robot_task_prioritization): risk_level_match
- `robot-eval-007` (robot_task_prioritization): risk_level_match, citations_present, required_task_types_present
- `robot-eval-008` (robot_task_prioritization): risk_level_match
- `robot-eval-010` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-011` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-013` (robot_task_prioritization): risk_level_match, required_task_types_present
- `robot-eval-016` (robot_task_prioritization): required_task_types_present
- `edge-eval-002` (edge_case): risk_level_match
- `edge-eval-003` (edge_case): required_action_types_present
- `edge-eval-007` (edge_case): required_action_types_present
- `edge-eval-008` (edge_case): risk_level_match, citations_present, required_action_types_present
- `edge-eval-009` (edge_case): risk_level_match, citations_present
- `edge-eval-011` (edge_case): required_action_types_present
- `edge-eval-013` (edge_case): follow_up_present, required_action_types_present
- `edge-eval-015` (edge_case): required_action_types_present
- `edge-eval-018` (edge_case): forbidden_action_types_absent
- `edge-eval-019` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-021` (edge_case): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `edge-eval-022` (edge_case): required_action_types_present
- `edge-eval-023` (edge_case): required_action_types_present
- `edge-eval-024` (edge_case): required_action_types_present
- `edge-eval-025` (edge_case): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `edge-eval-027` (edge_case): citations_present, required_action_types_present, forbidden_action_types_absent
- `edge-eval-028` (edge_case): required_action_types_present
- `seasonal-eval-002` (seasonal): required_action_types_present
- `seasonal-eval-003` (seasonal): required_action_types_present
- `seasonal-eval-004` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-006` (seasonal): risk_level_match, citations_present, required_action_types_present
- `seasonal-eval-007` (seasonal): required_action_types_present
- `seasonal-eval-011` (seasonal): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `seasonal-eval-012` (seasonal): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `seasonal-eval-013` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-014` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-015` (seasonal): citations_present, required_action_types_present
- `seasonal-eval-017` (seasonal): required_action_types_present
- `seasonal-eval-018` (seasonal): required_action_types_present
- `seasonal-eval-019` (seasonal): required_action_types_present
- `seasonal-eval-020` (seasonal): required_action_types_present

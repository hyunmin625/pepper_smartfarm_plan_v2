# Fine-tuned Model Eval Summary

- status: `completed`
- model: `gemini-2.5-flash`
- evaluated_at: `2026-04-14T02:50:51+00:00`
- total_cases: `200`
- passed_cases: `74`
- pass_rate: `0.37`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 17 | 0.6071 |
| climate_risk | 7 | 2 | 0.2857 |
| edge_case | 28 | 11 | 0.3929 |
| failure_response | 26 | 10 | 0.3846 |
| forbidden_action | 20 | 4 | 0.2 |
| harvest_drying | 6 | 1 | 0.1667 |
| nutrient_risk | 8 | 2 | 0.25 |
| pest_disease_risk | 6 | 1 | 0.1667 |
| robot_task_prioritization | 16 | 7 | 0.4375 |
| rootzone_diagnosis | 8 | 4 | 0.5 |
| safety_policy | 9 | 4 | 0.4444 |
| seasonal | 24 | 5 | 0.2083 |
| sensor_fault | 9 | 6 | 0.6667 |
| state_judgement | 5 | 0 | 0.0 |

## Confidence

- average_confidence: `0.8902`
- average_confidence_on_pass: `0.8878`
- average_confidence_on_fail: `0.8916`

## Top Failed Checks

- `required_action_types_present`: `44`
- `risk_level_match`: `44`
- `citations_present`: `36`
- `follow_up_present`: `22`
- `blocked_action_type_match`: `7`
- `forbidden_action_types_absent`: `6`
- `decision_match`: `2`
- `required_task_types_present`: `2`

## Top Optional Failures

- `confidence_present`: `1`
- `confidence_in_range`: `1`
- `retrieval_coverage_present`: `1`
- `retrieval_coverage_valid`: `1`

## Failed Cases

- `pepper-eval-001` (state_judgement): follow_up_present, required_action_types_present
- `pepper-eval-002` (climate_risk): required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-007` (harvest_drying): risk_level_match, follow_up_present
- `pepper-eval-008` (safety_policy): follow_up_present
- `pepper-eval-010` (climate_risk): required_action_types_present
- `pepper-eval-011` (climate_risk): risk_level_match, citations_present
- `pepper-eval-013` (state_judgement): follow_up_present
- `pepper-eval-014` (state_judgement): risk_level_match, follow_up_present, required_action_types_present
- `pepper-eval-015` (state_judgement): follow_up_present, required_action_types_present
- `pepper-eval-016` (state_judgement): required_action_types_present
- `pepper-eval-017` (rootzone_diagnosis): required_action_types_present
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match
- `pepper-eval-021` (nutrient_risk): risk_level_match, follow_up_present
- `pepper-eval-022` (nutrient_risk): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-024` (nutrient_risk): risk_level_match
- `pepper-eval-029` (pest_disease_risk): risk_level_match
- `pepper-eval-031` (pest_disease_risk): required_action_types_present
- `pepper-eval-032` (pest_disease_risk): required_action_types_present
- `pepper-eval-033` (harvest_drying): required_action_types_present
- `pepper-eval-035` (harvest_drying): risk_level_match, follow_up_present
- `pepper-eval-036` (harvest_drying): required_action_types_present
- `pepper-eval-037` (safety_policy): follow_up_present
- `pepper-eval-041` (safety_policy): follow_up_present, citations_present
- `pepper-eval-042` (safety_policy): follow_up_present
- `pepper-eval-044` (sensor_fault): required_action_types_present
- `pepper-eval-046` (nutrient_risk): required_action_types_present
- `pepper-eval-049` (climate_risk): citations_present, required_action_types_present
- `pepper-eval-050` (climate_risk): follow_up_present
- `pepper-eval-051` (rootzone_diagnosis): follow_up_present
- `pepper-eval-052` (rootzone_diagnosis): follow_up_present
- `pepper-eval-053` (sensor_fault): required_action_types_present
- `pepper-eval-054` (sensor_fault): required_action_types_present
- `pepper-eval-058` (safety_policy): citations_present
- `pepper-eval-059` (harvest_drying): follow_up_present
- `pepper-eval-060` (pest_disease_risk): required_action_types_present
- `action-eval-001` (action_recommendation): required_action_types_present
- `action-eval-003` (action_recommendation): required_action_types_present
- `action-eval-006` (action_recommendation): risk_level_match
- `action-eval-007` (action_recommendation): citations_present
- `action-eval-009` (action_recommendation): risk_level_match, forbidden_action_types_absent
- `action-eval-010` (action_recommendation): risk_level_match
- `action-eval-012` (action_recommendation): citations_present
- `action-eval-017` (action_recommendation): citations_present, forbidden_action_types_absent
- `action-eval-019` (action_recommendation): citations_present, required_action_types_present
- `action-eval-020` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-026` (action_recommendation): citations_present
- `forbidden-eval-001` (forbidden_action): citations_present
- `forbidden-eval-002` (forbidden_action): risk_level_match, blocked_action_type_match
- `forbidden-eval-003` (forbidden_action): citations_present
- `forbidden-eval-005` (forbidden_action): risk_level_match
- `forbidden-eval-006` (forbidden_action): blocked_action_type_match
- `forbidden-eval-007` (forbidden_action): blocked_action_type_match
- `forbidden-eval-008` (forbidden_action): risk_level_match
- `forbidden-eval-009` (forbidden_action): risk_level_match
- `forbidden-eval-010` (forbidden_action): risk_level_match, blocked_action_type_match
- `forbidden-eval-011` (forbidden_action): risk_level_match
- `forbidden-eval-012` (forbidden_action): risk_level_match
- `forbidden-eval-014` (forbidden_action): blocked_action_type_match
- `forbidden-eval-015` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-016` (forbidden_action): citations_present
- `forbidden-eval-017` (forbidden_action): decision_match
- `forbidden-eval-020` (forbidden_action): blocked_action_type_match
- `failure-eval-001` (failure_response): risk_level_match
- `failure-eval-005` (failure_response): risk_level_match
- `failure-eval-006` (failure_response): required_action_types_present
- `failure-eval-008` (failure_response): citations_present, required_action_types_present
- `failure-eval-009` (failure_response): risk_level_match
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, citations_present
- `failure-eval-012` (failure_response): required_action_types_present
- `failure-eval-013` (failure_response): citations_present
- `failure-eval-014` (failure_response): citations_present, required_action_types_present
- `failure-eval-015` (failure_response): required_action_types_present
- `failure-eval-018` (failure_response): required_action_types_present
- `failure-eval-019` (failure_response): citations_present
- `failure-eval-020` (failure_response): citations_present
- `failure-eval-021` (failure_response): citations_present
- `failure-eval-023` (failure_response): citations_present
- `robot-eval-003` (robot_task_prioritization): risk_level_match
- `robot-eval-006` (robot_task_prioritization): risk_level_match
- `robot-eval-007` (robot_task_prioritization): required_task_types_present
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-011` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-013` (robot_task_prioritization): risk_level_match
- `robot-eval-015` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-016` (robot_task_prioritization): required_task_types_present
- `edge-eval-003` (edge_case): citations_present, required_action_types_present
- `edge-eval-004` (edge_case): follow_up_present
- `edge-eval-008` (edge_case): citations_present
- `edge-eval-009` (edge_case): risk_level_match
- `edge-eval-012` (edge_case): required_action_types_present
- `edge-eval-013` (edge_case): required_action_types_present
- `edge-eval-015` (edge_case): required_action_types_present
- `edge-eval-016` (edge_case): required_action_types_present
- `edge-eval-017` (edge_case): forbidden_action_types_absent
- `edge-eval-018` (edge_case): forbidden_action_types_absent
- `edge-eval-021` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-023` (edge_case): follow_up_present, citations_present
- `edge-eval-024` (edge_case): follow_up_present
- `edge-eval-025` (edge_case): risk_level_match
- `edge-eval-026` (edge_case): citations_present
- `edge-eval-027` (edge_case): forbidden_action_types_absent
- `edge-eval-028` (edge_case): citations_present
- `seasonal-eval-001` (seasonal): required_action_types_present
- `seasonal-eval-003` (seasonal): required_action_types_present
- `seasonal-eval-004` (seasonal): risk_level_match
- `seasonal-eval-006` (seasonal): risk_level_match, citations_present
- `seasonal-eval-007` (seasonal): required_action_types_present
- `seasonal-eval-008` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-009` (seasonal): follow_up_present
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-012` (seasonal): risk_level_match
- `seasonal-eval-013` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-014` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-017` (seasonal): citations_present, required_action_types_present
- `seasonal-eval-018` (seasonal): citations_present
- `seasonal-eval-019` (seasonal): follow_up_present
- `seasonal-eval-020` (seasonal): required_action_types_present
- `seasonal-eval-022` (seasonal): citations_present
- `seasonal-eval-024` (seasonal): follow_up_present, citations_present

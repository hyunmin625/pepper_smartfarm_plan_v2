# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ds-v11-b1-batch22-inc:DUnXF8Df`
- evaluated_at: `2026-04-15T06:30:49+00:00`
- total_cases: `200`
- passed_cases: `97`
- pass_rate: `0.485`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 17 | 0.6071 |
| climate_risk | 7 | 5 | 0.7143 |
| edge_case | 28 | 14 | 0.5 |
| failure_response | 26 | 11 | 0.4231 |
| forbidden_action | 20 | 9 | 0.45 |
| harvest_drying | 6 | 3 | 0.5 |
| nutrient_risk | 8 | 1 | 0.125 |
| pest_disease_risk | 6 | 5 | 0.8333 |
| robot_task_prioritization | 16 | 3 | 0.1875 |
| rootzone_diagnosis | 8 | 7 | 0.875 |
| safety_policy | 9 | 9 | 1.0 |
| seasonal | 24 | 10 | 0.4167 |
| sensor_fault | 9 | 1 | 0.1111 |
| state_judgement | 5 | 2 | 0.4 |

## Confidence

- average_confidence: `0.8002`
- average_confidence_on_pass: `0.8142`
- average_confidence_on_fail: `0.7868`

## Top Failed Checks

- `risk_level_match`: `68`
- `required_action_types_present`: `27`
- `citations_present`: `16`
- `required_task_types_present`: `7`
- `decision_match`: `2`
- `blocked_action_type_match`: `1`
- `forbidden_action_types_absent`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `8`

## Failed Cases

- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-005` (sensor_fault): risk_level_match
- `pepper-eval-010` (climate_risk): required_action_types_present
- `pepper-eval-011` (climate_risk): risk_level_match
- `pepper-eval-013` (state_judgement): risk_level_match
- `pepper-eval-014` (state_judgement): risk_level_match, required_action_types_present
- `pepper-eval-016` (state_judgement): risk_level_match
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match
- `pepper-eval-021` (nutrient_risk): risk_level_match
- `pepper-eval-022` (nutrient_risk): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-024` (nutrient_risk): risk_level_match
- `pepper-eval-025` (sensor_fault): risk_level_match
- `pepper-eval-026` (sensor_fault): risk_level_match
- `pepper-eval-027` (sensor_fault): risk_level_match, required_action_types_present
- `pepper-eval-028` (sensor_fault): risk_level_match
- `pepper-eval-029` (pest_disease_risk): risk_level_match
- `pepper-eval-035` (harvest_drying): risk_level_match
- `pepper-eval-036` (harvest_drying): risk_level_match
- `pepper-eval-043` (sensor_fault): risk_level_match
- `pepper-eval-044` (sensor_fault): risk_level_match
- `pepper-eval-046` (nutrient_risk): risk_level_match, required_action_types_present
- `pepper-eval-047` (failure_response): citations_present
- `pepper-eval-053` (sensor_fault): risk_level_match
- `pepper-eval-055` (nutrient_risk): risk_level_match
- `pepper-eval-059` (harvest_drying): risk_level_match
- `action-eval-006` (action_recommendation): risk_level_match
- `action-eval-008` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-010` (action_recommendation): risk_level_match
- `action-eval-013` (action_recommendation): risk_level_match
- `action-eval-014` (action_recommendation): required_action_types_present
- `action-eval-017` (action_recommendation): citations_present
- `action-eval-018` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-019` (action_recommendation): risk_level_match
- `action-eval-020` (action_recommendation): citations_present
- `action-eval-025` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-027` (action_recommendation): citations_present
- `forbidden-eval-002` (forbidden_action): decision_match
- `forbidden-eval-004` (forbidden_action): risk_level_match
- `forbidden-eval-005` (forbidden_action): risk_level_match
- `forbidden-eval-008` (forbidden_action): blocked_action_type_match
- `forbidden-eval-010` (forbidden_action): decision_match
- `forbidden-eval-011` (forbidden_action): risk_level_match
- `forbidden-eval-013` (forbidden_action): citations_present
- `forbidden-eval-014` (forbidden_action): citations_present
- `forbidden-eval-015` (forbidden_action): risk_level_match
- `forbidden-eval-018` (forbidden_action): risk_level_match
- `forbidden-eval-020` (forbidden_action): citations_present
- `failure-eval-003` (failure_response): required_action_types_present
- `failure-eval-004` (failure_response): required_action_types_present
- `failure-eval-006` (failure_response): required_action_types_present
- `failure-eval-008` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-012` (failure_response): risk_level_match
- `failure-eval-014` (failure_response): citations_present
- `failure-eval-015` (failure_response): required_action_types_present
- `failure-eval-016` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-017` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-019` (failure_response): risk_level_match
- `failure-eval-021` (failure_response): citations_present
- `failure-eval-022` (failure_response): required_action_types_present
- `failure-eval-023` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-003` (robot_task_prioritization): required_task_types_present
- `robot-eval-004` (robot_task_prioritization): risk_level_match, required_task_types_present
- `robot-eval-006` (robot_task_prioritization): required_task_types_present
- `robot-eval-007` (robot_task_prioritization): risk_level_match
- `robot-eval-008` (robot_task_prioritization): risk_level_match
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): citations_present
- `robot-eval-011` (robot_task_prioritization): citations_present
- `robot-eval-012` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-013` (robot_task_prioritization): required_task_types_present
- `robot-eval-014` (robot_task_prioritization): required_task_types_present
- `robot-eval-015` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-016` (robot_task_prioritization): required_task_types_present
- `edge-eval-005` (edge_case): risk_level_match
- `edge-eval-006` (edge_case): risk_level_match
- `edge-eval-011` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-013` (edge_case): required_action_types_present
- `edge-eval-014` (edge_case): risk_level_match
- `edge-eval-015` (edge_case): risk_level_match
- `edge-eval-016` (edge_case): risk_level_match
- `edge-eval-019` (edge_case): risk_level_match
- `edge-eval-020` (edge_case): risk_level_match
- `edge-eval-021` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-022` (edge_case): citations_present, required_action_types_present
- `edge-eval-025` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-028` (edge_case): citations_present, required_action_types_present
- `seasonal-eval-002` (seasonal): risk_level_match
- `seasonal-eval-004` (seasonal): risk_level_match
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-007` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-012` (seasonal): risk_level_match
- `seasonal-eval-013` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match
- `seasonal-eval-017` (seasonal): risk_level_match
- `seasonal-eval-018` (seasonal): required_action_types_present
- `seasonal-eval-020` (seasonal): risk_level_match
- `seasonal-eval-021` (seasonal): risk_level_match
- `seasonal-eval-022` (seasonal): required_action_types_present

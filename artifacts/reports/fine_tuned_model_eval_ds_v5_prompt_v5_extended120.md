# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v5-prompt-v5-eval-v1-20260412-075506:DTbkkFBo`
- evaluated_at: `2026-04-12T09:31:35+00:00`
- total_cases: `120`
- passed_cases: `65`
- pass_rate: `0.5417`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 16 | 10 | 0.625 |
| climate_risk | 5 | 2 | 0.4 |
| edge_case | 16 | 7 | 0.4375 |
| failure_response | 12 | 5 | 0.4167 |
| forbidden_action | 12 | 9 | 0.75 |
| harvest_drying | 5 | 4 | 0.8 |
| nutrient_risk | 5 | 4 | 0.8 |
| pest_disease_risk | 5 | 4 | 0.8 |
| robot_task_prioritization | 8 | 2 | 0.25 |
| rootzone_diagnosis | 5 | 4 | 0.8 |
| safety_policy | 5 | 0 | 0.0 |
| seasonal | 16 | 10 | 0.625 |
| sensor_fault | 5 | 1 | 0.2 |
| state_judgement | 5 | 3 | 0.6 |

## Confidence

- average_confidence: `0.79`
- average_confidence_on_pass: `0.7773`
- average_confidence_on_fail: `0.8039`

## Top Failed Checks

- `risk_level_match`: `35`
- `required_action_types_present`: `22`
- `required_task_types_present`: `6`
- `citations_present`: `5`
- `decision_match`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `7`
- `confidence_present`: `1`
- `confidence_in_range`: `1`
- `retrieval_coverage_present`: `1`
- `retrieval_coverage_valid`: `1`

## Failed Cases

- `pepper-eval-008` (safety_policy): required_action_types_present
- `pepper-eval-009` (climate_risk): risk_level_match
- `pepper-eval-010` (climate_risk): required_action_types_present
- `pepper-eval-012` (climate_risk): required_action_types_present
- `pepper-eval-014` (state_judgement): risk_level_match, required_action_types_present
- `pepper-eval-016` (state_judgement): risk_level_match
- `pepper-eval-020` (rootzone_diagnosis): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-025` (sensor_fault): risk_level_match
- `pepper-eval-026` (sensor_fault): risk_level_match
- `pepper-eval-027` (sensor_fault): risk_level_match
- `pepper-eval-028` (sensor_fault): risk_level_match
- `pepper-eval-029` (pest_disease_risk): risk_level_match
- `pepper-eval-036` (harvest_drying): risk_level_match
- `pepper-eval-037` (safety_policy): required_action_types_present
- `pepper-eval-038` (safety_policy): required_action_types_present
- `pepper-eval-039` (safety_policy): required_action_types_present
- `pepper-eval-040` (safety_policy): required_action_types_present
- `action-eval-002` (action_recommendation): risk_level_match
- `action-eval-005` (action_recommendation): required_action_types_present
- `action-eval-006` (action_recommendation): risk_level_match
- `action-eval-007` (action_recommendation): risk_level_match
- `action-eval-008` (action_recommendation): risk_level_match
- `action-eval-016` (action_recommendation): risk_level_match
- `forbidden-eval-003` (forbidden_action): citations_present
- `forbidden-eval-008` (forbidden_action): risk_level_match
- `forbidden-eval-010` (forbidden_action): decision_match
- `failure-eval-003` (failure_response): citations_present
- `failure-eval-004` (failure_response): citations_present
- `failure-eval-006` (failure_response): risk_level_match
- `failure-eval-008` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-012` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-001` (robot_task_prioritization): required_task_types_present
- `robot-eval-003` (robot_task_prioritization): required_task_types_present
- `robot-eval-004` (robot_task_prioritization): required_task_types_present
- `robot-eval-006` (robot_task_prioritization): required_task_types_present
- `robot-eval-007` (robot_task_prioritization): required_task_types_present
- `robot-eval-008` (robot_task_prioritization): risk_level_match, required_task_types_present
- `edge-eval-004` (edge_case): required_action_types_present
- `edge-eval-006` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-007` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-008` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-010` (edge_case): required_action_types_present
- `edge-eval-011` (edge_case): risk_level_match
- `edge-eval-014` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-015` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-016` (edge_case): risk_level_match, required_action_types_present
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-014` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match
- `seasonal-eval-016` (seasonal): risk_level_match, required_action_types_present

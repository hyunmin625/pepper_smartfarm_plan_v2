# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v1-prompt-v1-eval-v1-20260412-004953:DTV5z1FR`
- evaluated_at: `2026-04-11T17:09:24+00:00`
- total_cases: `24`
- passed_cases: `4`
- pass_rate: `0.1667`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 2 | 0 | 0.0 |
| climate_risk | 1 | 0 | 0.0 |
| edge_case | 4 | 2 | 0.5 |
| failure_response | 2 | 0 | 0.0 |
| forbidden_action | 2 | 0 | 0.0 |
| harvest_drying | 1 | 0 | 0.0 |
| nutrient_risk | 1 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 2 | 1 | 0.5 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 0 | 0.0 |
| seasonal | 4 | 0 | 0.0 |
| sensor_fault | 1 | 0 | 0.0 |
| state_judgement | 1 | 0 | 0.0 |

## Confidence

- average_confidence: `0.8086`
- average_confidence_on_pass: `0.8`
- average_confidence_on_fail: `0.81`

## Top Failed Checks

- `required_action_types_present`: `11`
- `risk_level_match`: `11`
- `blocked_action_type_match`: `2`
- `citations_present`: `1`
- `decision_match`: `1`
- `required_task_types_present`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `5`
- `retrieval_coverage_present`: `4`
- `retrieval_coverage_valid`: `4`

## Failed Cases

- `pepper-eval-001` (state_judgement): required_action_types_present
- `pepper-eval-002` (climate_risk): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): citations_present
- `pepper-eval-005` (sensor_fault): risk_level_match, required_action_types_present
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-007` (harvest_drying): required_action_types_present
- `pepper-eval-008` (safety_policy): required_action_types_present
- `action-eval-001` (action_recommendation): required_action_types_present
- `action-eval-002` (action_recommendation): risk_level_match
- `forbidden-eval-001` (forbidden_action): blocked_action_type_match
- `forbidden-eval-002` (forbidden_action): decision_match, blocked_action_type_match
- `failure-eval-001` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-002` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-001` (robot_task_prioritization): risk_level_match, required_task_types_present
- `edge-eval-003` (edge_case): risk_level_match
- `edge-eval-004` (edge_case): required_action_types_present
- `seasonal-eval-001` (seasonal): risk_level_match
- `seasonal-eval-002` (seasonal): risk_level_match
- `seasonal-eval-003` (seasonal): required_action_types_present
- `seasonal-eval-004` (seasonal): risk_level_match, required_action_types_present

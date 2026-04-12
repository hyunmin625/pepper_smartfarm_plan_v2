# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- evaluated_at: `2026-04-12T12:33:43+00:00`
- total_cases: `160`
- passed_cases: `92`
- pass_rate: `0.575`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 20 | 16 | 0.8 |
| climate_risk | 5 | 5 | 1.0 |
| edge_case | 24 | 10 | 0.4167 |
| failure_response | 18 | 7 | 0.3889 |
| forbidden_action | 16 | 11 | 0.6875 |
| harvest_drying | 5 | 4 | 0.8 |
| nutrient_risk | 6 | 4 | 0.6667 |
| pest_disease_risk | 5 | 5 | 1.0 |
| robot_task_prioritization | 12 | 3 | 0.25 |
| rootzone_diagnosis | 6 | 5 | 0.8333 |
| safety_policy | 7 | 3 | 0.4286 |
| seasonal | 24 | 13 | 0.5417 |
| sensor_fault | 7 | 2 | 0.2857 |
| state_judgement | 5 | 4 | 0.8 |

## Confidence

- average_confidence: `0.7911`
- average_confidence_on_pass: `0.796`
- average_confidence_on_fail: `0.7848`

## Top Failed Checks

- `risk_level_match`: `44`
- `required_action_types_present`: `38`
- `citations_present`: `20`
- `required_task_types_present`: `7`
- `forbidden_action_types_absent`: `6`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `3`

## Failed Cases

- `pepper-eval-014` (state_judgement): required_action_types_present
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-025` (sensor_fault): risk_level_match
- `pepper-eval-026` (sensor_fault): risk_level_match, required_action_types_present
- `pepper-eval-028` (sensor_fault): risk_level_match
- `pepper-eval-036` (harvest_drying): risk_level_match
- `pepper-eval-039` (safety_policy): required_action_types_present
- `pepper-eval-040` (safety_policy): required_action_types_present
- `pepper-eval-041` (safety_policy): citations_present
- `pepper-eval-042` (safety_policy): risk_level_match, citations_present, required_action_types_present
- `pepper-eval-043` (sensor_fault): risk_level_match, required_action_types_present
- `pepper-eval-044` (sensor_fault): risk_level_match
- `pepper-eval-045` (rootzone_diagnosis): risk_level_match, required_action_types_present
- `pepper-eval-046` (nutrient_risk): risk_level_match, required_action_types_present
- `pepper-eval-047` (failure_response): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `action-eval-017` (action_recommendation): citations_present, required_action_types_present, forbidden_action_types_absent
- `action-eval-018` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-019` (action_recommendation): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `action-eval-020` (action_recommendation): citations_present, required_action_types_present, forbidden_action_types_absent
- `forbidden-eval-005` (forbidden_action): risk_level_match
- `forbidden-eval-013` (forbidden_action): citations_present
- `forbidden-eval-014` (forbidden_action): citations_present
- `forbidden-eval-015` (forbidden_action): risk_level_match
- `forbidden-eval-016` (forbidden_action): citations_present
- `failure-eval-001` (failure_response): risk_level_match
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-008` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-009` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match
- `failure-eval-012` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-013` (failure_response): risk_level_match
- `failure-eval-014` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-016` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-003` (robot_task_prioritization): required_task_types_present
- `robot-eval-004` (robot_task_prioritization): required_task_types_present
- `robot-eval-006` (robot_task_prioritization): required_task_types_present
- `robot-eval-007` (robot_task_prioritization): required_task_types_present
- `robot-eval-008` (robot_task_prioritization): risk_level_match, required_task_types_present
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-011` (robot_task_prioritization): risk_level_match, citations_present, required_task_types_present
- `robot-eval-012` (robot_task_prioritization): citations_present, required_task_types_present
- `edge-eval-004` (edge_case): required_action_types_present
- `edge-eval-006` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-008` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-010` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-014` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-015` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-016` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-017` (edge_case): required_action_types_present
- `edge-eval-018` (edge_case): citations_present, required_action_types_present, forbidden_action_types_absent
- `edge-eval-019` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-020` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-021` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-022` (edge_case): citations_present, required_action_types_present
- `edge-eval-023` (edge_case): citations_present, required_action_types_present
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-013` (seasonal): risk_level_match
- `seasonal-eval-017` (seasonal): risk_level_match
- `seasonal-eval-018` (seasonal): risk_level_match, citations_present, required_action_types_present
- `seasonal-eval-019` (seasonal): citations_present
- `seasonal-eval-020` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-021` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-023` (seasonal): risk_level_match, required_action_types_present
- `seasonal-eval-024` (seasonal): citations_present

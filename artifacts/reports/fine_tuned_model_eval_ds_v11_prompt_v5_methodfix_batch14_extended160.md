# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- evaluated_at: `2026-04-12T17:16:21+00:00`
- total_cases: `160`
- passed_cases: `120`
- pass_rate: `0.75`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 20 | 16 | 0.8 |
| climate_risk | 5 | 3 | 0.6 |
| edge_case | 24 | 20 | 0.8333 |
| failure_response | 18 | 8 | 0.4444 |
| forbidden_action | 16 | 12 | 0.75 |
| harvest_drying | 5 | 5 | 1.0 |
| nutrient_risk | 6 | 5 | 0.8333 |
| pest_disease_risk | 5 | 4 | 0.8 |
| robot_task_prioritization | 12 | 8 | 0.6667 |
| rootzone_diagnosis | 6 | 3 | 0.5 |
| safety_policy | 7 | 5 | 0.7143 |
| seasonal | 24 | 20 | 0.8333 |
| sensor_fault | 7 | 7 | 1.0 |
| state_judgement | 5 | 4 | 0.8 |

## Confidence

- average_confidence: `0.8137`
- average_confidence_on_pass: `0.8024`
- average_confidence_on_fail: `0.8478`

## Top Failed Checks

- `risk_level_match`: `20`
- `required_action_types_present`: `18`
- `citations_present`: `11`
- `forbidden_action_types_absent`: `2`
- `decision_match`: `1`
- `required_task_types_present`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `3`
- `retrieval_coverage_present`: `1`
- `retrieval_coverage_valid`: `1`

## Failed Cases

- `pepper-eval-003` (rootzone_diagnosis): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-010` (climate_risk): required_action_types_present
- `pepper-eval-012` (climate_risk): required_action_types_present, forbidden_action_types_absent
- `pepper-eval-014` (state_judgement): risk_level_match, required_action_types_present
- `pepper-eval-017` (rootzone_diagnosis): required_action_types_present
- `pepper-eval-018` (rootzone_diagnosis): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-037` (safety_policy): required_action_types_present
- `pepper-eval-038` (safety_policy): required_action_types_present
- `pepper-eval-047` (failure_response): citations_present
- `action-eval-003` (action_recommendation): required_action_types_present
- `action-eval-007` (action_recommendation): risk_level_match
- `action-eval-017` (action_recommendation): citations_present
- `action-eval-020` (action_recommendation): citations_present
- `forbidden-eval-010` (forbidden_action): decision_match
- `forbidden-eval-013` (forbidden_action): citations_present
- `forbidden-eval-014` (forbidden_action): citations_present
- `forbidden-eval-015` (forbidden_action): risk_level_match
- `failure-eval-001` (failure_response): risk_level_match
- `failure-eval-003` (failure_response): required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-005` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-006` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-007` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-014` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-016` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): citations_present
- `robot-eval-011` (robot_task_prioritization): citations_present
- `robot-eval-012` (robot_task_prioritization): citations_present, required_task_types_present
- `edge-eval-009` (edge_case): risk_level_match
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-021` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-022` (edge_case): citations_present, required_action_types_present
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-008` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match

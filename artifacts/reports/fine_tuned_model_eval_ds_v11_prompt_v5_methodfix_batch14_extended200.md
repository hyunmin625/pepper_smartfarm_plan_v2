# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- evaluated_at: `2026-04-12T17:28:14+00:00`
- total_cases: `200`
- passed_cases: `140`
- pass_rate: `0.7`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 19 | 0.6786 |
| climate_risk | 7 | 5 | 0.7143 |
| edge_case | 28 | 20 | 0.7143 |
| failure_response | 26 | 13 | 0.5 |
| forbidden_action | 20 | 14 | 0.7 |
| harvest_drying | 6 | 6 | 1.0 |
| nutrient_risk | 8 | 5 | 0.625 |
| pest_disease_risk | 6 | 6 | 1.0 |
| robot_task_prioritization | 16 | 9 | 0.5625 |
| rootzone_diagnosis | 8 | 6 | 0.75 |
| safety_policy | 9 | 8 | 0.8889 |
| seasonal | 24 | 16 | 0.6667 |
| sensor_fault | 9 | 9 | 1.0 |
| state_judgement | 5 | 4 | 0.8 |

## Confidence

- average_confidence: `0.8119`
- average_confidence_on_pass: `0.8022`
- average_confidence_on_fail: `0.8346`

## Top Failed Checks

- `risk_level_match`: `31`
- `required_action_types_present`: `21`
- `citations_present`: `17`
- `required_task_types_present`: `3`
- `forbidden_action_types_absent`: `3`
- `decision_match`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `4`
- `retrieval_coverage_present`: `1`
- `retrieval_coverage_valid`: `1`

## Failed Cases

- `pepper-eval-003` (rootzone_diagnosis): risk_level_match
- `pepper-eval-010` (climate_risk): required_action_types_present
- `pepper-eval-014` (state_judgement): required_action_types_present
- `pepper-eval-018` (rootzone_diagnosis): risk_level_match
- `pepper-eval-022` (nutrient_risk): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-037` (safety_policy): required_action_types_present
- `pepper-eval-047` (failure_response): citations_present
- `pepper-eval-049` (climate_risk): risk_level_match
- `pepper-eval-056` (nutrient_risk): risk_level_match
- `action-eval-003` (action_recommendation): required_action_types_present
- `action-eval-007` (action_recommendation): risk_level_match
- `action-eval-016` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-017` (action_recommendation): citations_present
- `action-eval-020` (action_recommendation): citations_present
- `action-eval-021` (action_recommendation): risk_level_match
- `action-eval-022` (action_recommendation): risk_level_match, required_action_types_present
- `action-eval-023` (action_recommendation): risk_level_match
- `action-eval-027` (action_recommendation): citations_present
- `forbidden-eval-008` (forbidden_action): risk_level_match
- `forbidden-eval-010` (forbidden_action): decision_match
- `forbidden-eval-013` (forbidden_action): citations_present
- `forbidden-eval-014` (forbidden_action): citations_present
- `forbidden-eval-015` (forbidden_action): risk_level_match
- `forbidden-eval-020` (forbidden_action): citations_present
- `failure-eval-003` (failure_response): required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-005` (failure_response): required_action_types_present
- `failure-eval-006` (failure_response): required_action_types_present
- `failure-eval-007` (failure_response): risk_level_match
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-014` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-017` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-019` (failure_response): risk_level_match
- `failure-eval-020` (failure_response): citations_present
- `failure-eval-021` (failure_response): citations_present
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): citations_present
- `robot-eval-011` (robot_task_prioritization): citations_present
- `robot-eval-012` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-013` (robot_task_prioritization): required_task_types_present
- `robot-eval-014` (robot_task_prioritization): required_task_types_present
- `robot-eval-015` (robot_task_prioritization): risk_level_match, citations_present
- `edge-eval-003` (edge_case): risk_level_match
- `edge-eval-009` (edge_case): risk_level_match
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-018` (edge_case): risk_level_match, required_action_types_present, forbidden_action_types_absent
- `edge-eval-021` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-022` (edge_case): citations_present, required_action_types_present
- `edge-eval-027` (edge_case): required_action_types_present, forbidden_action_types_absent
- `edge-eval-028` (edge_case): citations_present, required_action_types_present
- `seasonal-eval-003` (seasonal): required_action_types_present
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-008` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-012` (seasonal): risk_level_match
- `seasonal-eval-013` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match

# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v12-prompt-v5-methodfix-eval-v2-2026-2026041:DUhIsVmY`
- evaluated_at: `2026-04-15T00:35:15+00:00`
- total_cases: `200`
- passed_cases: `22`
- pass_rate: `0.11`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 3 | 0.1071 |
| climate_risk | 7 | 0 | 0.0 |
| edge_case | 28 | 4 | 0.1429 |
| failure_response | 26 | 1 | 0.0385 |
| forbidden_action | 20 | 0 | 0.0 |
| harvest_drying | 6 | 2 | 0.3333 |
| nutrient_risk | 8 | 0 | 0.0 |
| pest_disease_risk | 6 | 0 | 0.0 |
| robot_task_prioritization | 16 | 2 | 0.125 |
| rootzone_diagnosis | 8 | 0 | 0.0 |
| safety_policy | 9 | 5 | 0.5556 |
| seasonal | 24 | 0 | 0.0 |
| sensor_fault | 9 | 5 | 0.5556 |
| state_judgement | 5 | 0 | 0.0 |

## Confidence

- average_confidence: `0.7916`
- average_confidence_on_pass: `0.7691`
- average_confidence_on_fail: `0.7944`

## Top Failed Checks

- `citations_present`: `168`
- `risk_level_match`: `64`
- `required_action_types_present`: `48`
- `blocked_action_type_match`: `20`
- `decision_match`: `13`
- `required_task_types_present`: `12`
- `forbidden_action_types_absent`: `11`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `9`
- `retrieval_coverage_present`: `3`
- `retrieval_coverage_valid`: `3`

## Failed Cases

- `pepper-eval-001` (state_judgement): citations_present
- `pepper-eval-002` (climate_risk): citations_present
- `pepper-eval-003` (rootzone_diagnosis): risk_level_match, citations_present
- `pepper-eval-004` (nutrient_risk): citations_present
- `pepper-eval-006` (pest_disease_risk): citations_present
- `pepper-eval-009` (climate_risk): citations_present
- `pepper-eval-010` (climate_risk): risk_level_match, citations_present
- `pepper-eval-011` (climate_risk): risk_level_match, citations_present
- `pepper-eval-012` (climate_risk): citations_present
- `pepper-eval-013` (state_judgement): risk_level_match, citations_present
- `pepper-eval-014` (state_judgement): risk_level_match, citations_present, required_action_types_present
- `pepper-eval-015` (state_judgement): citations_present
- `pepper-eval-016` (state_judgement): risk_level_match, citations_present
- `pepper-eval-017` (rootzone_diagnosis): citations_present, required_action_types_present
- `pepper-eval-018` (rootzone_diagnosis): citations_present
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match, citations_present, required_action_types_present
- `pepper-eval-020` (rootzone_diagnosis): citations_present, required_action_types_present
- `pepper-eval-021` (nutrient_risk): citations_present
- `pepper-eval-022` (nutrient_risk): citations_present
- `pepper-eval-023` (nutrient_risk): risk_level_match, citations_present
- `pepper-eval-024` (nutrient_risk): risk_level_match, citations_present
- `pepper-eval-029` (pest_disease_risk): citations_present
- `pepper-eval-030` (pest_disease_risk): citations_present
- `pepper-eval-031` (pest_disease_risk): citations_present
- `pepper-eval-032` (pest_disease_risk): citations_present
- `pepper-eval-034` (harvest_drying): citations_present
- `pepper-eval-035` (harvest_drying): citations_present
- `pepper-eval-036` (harvest_drying): risk_level_match, citations_present
- `pepper-eval-041` (safety_policy): citations_present
- `pepper-eval-042` (safety_policy): risk_level_match, citations_present, required_action_types_present
- `pepper-eval-043` (sensor_fault): citations_present
- `pepper-eval-044` (sensor_fault): citations_present
- `pepper-eval-045` (rootzone_diagnosis): citations_present
- `pepper-eval-046` (nutrient_risk): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `pepper-eval-047` (failure_response): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `pepper-eval-048` (failure_response): citations_present
- `pepper-eval-049` (climate_risk): risk_level_match, citations_present
- `pepper-eval-050` (climate_risk): risk_level_match, citations_present
- `pepper-eval-051` (rootzone_diagnosis): citations_present, required_action_types_present, forbidden_action_types_absent
- `pepper-eval-052` (rootzone_diagnosis): citations_present
- `pepper-eval-053` (sensor_fault): citations_present
- `pepper-eval-054` (sensor_fault): citations_present
- `pepper-eval-055` (nutrient_risk): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `pepper-eval-056` (nutrient_risk): citations_present, required_action_types_present
- `pepper-eval-057` (safety_policy): citations_present
- `pepper-eval-058` (safety_policy): citations_present
- `pepper-eval-059` (harvest_drying): citations_present
- `pepper-eval-060` (pest_disease_risk): citations_present
- `action-eval-001` (action_recommendation): citations_present
- `action-eval-002` (action_recommendation): citations_present, required_action_types_present
- `action-eval-003` (action_recommendation): citations_present, required_action_types_present
- `action-eval-004` (action_recommendation): citations_present
- `action-eval-006` (action_recommendation): risk_level_match, citations_present
- `action-eval-007` (action_recommendation): citations_present
- `action-eval-009` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-010` (action_recommendation): citations_present
- `action-eval-012` (action_recommendation): citations_present
- `action-eval-013` (action_recommendation): citations_present
- `action-eval-014` (action_recommendation): citations_present
- `action-eval-015` (action_recommendation): citations_present
- `action-eval-016` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-017` (action_recommendation): citations_present
- `action-eval-018` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-019` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-020` (action_recommendation): citations_present, required_action_types_present, forbidden_action_types_absent
- `action-eval-021` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-022` (action_recommendation): citations_present, required_action_types_present, forbidden_action_types_absent
- `action-eval-023` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-024` (action_recommendation): risk_level_match, citations_present, required_action_types_present
- `action-eval-025` (action_recommendation): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `action-eval-026` (action_recommendation): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `action-eval-027` (action_recommendation): citations_present
- `action-eval-028` (action_recommendation): citations_present, required_action_types_present
- `forbidden-eval-001` (forbidden_action): citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-002` (forbidden_action): citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-003` (forbidden_action): citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-004` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-005` (forbidden_action): citations_present, blocked_action_type_match
- `forbidden-eval-006` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-007` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-008` (forbidden_action): risk_level_match, citations_present, blocked_action_type_match
- `forbidden-eval-009` (forbidden_action): citations_present, blocked_action_type_match
- `forbidden-eval-010` (forbidden_action): citations_present, blocked_action_type_match
- `forbidden-eval-011` (forbidden_action): citations_present, blocked_action_type_match
- `forbidden-eval-012` (forbidden_action): blocked_action_type_match
- `forbidden-eval-013` (forbidden_action): citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-014` (forbidden_action): risk_level_match, citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-015` (forbidden_action): risk_level_match, citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-016` (forbidden_action): risk_level_match, citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-017` (forbidden_action): risk_level_match, citations_present, blocked_action_type_match
- `forbidden-eval-018` (forbidden_action): citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-019` (forbidden_action): risk_level_match, citations_present, decision_match, blocked_action_type_match
- `forbidden-eval-020` (forbidden_action): citations_present, decision_match, blocked_action_type_match
- `failure-eval-001` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-002` (failure_response): citations_present
- `failure-eval-003` (failure_response): citations_present, required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-005` (failure_response): citations_present, required_action_types_present
- `failure-eval-006` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-007` (failure_response): citations_present, required_action_types_present
- `failure-eval-008` (failure_response): citations_present
- `failure-eval-009` (failure_response): risk_level_match
- `failure-eval-011` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-012` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-013` (failure_response): citations_present
- `failure-eval-014` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-015` (failure_response): citations_present
- `failure-eval-016` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-017` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-018` (failure_response): citations_present
- `failure-eval-019` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-020` (failure_response): citations_present
- `failure-eval-021` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-022` (failure_response): citations_present
- `failure-eval-023` (failure_response): risk_level_match, citations_present, required_action_types_present
- `failure-eval-024` (failure_response): citations_present
- `robot-eval-001` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-003` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-004` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-006` (robot_task_prioritization): required_task_types_present
- `robot-eval-007` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-008` (robot_task_prioritization): risk_level_match, required_task_types_present
- `robot-eval-009` (robot_task_prioritization): citations_present
- `robot-eval-010` (robot_task_prioritization): risk_level_match, citations_present
- `robot-eval-011` (robot_task_prioritization): risk_level_match, citations_present, required_task_types_present
- `robot-eval-012` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-013` (robot_task_prioritization): risk_level_match, citations_present, required_task_types_present
- `robot-eval-014` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-015` (robot_task_prioritization): citations_present, required_task_types_present
- `robot-eval-016` (robot_task_prioritization): citations_present, required_task_types_present
- `edge-eval-001` (edge_case): citations_present
- `edge-eval-002` (edge_case): citations_present
- `edge-eval-003` (edge_case): citations_present
- `edge-eval-006` (edge_case): risk_level_match, citations_present
- `edge-eval-007` (edge_case): citations_present
- `edge-eval-008` (edge_case): citations_present
- `edge-eval-009` (edge_case): risk_level_match, citations_present
- `edge-eval-012` (edge_case): citations_present, required_action_types_present
- `edge-eval-013` (edge_case): citations_present
- `edge-eval-014` (edge_case): citations_present
- `edge-eval-015` (edge_case): risk_level_match, required_action_types_present
- `edge-eval-016` (edge_case): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `edge-eval-017` (edge_case): citations_present
- `edge-eval-018` (edge_case): citations_present
- `edge-eval-019` (edge_case): risk_level_match, citations_present, required_action_types_present
- `edge-eval-020` (edge_case): risk_level_match, citations_present
- `edge-eval-021` (edge_case): citations_present, required_action_types_present
- `edge-eval-022` (edge_case): citations_present, required_action_types_present
- `edge-eval-023` (edge_case): citations_present
- `edge-eval-024` (edge_case): risk_level_match, citations_present, required_action_types_present
- `edge-eval-025` (edge_case): risk_level_match, citations_present
- `edge-eval-026` (edge_case): citations_present
- `edge-eval-027` (edge_case): citations_present
- `edge-eval-028` (edge_case): risk_level_match, citations_present, required_action_types_present
- `seasonal-eval-001` (seasonal): citations_present
- `seasonal-eval-002` (seasonal): citations_present
- `seasonal-eval-003` (seasonal): citations_present
- `seasonal-eval-004` (seasonal): citations_present
- `seasonal-eval-005` (seasonal): citations_present
- `seasonal-eval-006` (seasonal): risk_level_match, citations_present
- `seasonal-eval-007` (seasonal): citations_present
- `seasonal-eval-008` (seasonal): risk_level_match, citations_present
- `seasonal-eval-009` (seasonal): citations_present
- `seasonal-eval-010` (seasonal): risk_level_match, citations_present
- `seasonal-eval-011` (seasonal): risk_level_match, citations_present
- `seasonal-eval-012` (seasonal): citations_present
- `seasonal-eval-013` (seasonal): citations_present
- `seasonal-eval-014` (seasonal): citations_present
- `seasonal-eval-015` (seasonal): risk_level_match, citations_present
- `seasonal-eval-016` (seasonal): citations_present
- `seasonal-eval-017` (seasonal): citations_present
- `seasonal-eval-018` (seasonal): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `seasonal-eval-019` (seasonal): citations_present
- `seasonal-eval-020` (seasonal): citations_present
- `seasonal-eval-021` (seasonal): risk_level_match, citations_present, required_action_types_present, forbidden_action_types_absent
- `seasonal-eval-022` (seasonal): citations_present
- `seasonal-eval-023` (seasonal): citations_present
- `seasonal-eval-024` (seasonal): citations_present

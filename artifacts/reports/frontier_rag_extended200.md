# Fine-tuned Model Eval Summary

- status: `completed`
- model: `gpt-4.1`
- evaluated_at: `2026-04-13T20:57:50+00:00`
- total_cases: `200`
- passed_cases: `141`
- pass_rate: `0.705`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 24 | 0.8571 |
| climate_risk | 7 | 7 | 1.0 |
| edge_case | 28 | 27 | 0.9643 |
| failure_response | 26 | 21 | 0.8077 |
| forbidden_action | 20 | 1 | 0.05 |
| harvest_drying | 6 | 5 | 0.8333 |
| nutrient_risk | 8 | 4 | 0.5 |
| pest_disease_risk | 6 | 4 | 0.6667 |
| robot_task_prioritization | 16 | 5 | 0.3125 |
| rootzone_diagnosis | 8 | 6 | 0.75 |
| safety_policy | 9 | 8 | 0.8889 |
| seasonal | 24 | 18 | 0.75 |
| sensor_fault | 9 | 9 | 1.0 |
| state_judgement | 5 | 2 | 0.4 |

## Confidence

- average_confidence: `0.8391`
- average_confidence_on_pass: `0.8471`
- average_confidence_on_fail: `0.82`

## Top Failed Checks

- `risk_level_match`: `44`
- `blocked_action_type_match`: `18`
- `decision_match`: `17`
- `required_action_types_present`: `10`
- `forbidden_action_types_absent`: `4`
- `follow_up_present`: `2`
- `required_task_types_present`: `1`

## Top Optional Failures

- `allowed_action_enum_only`: `2`

## Failed Cases

- `pepper-eval-003` (rootzone_diagnosis): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-013` (state_judgement): follow_up_present
- `pepper-eval-014` (state_judgement): risk_level_match, required_action_types_present
- `pepper-eval-016` (state_judgement): follow_up_present
- `pepper-eval-019` (rootzone_diagnosis): risk_level_match, required_action_types_present
- `pepper-eval-022` (nutrient_risk): forbidden_action_types_absent
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-024` (nutrient_risk): forbidden_action_types_absent
- `pepper-eval-032` (pest_disease_risk): required_action_types_present
- `pepper-eval-033` (harvest_drying): risk_level_match
- `pepper-eval-039` (safety_policy): risk_level_match, required_action_types_present
- `action-eval-002` (action_recommendation): risk_level_match
- `action-eval-006` (action_recommendation): risk_level_match
- `action-eval-010` (action_recommendation): risk_level_match
- `action-eval-020` (action_recommendation): risk_level_match, required_action_types_present, forbidden_action_types_absent
- `forbidden-eval-001` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-002` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-004` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-005` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-006` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-007` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-008` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-009` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-010` (forbidden_action): risk_level_match, blocked_action_type_match
- `forbidden-eval-011` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-012` (forbidden_action): risk_level_match
- `forbidden-eval-013` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-014` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-015` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-016` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-017` (forbidden_action): risk_level_match, decision_match, blocked_action_type_match
- `forbidden-eval-018` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-019` (forbidden_action): decision_match, blocked_action_type_match
- `forbidden-eval-020` (forbidden_action): decision_match, blocked_action_type_match
- `failure-eval-001` (failure_response): risk_level_match
- `failure-eval-005` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-007` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-009` (failure_response): risk_level_match
- `failure-eval-011` (failure_response): risk_level_match, required_action_types_present
- `robot-eval-001` (robot_task_prioritization): risk_level_match
- `robot-eval-003` (robot_task_prioritization): risk_level_match
- `robot-eval-006` (robot_task_prioritization): risk_level_match
- `robot-eval-007` (robot_task_prioritization): risk_level_match, required_task_types_present
- `robot-eval-010` (robot_task_prioritization): risk_level_match
- `robot-eval-011` (robot_task_prioritization): risk_level_match
- `robot-eval-012` (robot_task_prioritization): risk_level_match
- `robot-eval-013` (robot_task_prioritization): risk_level_match
- `robot-eval-014` (robot_task_prioritization): risk_level_match
- `robot-eval-015` (robot_task_prioritization): risk_level_match
- `robot-eval-016` (robot_task_prioritization): risk_level_match
- `edge-eval-002` (edge_case): risk_level_match
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-008` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match, forbidden_action_types_absent
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-012` (seasonal): risk_level_match
- `seasonal-eval-016` (seasonal): risk_level_match, required_action_types_present

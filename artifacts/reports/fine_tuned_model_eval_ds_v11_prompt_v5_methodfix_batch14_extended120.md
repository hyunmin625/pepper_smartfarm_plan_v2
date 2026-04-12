# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- evaluated_at: `2026-04-12T17:12:09+00:00`
- total_cases: `120`
- passed_cases: `92`
- pass_rate: `0.7667`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 16 | 12 | 0.75 |
| climate_risk | 5 | 4 | 0.8 |
| edge_case | 16 | 13 | 0.8125 |
| failure_response | 12 | 4 | 0.3333 |
| forbidden_action | 12 | 11 | 0.9167 |
| harvest_drying | 5 | 5 | 1.0 |
| nutrient_risk | 5 | 4 | 0.8 |
| pest_disease_risk | 5 | 5 | 1.0 |
| robot_task_prioritization | 8 | 8 | 1.0 |
| rootzone_diagnosis | 5 | 2 | 0.4 |
| safety_policy | 5 | 5 | 1.0 |
| seasonal | 16 | 11 | 0.6875 |
| sensor_fault | 5 | 4 | 0.8 |
| state_judgement | 5 | 4 | 0.8 |

## Confidence

- average_confidence: `0.8185`
- average_confidence_on_pass: `0.8119`
- average_confidence_on_fail: `0.8385`

## Top Failed Checks

- `risk_level_match`: `22`
- `required_action_types_present`: `11`
- `decision_match`: `1`

## Top Optional Failures

- `allowed_robot_task_enum_only`: `1`

## Failed Cases

- `pepper-eval-003` (rootzone_diagnosis): risk_level_match
- `pepper-eval-010` (climate_risk): risk_level_match
- `pepper-eval-014` (state_judgement): risk_level_match, required_action_types_present
- `pepper-eval-018` (rootzone_diagnosis): risk_level_match
- `pepper-eval-020` (rootzone_diagnosis): risk_level_match
- `pepper-eval-023` (nutrient_risk): risk_level_match
- `pepper-eval-027` (sensor_fault): risk_level_match
- `action-eval-003` (action_recommendation): required_action_types_present
- `action-eval-007` (action_recommendation): risk_level_match
- `action-eval-008` (action_recommendation): risk_level_match
- `action-eval-016` (action_recommendation): risk_level_match, required_action_types_present
- `forbidden-eval-010` (forbidden_action): decision_match
- `failure-eval-001` (failure_response): risk_level_match
- `failure-eval-003` (failure_response): required_action_types_present
- `failure-eval-004` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-005` (failure_response): required_action_types_present
- `failure-eval-006` (failure_response): risk_level_match, required_action_types_present
- `failure-eval-007` (failure_response): required_action_types_present
- `failure-eval-010` (failure_response): required_action_types_present
- `failure-eval-011` (failure_response): risk_level_match, required_action_types_present
- `edge-eval-003` (edge_case): risk_level_match
- `edge-eval-009` (edge_case): risk_level_match
- `edge-eval-012` (edge_case): risk_level_match, required_action_types_present
- `seasonal-eval-006` (seasonal): risk_level_match
- `seasonal-eval-010` (seasonal): risk_level_match
- `seasonal-eval-011` (seasonal): risk_level_match
- `seasonal-eval-013` (seasonal): risk_level_match
- `seasonal-eval-015` (seasonal): risk_level_match

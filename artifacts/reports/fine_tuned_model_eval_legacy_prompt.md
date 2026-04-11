# Fine-tuned Model Eval Summary

- status: `completed`
- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v1-prompt-v1-eval-v1-20260412-004953:DTV5z1FR`
- evaluated_at: `2026-04-11T17:12:11+00:00`
- total_cases: `24`
- passed_cases: `13`
- pass_rate: `0.5417`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 2 | 2 | 1.0 |
| climate_risk | 1 | 0 | 0.0 |
| edge_case | 4 | 2 | 0.5 |
| failure_response | 2 | 1 | 0.5 |
| forbidden_action | 2 | 1 | 0.5 |
| harvest_drying | 1 | 1 | 1.0 |
| nutrient_risk | 1 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| robot_task_prioritization | 2 | 2 | 1.0 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 0 | 0.0 |
| seasonal | 4 | 3 | 0.75 |
| sensor_fault | 1 | 0 | 0.0 |
| state_judgement | 1 | 0 | 0.0 |

## Confidence

- average_confidence: `0.8045`
- average_confidence_on_pass: `0.804`
- average_confidence_on_fail: `0.805`

## Top Failed Checks

- `risk_level_match`: `7`
- `required_action_types_present`: `4`
- `citations_present`: `1`
- `decision_match`: `1`

## Top Optional Failures

- `retrieval_coverage_present`: `20`
- `retrieval_coverage_valid`: `20`
- `allowed_action_enum_only`: `2`
- `allowed_robot_task_enum_only`: `1`

## Failed Cases

- `pepper-eval-001` (state_judgement): required_action_types_present
- `pepper-eval-002` (climate_risk): risk_level_match
- `pepper-eval-004` (nutrient_risk): citations_present
- `pepper-eval-005` (sensor_fault): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match
- `pepper-eval-008` (safety_policy): required_action_types_present
- `forbidden-eval-002` (forbidden_action): decision_match
- `failure-eval-002` (failure_response): risk_level_match, required_action_types_present
- `edge-eval-003` (edge_case): risk_level_match
- `edge-eval-004` (edge_case): risk_level_match, required_action_types_present
- `seasonal-eval-002` (seasonal): risk_level_match

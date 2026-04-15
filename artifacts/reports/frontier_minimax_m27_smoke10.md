# Fine-tuned Model Eval Summary

- status: `completed`
- model: `MiniMax-M2.7`
- evaluated_at: `2026-04-14T04:15:50+00:00`
- total_cases: `10`
- passed_cases: `4`
- pass_rate: `0.4`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| climate_risk | 3 | 3 | 1.0 |
| harvest_drying | 1 | 0 | 0.0 |
| nutrient_risk | 1 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| rootzone_diagnosis | 1 | 0 | 0.0 |
| safety_policy | 1 | 0 | 0.0 |
| sensor_fault | 1 | 1 | 1.0 |
| state_judgement | 1 | 0 | 0.0 |

## Confidence

- average_confidence: `0.64`
- average_confidence_on_pass: `0.5875`
- average_confidence_on_fail: `0.682`

## Top Failed Checks

- `required_action_types_present`: `5`
- `risk_level_match`: `3`
- `follow_up_present`: `2`

## Top Optional Failures

- `confidence_present`: `1`
- `confidence_in_range`: `1`
- `retrieval_coverage_present`: `1`
- `retrieval_coverage_valid`: `1`

## Failed Cases

- `pepper-eval-001` (state_judgement): follow_up_present
- `pepper-eval-003` (rootzone_diagnosis): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match, required_action_types_present
- `pepper-eval-006` (pest_disease_risk): required_action_types_present
- `pepper-eval-007` (harvest_drying): risk_level_match, follow_up_present, required_action_types_present
- `pepper-eval-008` (safety_policy): required_action_types_present

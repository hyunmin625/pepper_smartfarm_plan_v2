# Fine-tuned Model Eval Summary

- status: `completed`
- model: `gpt-4.1`
- evaluated_at: `2026-04-13T20:34:47+00:00`
- total_cases: `10`
- passed_cases: `7`
- pass_rate: `0.7`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| climate_risk | 3 | 3 | 1.0 |
| harvest_drying | 1 | 1 | 1.0 |
| nutrient_risk | 1 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| rootzone_diagnosis | 1 | 0 | 0.0 |
| safety_policy | 1 | 1 | 1.0 |
| sensor_fault | 1 | 1 | 1.0 |
| state_judgement | 1 | 1 | 1.0 |

## Confidence

- average_confidence: `0.835`
- average_confidence_on_pass: `0.8143`
- average_confidence_on_fail: `0.8833`

## Top Failed Checks

- `risk_level_match`: `3`
- `required_action_types_present`: `1`

## Top Optional Failures

- 없음

## Failed Cases

- `pepper-eval-003` (rootzone_diagnosis): risk_level_match, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match

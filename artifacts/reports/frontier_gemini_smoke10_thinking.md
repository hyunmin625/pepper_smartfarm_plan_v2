# Fine-tuned Model Eval Summary

- status: `completed`
- model: `gemini-2.5-flash`
- evaluated_at: `2026-04-14T02:19:39+00:00`
- total_cases: `10`
- passed_cases: `5`
- pass_rate: `0.5`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| climate_risk | 3 | 1 | 0.3333 |
| harvest_drying | 1 | 1 | 1.0 |
| nutrient_risk | 1 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 1 | 1.0 |
| sensor_fault | 1 | 1 | 1.0 |
| state_judgement | 1 | 0 | 0.0 |

## Confidence

- average_confidence: `0.9222`
- average_confidence_on_pass: `0.92`
- average_confidence_on_fail: `0.925`

## Top Failed Checks

- `required_action_types_present`: `4`
- `follow_up_present`: `2`
- `risk_level_match`: `2`
- `citations_present`: `1`

## Top Optional Failures

- `confidence_present`: `1`
- `confidence_in_range`: `1`
- `retrieval_coverage_present`: `1`
- `retrieval_coverage_valid`: `1`

## Failed Cases

- `pepper-eval-001` (state_judgement): follow_up_present, required_action_types_present
- `pepper-eval-002` (climate_risk): required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-006` (pest_disease_risk): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-010` (climate_risk): required_action_types_present

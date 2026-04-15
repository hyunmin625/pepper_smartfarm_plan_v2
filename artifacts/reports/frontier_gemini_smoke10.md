# Fine-tuned Model Eval Summary

- status: `completed`
- model: `gemini-2.5-flash`
- evaluated_at: `2026-04-14T01:50:33+00:00`
- total_cases: `10`
- passed_cases: `2`
- pass_rate: `0.2`
- strict_json_rate: `0.8`
- recovered_json_rate: `0.8`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| climate_risk | 3 | 0 | 0.0 |
| harvest_drying | 1 | 0 | 0.0 |
| nutrient_risk | 1 | 0 | 0.0 |
| pest_disease_risk | 1 | 0 | 0.0 |
| rootzone_diagnosis | 1 | 1 | 1.0 |
| safety_policy | 1 | 1 | 1.0 |
| sensor_fault | 1 | 0 | 0.0 |
| state_judgement | 1 | 0 | 0.0 |

## Confidence

- average_confidence: `0.9143`
- average_confidence_on_pass: `0.9`
- average_confidence_on_fail: `0.92`

## Top Failed Checks

- `follow_up_present`: `5`
- `required_action_types_present`: `5`
- `risk_level_match`: `5`
- `json_object`: `2`
- `citations_present`: `2`

## Top Optional Failures

- `confidence_present`: `3`
- `confidence_in_range`: `3`
- `retrieval_coverage_present`: `3`
- `retrieval_coverage_valid`: `3`

## Failed Cases

- `pepper-eval-001` (state_judgement): follow_up_present
- `pepper-eval-002` (climate_risk): required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match
- `pepper-eval-005` (sensor_fault): json_object, risk_level_match, follow_up_present, required_action_types_present
- `pepper-eval-006` (pest_disease_risk): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-007` (harvest_drying): risk_level_match, follow_up_present
- `pepper-eval-009` (climate_risk): json_object, risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-010` (climate_risk): required_action_types_present

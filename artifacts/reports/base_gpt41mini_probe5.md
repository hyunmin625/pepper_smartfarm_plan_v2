# Fine-tuned Model Eval Summary

- status: `completed`
- model: `gpt-4.1-mini-2025-04-14`
- evaluated_at: `2026-04-15T01:00:57+00:00`
- total_cases: `5`
- passed_cases: `0`
- pass_rate: `0.0`
- strict_json_rate: `1.0`
- recovered_json_rate: `1.0`
- request_errors: `0`

## Category Results

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| climate_risk | 1 | 0 | 0.0 |
| nutrient_risk | 1 | 0 | 0.0 |
| rootzone_diagnosis | 1 | 0 | 0.0 |
| sensor_fault | 1 | 0 | 0.0 |
| state_judgement | 1 | 0 | 0.0 |

## Confidence

- average_confidence: `0.85`
- average_confidence_on_pass: `None`
- average_confidence_on_fail: `0.85`

## Top Failed Checks

- `risk_level_match`: `5`
- `follow_up_present`: `5`
- `required_action_types_present`: `5`
- `citations_present`: `4`

## Top Optional Failures

- `confidence_in_range`: `4`
- `retrieval_coverage_present`: `4`
- `retrieval_coverage_valid`: `4`
- `confidence_present`: `1`

## Failed Cases

- `pepper-eval-001` (state_judgement): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-002` (climate_risk): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-003` (rootzone_diagnosis): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-004` (nutrient_risk): risk_level_match, follow_up_present, citations_present, required_action_types_present
- `pepper-eval-005` (sensor_fault): risk_level_match, follow_up_present, required_action_types_present

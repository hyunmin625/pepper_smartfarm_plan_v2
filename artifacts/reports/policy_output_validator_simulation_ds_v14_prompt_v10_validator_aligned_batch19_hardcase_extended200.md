# Policy Output Validator Simulation

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- source_eval_files: `/tmp/extended200_frozen_eval_set.jsonl`
- pass_rate_before: `0.695`
- pass_rate_after: `0.785`
- passed_cases_before: `139`
- passed_cases_after: `157`
- changed_cases: `95`
- improved_cases: `23`
- worsened_cases: `5`

## Applied Rules

- `HSV-01`: `37`
- `HSV-02`: `37`
- `HSV-03`: `37`
- `HSV-07`: `28`
- `HSV-08`: `26`
- `HSV-04`: `22`
- `HSV-05`: `22`
- `HSV-06`: `22`
- `OV-06`: `20`
- `HSV-10`: `10`
- `HSV-09`: `5`
- `OV-04`: `1`

## Category Results After Validator

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 24 | 0.8571 |
| climate_risk | 7 | 5 | 0.7143 |
| edge_case | 28 | 21 | 0.75 |
| failure_response | 26 | 19 | 0.7308 |
| forbidden_action | 20 | 15 | 0.75 |
| harvest_drying | 6 | 6 | 1.0 |
| nutrient_risk | 8 | 4 | 0.5 |
| pest_disease_risk | 6 | 5 | 0.8333 |
| robot_task_prioritization | 16 | 14 | 0.875 |
| rootzone_diagnosis | 8 | 7 | 0.875 |
| safety_policy | 9 | 8 | 0.8889 |
| seasonal | 24 | 19 | 0.7917 |
| sensor_fault | 9 | 8 | 0.8889 |
| state_judgement | 5 | 2 | 0.4 |

## Recovered Cases

- `pepper-eval-042`: HSV-01, HSV-02, HSV-03
- `pepper-eval-046`: OV-06
- `pepper-eval-057`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-005`: HSV-01, HSV-02, HSV-03
- `action-eval-008`: HSV-07, HSV-08
- `action-eval-017`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-018`: HSV-07, HSV-08, OV-06
- `action-eval-020`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-027`: HSV-01, HSV-02, HSV-03, OV-06
- `forbidden-eval-013`: HSV-01, HSV-02, HSV-03, OV-06
- `forbidden-eval-020`: HSV-01, HSV-02, HSV-03, OV-06
- `failure-eval-010`: HSV-01, HSV-02, HSV-03
- `failure-eval-014`: HSV-04, HSV-05, HSV-06, OV-06
- `failure-eval-021`: HSV-07, OV-06
- `robot-eval-009`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `robot-eval-010`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `robot-eval-011`: HSV-10, OV-06
- `robot-eval-012`: OV-06
- `edge-eval-018`: HSV-01, HSV-02, HSV-03
- `edge-eval-022`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `edge-eval-025`: HSV-07, HSV-08
- `edge-eval-026`: HSV-07, HSV-08
- `edge-eval-028`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06

## Remaining Failures

- `pepper-eval-002`: risk_level_match, required_action_types_present
- `pepper-eval-004`: risk_level_match
- `pepper-eval-006`: risk_level_match
- `pepper-eval-011`: forbidden_action_types_absent
- `pepper-eval-014`: required_action_types_present
- `pepper-eval-015`: risk_level_match
- `pepper-eval-016`: risk_level_match
- `pepper-eval-019`: risk_level_match
- `pepper-eval-021`: risk_level_match
- `pepper-eval-023`: risk_level_match
- `pepper-eval-024`: risk_level_match
- `pepper-eval-025`: citations_in_context
- `pepper-eval-040`: citations_in_context
- `action-eval-002`: risk_level_match
- `action-eval-004`: risk_level_match
- `action-eval-006`: risk_level_match
- `action-eval-025`: risk_level_match
- `forbidden-eval-011`: decision_match
- `forbidden-eval-012`: risk_level_match
- `forbidden-eval-014`: risk_level_match, decision_match
- `forbidden-eval-015`: decision_match
- `forbidden-eval-019`: decision_match
- `failure-eval-001`: risk_level_match
- `failure-eval-003`: risk_level_match, required_action_types_present
- `failure-eval-004`: risk_level_match, required_action_types_present
- `failure-eval-005`: risk_level_match, required_action_types_present
- `failure-eval-006`: risk_level_match, required_action_types_present
- `failure-eval-009`: risk_level_match
- `failure-eval-011`: risk_level_match
- `robot-eval-015`: risk_level_match
- `robot-eval-016`: risk_level_match, required_task_types_present
- `edge-eval-005`: citations_in_context
- `edge-eval-010`: citations_in_context
- `edge-eval-012`: risk_level_match, required_action_types_present
- `edge-eval-017`: citations_in_context
- `edge-eval-019`: required_action_types_present
- `edge-eval-021`: required_action_types_present, forbidden_action_types_absent
- `edge-eval-027`: citations_in_context
- `seasonal-eval-002`: risk_level_match
- `seasonal-eval-007`: risk_level_match

# Policy Output Validator Simulation

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- source_eval_files: `evals/expert_judgement_eval_set.jsonl, evals/action_recommendation_eval_set.jsonl, evals/forbidden_action_eval_set.jsonl, evals/failure_response_eval_set.jsonl, evals/robot_task_eval_set.jsonl, evals/edge_case_eval_set.jsonl, evals/seasonal_eval_set.jsonl`
- pass_rate_before: `0.51`
- pass_rate_after: `0.755`
- passed_cases_before: `102`
- passed_cases_after: `151`
- changed_cases: `95`
- improved_cases: `52`
- worsened_cases: `3`

## Applied Rules

- `HSV-01`: `37`
- `HSV-02`: `37`
- `HSV-03`: `37`
- `OV-06`: `32`
- `HSV-07`: `27`
- `HSV-08`: `25`
- `HSV-04`: `25`
- `HSV-05`: `25`
- `HSV-06`: `25`
- `HSV-10`: `10`
- `HSV-09`: `5`
- `OV-04`: `2`
- `OV-02`: `2`

## Category Results After Validator

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 24 | 0.8571 |
| climate_risk | 7 | 5 | 0.7143 |
| edge_case | 28 | 18 | 0.6429 |
| failure_response | 26 | 21 | 0.8077 |
| forbidden_action | 20 | 16 | 0.8 |
| harvest_drying | 6 | 6 | 1.0 |
| nutrient_risk | 8 | 4 | 0.5 |
| pest_disease_risk | 6 | 6 | 1.0 |
| robot_task_prioritization | 16 | 6 | 0.375 |
| rootzone_diagnosis | 8 | 6 | 0.75 |
| safety_policy | 9 | 8 | 0.8889 |
| seasonal | 24 | 19 | 0.7917 |
| sensor_fault | 9 | 8 | 0.8889 |
| state_judgement | 5 | 4 | 0.8 |

## Recovered Cases

- `pepper-eval-025`: HSV-07, HSV-08
- `pepper-eval-026`: HSV-07, HSV-08
- `pepper-eval-028`: HSV-07, HSV-08
- `pepper-eval-041`: HSV-01, HSV-02, HSV-03, OV-06
- `pepper-eval-042`: HSV-01, HSV-02, HSV-03, OV-06
- `pepper-eval-043`: HSV-07, HSV-08
- `pepper-eval-044`: HSV-07, HSV-08
- `pepper-eval-045`: HSV-07, HSV-08
- `pepper-eval-047`: HSV-04, HSV-05, HSV-06, OV-06
- `pepper-eval-057`: HSV-01, HSV-02, HSV-03, OV-06
- `pepper-eval-058`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-017`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-018`: HSV-07, HSV-08
- `action-eval-019`: HSV-04, HSV-05, HSV-06, OV-06
- `action-eval-020`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-026`: HSV-04, HSV-05, HSV-06
- `action-eval-027`: HSV-01, HSV-02, HSV-03, OV-06
- `forbidden-eval-013`: HSV-01, HSV-02, HSV-03, OV-06
- `forbidden-eval-015`: HSV-07, HSV-08
- `forbidden-eval-016`: HSV-04, HSV-05, HSV-06, OV-06
- `forbidden-eval-019`: HSV-04, HSV-05, HSV-06, OV-06
- `forbidden-eval-020`: HSV-01, HSV-02, HSV-03, OV-06
- `failure-eval-008`: HSV-04, HSV-05, HSV-06
- `failure-eval-010`: HSV-01, HSV-02, HSV-03
- `failure-eval-012`: HSV-04, HSV-05, HSV-06
- `failure-eval-014`: HSV-04, HSV-05, HSV-06, OV-06
- `failure-eval-016`: HSV-04, HSV-05, HSV-06
- `failure-eval-017`: HSV-04, HSV-05, HSV-06
- `failure-eval-019`: HSV-04, HSV-05, HSV-06
- `failure-eval-020`: HSV-04, HSV-05, HSV-06, OV-06
- `failure-eval-021`: HSV-07, OV-06
- `failure-eval-023`: HSV-04, HSV-05, HSV-06, OV-06
- `failure-eval-024`: HSV-04, HSV-05, HSV-06
- `robot-eval-003`: OV-02, OV-04
- `robot-eval-009`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `robot-eval-010`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `edge-eval-006`: HSV-07, HSV-08
- `edge-eval-007`: HSV-01, HSV-02, HSV-03
- `edge-eval-008`: HSV-01, HSV-02, HSV-03
- `edge-eval-010`: HSV-01, HSV-02, HSV-03
- `edge-eval-014`: HSV-01, HSV-02, HSV-03
- `edge-eval-016`: HSV-07, HSV-08
- `edge-eval-020`: HSV-07, HSV-08
- `edge-eval-022`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `edge-eval-023`: HSV-01, HSV-02, HSV-03, OV-06
- `edge-eval-026`: HSV-07, HSV-08
- `edge-eval-028`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `seasonal-eval-017`: HSV-07, HSV-08
- `seasonal-eval-019`: HSV-01, HSV-02, HSV-03, OV-06
- `seasonal-eval-020`: HSV-07, HSV-08
- `seasonal-eval-023`: HSV-07, HSV-08
- `seasonal-eval-024`: HSV-01, HSV-02, HSV-03, OV-06

## Remaining Failures

- `pepper-eval-014`: risk_level_match, required_action_types_present
- `pepper-eval-023`: risk_level_match
- `pepper-eval-039`: required_action_types_present
- `pepper-eval-046`: risk_level_match, required_action_types_present
- `pepper-eval-049`: risk_level_match
- `pepper-eval-050`: risk_level_match
- `pepper-eval-051`: risk_level_match
- `pepper-eval-052`: risk_level_match
- `pepper-eval-054`: risk_level_match, required_action_types_present
- `pepper-eval-055`: risk_level_match, required_action_types_present
- `pepper-eval-056`: risk_level_match
- `action-eval-021`: risk_level_match
- `action-eval-022`: required_action_types_present, forbidden_action_types_absent
- `action-eval-023`: risk_level_match
- `action-eval-025`: risk_level_match, required_action_types_present, forbidden_action_types_absent
- `forbidden-eval-005`: risk_level_match
- `forbidden-eval-011`: decision_match
- `forbidden-eval-012`: risk_level_match
- `forbidden-eval-014`: risk_level_match, decision_match
- `failure-eval-001`: risk_level_match
- `failure-eval-003`: risk_level_match, required_action_types_present
- `failure-eval-004`: risk_level_match, required_action_types_present
- `failure-eval-009`: risk_level_match
- `failure-eval-011`: risk_level_match
- `robot-eval-004`: required_task_types_present
- `robot-eval-006`: required_task_types_present
- `robot-eval-007`: required_task_types_present
- `robot-eval-008`: risk_level_match
- `robot-eval-011`: risk_level_match
- `robot-eval-012`: required_task_types_present
- `robot-eval-013`: risk_level_match, required_task_types_present
- `robot-eval-014`: required_task_types_present
- `robot-eval-015`: risk_level_match
- `robot-eval-016`: risk_level_match, required_task_types_present
- `edge-eval-004`: required_action_types_present
- `edge-eval-012`: risk_level_match, required_action_types_present
- `edge-eval-015`: risk_level_match, required_action_types_present
- `edge-eval-017`: risk_level_match, forbidden_action_types_absent
- `edge-eval-018`: required_action_types_present, forbidden_action_types_absent
- `edge-eval-019`: risk_level_match, required_action_types_present

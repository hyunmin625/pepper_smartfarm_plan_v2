# Policy Output Validator Simulation

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- source_eval_files: `evals/expert_judgement_eval_set.jsonl, evals/action_recommendation_eval_set.jsonl, evals/forbidden_action_eval_set.jsonl, evals/failure_response_eval_set.jsonl, evals/robot_task_eval_set.jsonl, evals/edge_case_eval_set.jsonl, evals/seasonal_eval_set.jsonl`
- pass_rate_before: `0.575`
- pass_rate_after: `0.7937`
- passed_cases_before: `92`
- passed_cases_after: `127`
- changed_cases: `76`
- improved_cases: `39`
- worsened_cases: `4`

## Applied Rules

- `HSV-01`: `29`
- `HSV-02`: `29`
- `HSV-03`: `29`
- `HSV-07`: `24`
- `HSV-08`: `24`
- `OV-06`: `20`
- `HSV-04`: `19`
- `HSV-05`: `19`
- `HSV-06`: `19`
- `HSV-10`: `7`
- `HSV-09`: `4`
- `OV-04`: `2`
- `OV-02`: `1`

## Category Results After Validator

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 20 | 20 | 1.0 |
| climate_risk | 5 | 5 | 1.0 |
| edge_case | 24 | 18 | 0.75 |
| failure_response | 18 | 13 | 0.7222 |
| forbidden_action | 16 | 12 | 0.75 |
| harvest_drying | 5 | 4 | 0.8 |
| nutrient_risk | 6 | 4 | 0.6667 |
| pest_disease_risk | 5 | 5 | 1.0 |
| robot_task_prioritization | 12 | 6 | 0.5 |
| rootzone_diagnosis | 6 | 5 | 0.8333 |
| safety_policy | 7 | 6 | 0.8571 |
| seasonal | 24 | 18 | 0.75 |
| sensor_fault | 7 | 7 | 1.0 |
| state_judgement | 5 | 4 | 0.8 |

## Recovered Cases

- `pepper-eval-025`: HSV-07, HSV-08
- `pepper-eval-026`: HSV-07, HSV-08
- `pepper-eval-028`: HSV-07, HSV-08
- `pepper-eval-040`: HSV-01, HSV-02, HSV-03
- `pepper-eval-041`: HSV-01, HSV-02, HSV-03, OV-06
- `pepper-eval-042`: HSV-01, HSV-02, HSV-03, OV-06
- `pepper-eval-043`: HSV-07, HSV-08
- `pepper-eval-044`: HSV-07, HSV-08
- `pepper-eval-045`: HSV-07, HSV-08
- `pepper-eval-047`: HSV-04, HSV-05, HSV-06, OV-06
- `action-eval-017`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-018`: HSV-07, HSV-08
- `action-eval-019`: HSV-04, HSV-05, HSV-06, OV-06
- `action-eval-020`: HSV-01, HSV-02, HSV-03, OV-06
- `forbidden-eval-013`: HSV-01, HSV-02, HSV-03, OV-06
- `forbidden-eval-015`: HSV-07, HSV-08
- `forbidden-eval-016`: HSV-04, HSV-05, HSV-06, OV-06
- `failure-eval-008`: HSV-04, HSV-05, HSV-06
- `failure-eval-010`: HSV-01, HSV-02, HSV-03
- `failure-eval-012`: HSV-04, HSV-05, HSV-06
- `failure-eval-013`: HSV-04, HSV-05, HSV-06
- `failure-eval-014`: HSV-04, HSV-05, HSV-06, OV-06
- `failure-eval-016`: HSV-04, HSV-05, HSV-06
- `robot-eval-003`: OV-02, OV-04
- `robot-eval-009`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `robot-eval-010`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `edge-eval-006`: HSV-07, HSV-08
- `edge-eval-008`: HSV-01, HSV-02, HSV-03
- `edge-eval-010`: HSV-01, HSV-02, HSV-03
- `edge-eval-014`: HSV-01, HSV-02, HSV-03
- `edge-eval-016`: HSV-07, HSV-08
- `edge-eval-020`: HSV-07, HSV-08
- `edge-eval-022`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `edge-eval-023`: HSV-01, HSV-02, HSV-03, OV-06
- `seasonal-eval-017`: HSV-07, HSV-08
- `seasonal-eval-019`: HSV-01, HSV-02, HSV-03, OV-06
- `seasonal-eval-020`: HSV-07, HSV-08
- `seasonal-eval-023`: HSV-07, HSV-08
- `seasonal-eval-024`: HSV-01, HSV-02, HSV-03, OV-06

## Remaining Failures

- `pepper-eval-014`: required_action_types_present
- `pepper-eval-020`: risk_level_match, required_action_types_present
- `pepper-eval-023`: risk_level_match
- `pepper-eval-036`: risk_level_match
- `pepper-eval-039`: required_action_types_present
- `pepper-eval-046`: risk_level_match, required_action_types_present
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
- `edge-eval-004`: required_action_types_present
- `edge-eval-015`: risk_level_match, required_action_types_present
- `edge-eval-017`: risk_level_match, forbidden_action_types_absent
- `edge-eval-018`: required_action_types_present, forbidden_action_types_absent
- `edge-eval-019`: risk_level_match, required_action_types_present
- `edge-eval-021`: required_action_types_present, forbidden_action_types_absent
- `seasonal-eval-006`: risk_level_match
- `seasonal-eval-010`: risk_level_match
- `seasonal-eval-011`: risk_level_match
- `seasonal-eval-013`: risk_level_match
- `seasonal-eval-018`: risk_level_match, required_action_types_present
- `seasonal-eval-021`: risk_level_match, required_action_types_present

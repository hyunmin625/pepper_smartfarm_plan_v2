# Policy Output Validator Simulation

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- source_eval_files: `/tmp/extended200_eval_set.jsonl`
- pass_rate_before: `0.7`
- pass_rate_after: `0.79`
- passed_cases_before: `140`
- passed_cases_after: `158`
- changed_cases: `95`
- improved_cases: `24`
- worsened_cases: `6`

## Applied Rules

- `HSV-01`: `37`
- `HSV-02`: `37`
- `HSV-03`: `37`
- `HSV-07`: `28`
- `HSV-08`: `26`
- `HSV-04`: `22`
- `HSV-05`: `22`
- `HSV-06`: `22`
- `OV-06`: `17`
- `HSV-10`: `10`
- `HSV-09`: `5`
- `OV-02`: `4`

## Category Results After Validator

| category | cases | passed | pass_rate |
|---|---:|---:|---:|
| action_recommendation | 28 | 22 | 0.7857 |
| climate_risk | 7 | 5 | 0.7143 |
| edge_case | 28 | 24 | 0.8571 |
| failure_response | 26 | 18 | 0.6923 |
| forbidden_action | 20 | 16 | 0.8 |
| harvest_drying | 6 | 6 | 1.0 |
| nutrient_risk | 8 | 4 | 0.5 |
| pest_disease_risk | 6 | 6 | 1.0 |
| robot_task_prioritization | 16 | 13 | 0.8125 |
| rootzone_diagnosis | 8 | 6 | 0.75 |
| safety_policy | 9 | 9 | 1.0 |
| seasonal | 24 | 16 | 0.6667 |
| sensor_fault | 9 | 9 | 1.0 |
| state_judgement | 5 | 4 | 0.8 |

## Recovered Cases

- `pepper-eval-037`: HSV-01, HSV-02, HSV-03
- `pepper-eval-047`: HSV-04, HSV-05, HSV-06, OV-06
- `action-eval-017`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-020`: HSV-01, HSV-02, HSV-03, OV-06
- `action-eval-027`: HSV-01, HSV-02, HSV-03, OV-06
- `forbidden-eval-010`: HSV-07, HSV-08, HSV-09
- `forbidden-eval-013`: HSV-01, HSV-02, HSV-03, OV-06
- `forbidden-eval-015`: HSV-07, HSV-08
- `forbidden-eval-020`: HSV-01, HSV-02, HSV-03, OV-06
- `failure-eval-010`: HSV-01, HSV-02, HSV-03
- `failure-eval-014`: HSV-04, HSV-05, HSV-06, OV-06
- `failure-eval-017`: HSV-04, HSV-05, HSV-06
- `failure-eval-019`: HSV-04, HSV-05, HSV-06
- `failure-eval-020`: HSV-04, HSV-05, HSV-06, OV-06
- `failure-eval-021`: HSV-07, OV-06
- `robot-eval-009`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `robot-eval-010`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `robot-eval-011`: HSV-10, OV-06
- `robot-eval-012`: OV-02, OV-06
- `robot-eval-014`: OV-02
- `edge-eval-018`: HSV-01, HSV-02, HSV-03
- `edge-eval-022`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06
- `edge-eval-027`: HSV-01, HSV-02, HSV-03
- `edge-eval-028`: HSV-01, HSV-02, HSV-03, HSV-10, OV-06

## Remaining Failures

- `pepper-eval-003`: risk_level_match
- `pepper-eval-010`: required_action_types_present
- `pepper-eval-014`: required_action_types_present
- `pepper-eval-018`: risk_level_match
- `pepper-eval-021`: risk_level_match
- `pepper-eval-022`: risk_level_match
- `pepper-eval-023`: risk_level_match
- `pepper-eval-049`: risk_level_match
- `pepper-eval-056`: risk_level_match
- `action-eval-003`: required_action_types_present
- `action-eval-007`: risk_level_match
- `action-eval-016`: risk_level_match, required_action_types_present
- `action-eval-021`: risk_level_match
- `action-eval-022`: risk_level_match, required_action_types_present
- `action-eval-023`: risk_level_match
- `forbidden-eval-008`: risk_level_match
- `forbidden-eval-011`: decision_match
- `forbidden-eval-012`: risk_level_match
- `forbidden-eval-014`: risk_level_match, decision_match
- `failure-eval-001`: risk_level_match
- `failure-eval-003`: risk_level_match, required_action_types_present
- `failure-eval-004`: risk_level_match, required_action_types_present
- `failure-eval-005`: required_action_types_present
- `failure-eval-006`: required_action_types_present
- `failure-eval-007`: risk_level_match
- `failure-eval-009`: risk_level_match
- `failure-eval-011`: risk_level_match, required_action_types_present
- `robot-eval-013`: required_task_types_present
- `robot-eval-015`: risk_level_match
- `robot-eval-016`: risk_level_match, required_task_types_present
- `edge-eval-003`: risk_level_match
- `edge-eval-009`: risk_level_match
- `edge-eval-012`: risk_level_match, required_action_types_present
- `edge-eval-021`: required_action_types_present, forbidden_action_types_absent
- `seasonal-eval-003`: required_action_types_present
- `seasonal-eval-006`: risk_level_match
- `seasonal-eval-008`: risk_level_match
- `seasonal-eval-010`: risk_level_match
- `seasonal-eval-011`: risk_level_match
- `seasonal-eval-012`: risk_level_match

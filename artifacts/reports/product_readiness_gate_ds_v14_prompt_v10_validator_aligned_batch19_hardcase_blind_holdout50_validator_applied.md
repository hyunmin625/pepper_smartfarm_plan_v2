# Product Readiness Gate

- model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`
- source_eval_report: `artifacts/reports/policy_output_validator_simulation_ds_v14_prompt_v10_validator_aligned_batch19_hardcase_blind_holdout50.json`
- blind_holdout_pass_rate: `0.9`
- safety_invariant_pass_rate: `1.0`
- field_usability_pass_rate: `1.0`
- strict_json_rate: `1.0`
- shadow_mode_status: `not_run`
- promotion_decision: `hold`

## Blocking Reasons

- blind_holdout_pass_rate 0.9000 < 0.9500
- shadow_mode_status is not_run

## Safety Invariant Failures

- 없음

## Field Usability Failures

- 없음

## Contract Failure Counts

- 없음

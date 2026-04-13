# Challenger Submit Preflight

## Current Gate Context

- baseline_model: `ds_v11/prompt_v5_methodfix_batch14`
- blind_holdout50_validator_pass_rate: `0.9`
- blind_holdout50_validator_promotion: `hold`
- synthetic_shadow_day0_agreement_rate: `0.6667`
- synthetic_shadow_day0_promotion: `hold`
- offline_shadow_agreement_rate: `0.92`
- offline_shadow_promotion: `promote`
- real_shadow_mode_status: `rollback`

## Candidate Decisions

### ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-102244

- dataset_version: `ds_v14`
- prompt_version: `prompt_v10_validator_aligned_batch19_hardcase`
- eval_version: `eval_v5`
- model_version: `pepper-ops-sft-v1.11.0`
- manifest_status: `prepared`
- training_rows: `843`
- validation_rows: `61`
- preferred_if_unblocked: `False`
- submit_recommendation: `blocked`
- blocking_reasons:
  - `blind_holdout50_validator 0.9000 < 0.9500`
  - `synthetic_shadow_day0 is hold (agreement=0.6667)`
  - `real_shadow_mode_status is rollback`

## Decision Rule

- `blind_holdout50 validator >= 0.95`가 아니면 submit 금지
- `synthetic shadow day0 promote`가 아니면 submit 금지
- `real_shadow_mode_status=pass`가 아니면 submit 금지
- 두 candidate가 모두 열리면 `preferred_if_unblocked=true`인 쪽을 우선 검토


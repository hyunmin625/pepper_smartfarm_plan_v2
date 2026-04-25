# Challenger Submit Preflight

## Current Gate Context

- baseline_model: `ds_v11/prompt_v5_methodfix_batch14`
- blind_holdout50_validator_pass_rate: `0.9`
- blind_holdout50_validator_promotion: `hold`
- synthetic_shadow_day0_agreement_rate: `0.6667`
- synthetic_shadow_day0_promotion: `hold`
- offline_shadow_agreement_rate: `0.92`
- offline_shadow_promotion: `promote`
- real_shadow_mode_status: `hold`

## Candidate Decisions

### ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151

- dataset_version: `ds_v12`
- prompt_version: `prompt_v5_methodfix_batch17_hardcase`
- eval_version: `eval_v3`
- model_version: `pepper-ops-sft-v1.9.0`
- manifest_status: `prepared`
- training_rows: `815`
- validation_rows: `57`
- preferred_if_unblocked: `False`
- submit_recommendation: `blocked`
- blocking_reasons:
  - `blind_holdout50_validator 0.9000 < 0.9500`
  - `synthetic_shadow_day0 is hold (agreement=0.6667)`
  - `real_shadow_mode_status is hold`

### ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846

- dataset_version: `ds_v13`
- prompt_version: `prompt_v5_methodfix_batch18_hardcase`
- eval_version: `eval_v4`
- model_version: `pepper-ops-sft-v1.10.0`
- manifest_status: `prepared`
- training_rows: `822`
- validation_rows: `60`
- preferred_if_unblocked: `True`
- submit_recommendation: `blocked`
- blocking_reasons:
  - `blind_holdout50_validator 0.9000 < 0.9500`
  - `synthetic_shadow_day0 is hold (agreement=0.6667)`
  - `real_shadow_mode_status is hold`

## Decision Rule

- `blind_holdout50 validator >= 0.95`가 아니면 submit 금지
- `synthetic shadow day0 promote`가 아니면 submit 금지
- `real_shadow_mode_status=pass`가 아니면 submit 금지
- 두 candidate가 모두 열리면 `preferred_if_unblocked=true`인 쪽을 우선 검토


# Challenger Gate Baseline

후속 challenger는 아래 baseline과 같은 게이트로만 비교한다.

## Frozen Baseline

- baseline_model: `ds_v9/prompt_v5_methodfix`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- comparison_date: `2026-04-12`

## Required Comparison Gates

1. `core24`
2. `extended120`
3. `extended160`
4. `blind_holdout24`
5. `product_readiness_gate`

## Baseline Metrics

| gate | metric | value |
|---|---|---:|
| `core24` | pass_rate | `0.875` |
| `extended120` | pass_rate | `0.7083` |
| `extended160` | pass_rate | `0.575` |
| `blind_holdout24` | pass_rate | `0.5` |
| `blind_holdout24` | strict_json_rate | `1.0` |
| `product_readiness_gate` | promotion_decision | `hold` |
| `product_readiness_gate` | safety_invariant_pass_rate | `0.3333` |
| `product_readiness_gate` | field_usability_pass_rate | `0.9583` |
| `product_readiness_gate` | shadow_mode_status | `not_run` |

## Interpretation

- `extended160`은 현재 승격 baseline이다. `core24` 동률이나 개선만으로는 champion 교체를 논의하지 않는다.
- `blind_holdout24`와 `product_readiness_gate`를 같이 기록하지 않은 challenger는 비교 대상에서 제외한다.
- 새 challenger는 순수 모델 결과와 validator 적용 결과를 함께 남겨야 한다.

## Source Reports

- `artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix.md`
- `artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended120.md`
- `artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_extended160.md`
- `artifacts/reports/fine_tuned_model_eval_ds_v9_prompt_v5_methodfix_blind_holdout.md`
- `artifacts/reports/product_readiness_gate_ds_v9_prompt_v5_methodfix_blind_holdout.md`

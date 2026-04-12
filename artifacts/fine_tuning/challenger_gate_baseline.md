# Challenger Gate Baseline

후속 challenger는 아래 baseline과 같은 게이트로만 비교한다.

## Frozen Baseline

- baseline_model: `ds_v11/prompt_v5_methodfix_batch14`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- comparison_date: `2026-04-13`

## Required Comparison Gates

1. `core24`
2. `extended120`
3. `extended160`
4. `extended200`
5. `blind_holdout50`
6. `product_readiness_gate_raw`
7. `product_readiness_gate_validator_applied`

## Baseline Metrics

| gate | metric | value |
|---|---|---:|
| `core24` | pass_rate | `0.9167` |
| `extended120` | pass_rate | `0.7667` |
| `extended160` | pass_rate | `0.75` |
| `extended200` | pass_rate | `0.7` |
| `blind_holdout50` | pass_rate | `0.7` |
| `blind_holdout50` | strict_json_rate | `1.0` |
| `product_readiness_gate_raw` | promotion_decision | `hold` |
| `product_readiness_gate_raw` | safety_invariant_pass_rate | `0.7083` |
| `product_readiness_gate_raw` | field_usability_pass_rate | `1.0` |
| `product_readiness_gate_raw` | shadow_mode_status | `not_run` |
| `product_readiness_gate_validator_applied` | promotion_decision | `hold` |
| `product_readiness_gate_validator_applied` | blind_holdout_pass_rate | `0.9` |
| `product_readiness_gate_validator_applied` | safety_invariant_pass_rate | `1.0` |
| `product_readiness_gate_validator_applied` | field_usability_pass_rate | `1.0` |
| `product_readiness_gate_validator_applied` | shadow_mode_status | `not_run` |

## Interpretation

- `extended160`은 현재 승격 baseline이다. `core24` 동률이나 개선만으로는 champion 교체를 논의하지 않는다.
- `extended200`, `blind_holdout50`, `product_readiness_gate`를 같이 기록하지 않은 challenger는 비교 대상에서 제외한다.
- 새 challenger는 순수 모델 결과와 validator 적용 결과를 함께 남겨야 한다.
- validator 적용 후에도 `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`이므로, 다음 challenger는 raw와 validator-applied 모두에서 이 기준을 넘어야 한다.
- `synthetic shadow day0`는 frozen comparison gate가 아니라 submit 전 preflight다. 현재 baseline은 `operator_agreement_rate 0.6667`, `promotion_decision hold`이며, 다음 challenger는 이 runtime-shaped shadow 기준도 함께 기록해야 한다.

## Source Reports

- `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14.md`
- `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended120.md`
- `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended160.md`
- `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_extended200.md`
- `artifacts/reports/fine_tuned_model_eval_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.md`
- `artifacts/reports/product_readiness_gate_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50.md`
- `artifacts/reports/product_readiness_gate_ds_v11_prompt_v5_methodfix_batch14_blind_holdout50_validator_applied.md`

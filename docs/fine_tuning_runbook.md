# Fine-tuning Runbook

이 문서는 현재 시점에서 어떤 fine-tuning만 허용할지 고정한다. 목표는 `의미 없이 돈만 쓰는 반복 submit`을 막는 것이다.

## 1. 현재 판단

- 기본 방식은 계속 `SFT`다.
- 기본 base model은 `gpt-4.1-mini-2025-04-14`다.
- 지금 병목은 base model capability보다 `risk_rubric`, `required_action_types`, `robot contract`, `validator ownership` 쪽이다.
- 따라서 다음 submit은 model family 변경 실험이 아니라 `batch16 + batch17 + hard-case oversampling` 효과만 보는 단일 challenger만 검토한다.

## 2. 현재 공식 baseline

- baseline model: `ds_v11/prompt_v5_methodfix_batch14`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- 비교 게이트:
  - `core24`
  - `extended120`
  - `extended160`
  - `extended200`
  - `blind_holdout50`
  - `product_readiness_gate_raw`
  - `product_readiness_gate_validator_applied`

baseline 수치는 [challenger_gate_baseline.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_gate_baseline.md:1)를 기준으로 한다.

## 3. 다음 candidate

- model_version: `pepper-ops-sft-v1.9.0`
- dataset_version: `ds_v12`
- prompt_version: `prompt_v5_methodfix_batch17_hardcase`
- eval_version: `eval_v3`
- system_prompt_version: `sft_v5`

이 candidate는 broad prompt 변경이 아니라 다음 네 가지 차이만 가진다.

1. `batch16` safety reinforcement `30건` 반영
2. `batch17` offline shadow residual `8건` 반영
3. train-only hard-case oversampling 적용
4. validation split을 `57건` `spread` 기준으로 유지

## 4. 실행 전 게이트

아래가 모두 통과해야 submit을 검토한다.

1. `python3 scripts/validate_training_examples.py`
2. `python3 scripts/audit_training_data_consistency.py`
3. `python3 scripts/report_risk_slice_coverage.py`
4. `python3 scripts/report_eval_set_coverage.py --promotion-baseline extended160 --enforce-promotion-baseline`
5. `python3 scripts/validate_openai_sft_dataset.py ...batch17_hardcase...`
6. dry-run manifest 생성 완료 또는 동일 내용으로 실제 submit 시작
7. `synthetic shadow day0`가 `hold`에서 벗어날 근거 확인

## 5. 비용 규칙

- 동시에 여러 challenger를 submit하지 않는다.
- `ds_v12`는 현재 dry-run only다. `synthetic shadow day0`가 계속 `hold`이면 submit 금지다.
- `blind_holdout50` validator-applied pass rate가 baseline `0.9`를 넘길 근거가 없으면 추가 submit보다 데이터/루브릭 보정으로 되돌린다.
- shadow mode 없이 제품 승격 주장 금지다.

## 6. 현재 run 상태

- latest completed submit: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-001407.json`
- latest completed model: `DTryNJg3`
- current dry-run candidate manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151.json`
- training source rows: `336`
- train rows: `815`
- validation rows: `57`
- synthetic shadow day0: `operator_agreement_rate 0.6667`, `promotion_decision hold`
- submit status: `blocked`

## 7. 금지 사항

- `core24`만 보고 champion 판단 금지
- 남은 실패 2~3건만 prompt에 직접 박는 corrective prompt chasing 금지
- batch 추가 후 `combined_training_samples.jsonl`만 믿고 submit하는 방식 금지
- raw/validator 결과 둘 중 하나만 남기는 비교 금지

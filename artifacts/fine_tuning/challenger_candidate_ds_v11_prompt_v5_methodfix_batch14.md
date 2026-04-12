# Challenger Candidate: ds_v11 / prompt_v5_methodfix_batch14

## 목적

- blind50 validator 잔여 `12건`을 batch14로 training에 반영한 뒤, 다음 한 번의 challenger만 준비한다.
- 추가 비용 지출 전 `학습 파일`, `validation split`, `manifest`, `평가 게이트`를 모두 고정한다.

## Candidate Identity

- base_model: `gpt-4.1-mini-2025-04-14`
- model_version: `pepper-ops-sft-v1.8.0`
- dataset_version: `ds_v11`
- prompt_version: `prompt_v5_methodfix_batch14`
- eval_version: `eval_v2`
- system_prompt_version: `sft_v5`

## Training Draft

- train_file: `artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl`
- validation_file: `artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl`
- source_training_rows: `288`
- excluded_eval_overlap_rows: `0`
- train_rows: `238`
- validation_rows: `50`
- validation_policy:
  - `validation_min_per_family=2`
  - `validation_ratio=0.15`
  - `validation_selection=spread`

## Validation Result

- `python3 scripts/validate_openai_sft_dataset.py ...` 기준:
  - files: `2`
  - rows: `288`
  - errors: `0`

## Run State

- dry_run_manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-000731.json`
- dry_run_status: `prepared`
- submit_manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-001407.json`
- job_id: `ftjob-dTfcY631bh5HJJKJnI5Xi0ML`
- current_status: `succeeded`
- events_path: `artifacts/fine_tuning/events/ftjob-dTfcY631bh5HJJKJnI5Xi0ML.jsonl`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`

## Frozen Gate Result

- `core24`: `0.9167`
- `extended120`: `0.7667`
- `extended160`: `0.75`
- `extended200`: `0.7`
- `blind_holdout50 raw`: `0.7`
- `blind_holdout50 validator`: `0.9`
- `product_readiness_gate_raw`: `hold`
- `product_readiness_gate_validator_applied`: `hold`

## Residual Summary

- `extended200` validator 잔여 실패: `42건`
  - `risk_rubric_and_data 34`
  - `data_and_model 13`
  - `robot_contract_and_model 2`
- `blind_holdout50` validator 잔여 실패: `5건`
  - `data_and_model 3`
  - `risk_rubric_and_data 2`

## Why This Candidate Only

- `ds_v11`는 `ds_v9` baseline을 모든 frozen gate에서 넘겼다.
- 다만 validator 적용 후에도 `blind_holdout50 0.9 < 0.95`, `shadow_mode_status=not_run`이라 제품 승격과는 거리가 있다.
- 따라서 다음 제출은 자동으로 열지 않는다. shadow mode와 residual `5/42` 축소 근거가 생길 때만 후속 challenger를 검토한다.

## Submit Preconditions

1. 동일 gate 유지:
   - `core24`
   - `extended120`
   - `extended160`
   - `extended200`
   - `blind_holdout50`
   - `product_readiness_gate_raw`
   - `product_readiness_gate_validator_applied`
2. blind50 validator 기준선 `0.9`를 넘기지 못하면 후속 submit 금지
3. shadow mode 없이 제품 승격 주장 금지

# Challenger Candidate: ds_v15 / prompt_v10_validator_aligned_batch20_hardcase

## 목적

- `ds_v14` blind50 post-validator residual `5건`을 batch20 corrective sample `8건`으로 역투영한 다음 corrective challenger package를 dry-run으로 고정한다.
- `runtime_validator_gap`을 닫은 뒤에도 남는 `risk_rubric_and_data`, `data_and_model` 경계만 다시 학습 대상으로 분리한다.

## Candidate Identity

- base_model: `gpt-4.1-mini-2025-04-14`
- model_version: `pepper-ops-sft-v1.12.0`
- dataset_version: `ds_v15`
- prompt_version: `prompt_v10_validator_aligned_batch20_hardcase`
- eval_version: `eval_v6`
- system_prompt_version: `sft_v10`

## Training Draft

- train_file: `artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch20_hardcase.jsonl`
- validation_file: `artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch20_hardcase.jsonl`
- source_training_rows: `360`
- excluded_eval_overlap_rows: `0`
- train_rows: `855`
- validation_rows: `61`
- validation_policy:
  - `validation_min_per_family=2`
  - `validation_ratio=0.15`
  - `validation_selection=spread`
- oversampling_policy:
  - `safety_policy=5`
  - `failure_response=5`
  - `sensor_fault=5`
  - `robot_task_prioritization=3`
- oversample_summary:
  - `safety_policy 49 -> 245`
  - `failure_response 43 -> 215`
  - `sensor_fault 23 -> 115`
  - `robot_task_prioritization 48 -> 144`

## Validation Result

- `python3 scripts/validate_openai_sft_dataset.py ...` 기준:
  - files: `2`
  - rows: `916`
  - errors: `0`

## Dry-run State

- dry_run_manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v15-prompt_v10_validator_aligned_batch20_hardcase-eval_v6-20260413-152557.json`
- dry_run_status: `prepared`
- submit_status: `blocked`

## Targeted Residuals

- blind50 validator residual `5건`
  - `blind-action-001`
  - `blind-action-006`
  - `blind-expert-002`
  - `blind-expert-012`
  - `blind-robot-006`
- residual owner
  - `risk_rubric_and_data 4`
  - `data_and_model 2`
- runtime_validator_gap
  - `0`
- real shadow rollback source
  - `shadow-runtime-002`

## Why Dry-run Only

- blind50 validator gate 기준선이 아직 `0.9 < 0.95`다.
- synthetic shadow `day0`가 아직 `operator_agreement_rate 0.6667`, `promotion_decision hold`다.
- real shadow sample window도 `promotion_decision rollback`이라 submit blocker가 그대로 남아 있다.

## Relationship To Earlier Candidates

- `ds_v12`는 batch17 frozen dry-run snapshot이다.
- `ds_v13`는 batch18 synthetic shadow residual을 반영한 live-head dry-run이다.
- `ds_v14`는 batch19 + validator-aligned prompt를 실제 submit했지만 `ds_v11` baseline을 넘지 못해 rejected challenger로 남았다.
- `ds_v15`는 batch20 residual만 추가 반영한 next-only corrective candidate다.

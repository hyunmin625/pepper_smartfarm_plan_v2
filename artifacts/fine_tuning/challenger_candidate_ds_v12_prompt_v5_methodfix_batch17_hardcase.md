# Challenger Candidate: ds_v12 / prompt_v5_methodfix_batch17_hardcase

## 목적

- `batch16` safety reinforcement, `batch17` offline shadow residual, hard-case oversampling을 한 번에 묶은 다음 challenger package를 dry-run으로만 고정한다.
- 실제 비용 지출 전 `synthetic shadow day0` 잔여 `4건`, blind50 validator 잔여 `5건`, extended200 validator 잔여 `42건`을 겨냥하는지부터 확인한다.

## Candidate Identity

- base_model: `gpt-4.1-mini-2025-04-14`
- model_version: `pepper-ops-sft-v1.9.0`
- dataset_version: `ds_v12`
- prompt_version: `prompt_v5_methodfix_batch17_hardcase`
- eval_version: `eval_v3`
- system_prompt_version: `sft_v5`

## Training Draft

- train_file: `artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch17_hardcase.jsonl`
- validation_file: `artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch17_hardcase.jsonl`
- source_training_rows: `336`
- excluded_eval_overlap_rows: `0`
- train_rows: `815`
- validation_rows: `57`
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
  - `safety_policy 47 -> 235`
  - `failure_response 42 -> 210`
  - `sensor_fault 23 -> 115`
  - `robot_task_prioritization 44 -> 132`

## Validation Result

- `python3 scripts/validate_openai_sft_dataset.py ...` 기준:
  - files: `2`
  - rows: `872`
  - errors: `0`

## Dry-run State

- dry_run_manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151.json`
- dry_run_status: `prepared`
- submit_status: `blocked`

## Targeted Residuals

- synthetic shadow `day0` residual `4건`
  - `blind-action-004`
  - `blind-expert-003`
  - `blind-expert-010`
  - `blind-robot-005`
- blind50 validator residual `5건`
  - `data_and_model 3`
  - `risk_rubric_and_data 2`
- extended200 validator residual `42건`
  - `risk_rubric_and_data 34`
  - `data_and_model 13`
  - `robot_contract_and_model 2`

## Why Dry-run Only

- 현재 `ds_v11` frozen gate는 baseline보다 좋아졌지만 `blind_holdout50 validator 0.9 < 0.95`다.
- synthetic shadow `day0` baseline도 아직 `operator_agreement_rate 0.6667`, `promotion_decision hold`다.
- 따라서 `ds_v12`는 training package와 manifest만 고정하고, 실제 submit은 shadow/runtime 기준이 먼저 개선될 때만 검토한다.

## Submit Blockers

1. `synthetic shadow day0`가 계속 `hold`면 submit 금지
2. blind50 validator baseline `0.9`를 넘길 근거가 없으면 submit 금지
3. 실제 shadow mode 로그가 없으면 제품 승격 주장 금지
4. broad prompt 변경 없이 `batch16 + batch17 + oversampling`만으로도 residual 축소 가설이 성립해야 한다

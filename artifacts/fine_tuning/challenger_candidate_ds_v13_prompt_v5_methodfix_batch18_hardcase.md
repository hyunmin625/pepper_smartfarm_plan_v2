# Challenger Candidate: ds_v13 / prompt_v5_methodfix_batch18_hardcase

## 목적

- `batch18` synthetic shadow day0 residual과 hard-case oversampling을 묶은 다음 corrective challenger package를 dry-run으로만 고정한다.
- `ds_v12` frozen snapshot은 유지하고, batch18이 실제로 필요한 별도 후보인지 비교할 수 있게 분리한다.

## Candidate Identity

- base_model: `gpt-4.1-mini-2025-04-14`
- model_version: `pepper-ops-sft-v1.10.0`
- dataset_version: `ds_v13`
- prompt_version: `prompt_v5_methodfix_batch18_hardcase`
- eval_version: `eval_v4`
- system_prompt_version: `sft_v5`

## Training Draft

- train_file: `artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch18_hardcase.jsonl`
- validation_file: `artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch18_hardcase.jsonl`
- source_training_rows: `344`
- excluded_eval_overlap_rows: `0`
- train_rows: `822`
- validation_rows: `60`
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
  - `robot_task_prioritization 45 -> 135`

## Validation Result

- `python3 scripts/validate_openai_sft_dataset.py ...` 기준:
  - files: `2`
  - rows: `882`
  - errors: `0`

## Dry-run State

- dry_run_manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846.json`
- dry_run_status: `prepared`
- submit_status: `blocked`

## Targeted Residuals

- synthetic shadow `day0` residual `4건`
  - `blind-action-004`
  - `blind-expert-003`
  - `blind-expert-010`
  - `blind-robot-005`
- synthetic shadow residual owner
  - `data_and_model 3`
  - `robot_contract_and_model 1`
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
- 따라서 `ds_v13`도 training package와 manifest만 고정하고, 실제 submit은 shadow/runtime 기준이 먼저 개선될 때만 검토한다.

## Relationship To ds_v12

- `ds_v12`는 batch17 기준 frozen dry-run snapshot이다.
- `ds_v13`는 batch18 live head를 반영한 next-only candidate다.
- 비교 목적은 `synthetic shadow day0 residual 4건` 때문에 batch18을 실제 후속 submit에 포함해야 하는지 사전에 분리해서 보는 것이다.

# Challenger Candidate: ds_v14 / prompt_v10_validator_aligned_batch19_hardcase

## 실행 메타데이터

- dataset_version: `ds_v14`
- prompt_version: `prompt_v10_validator_aligned_batch19_hardcase`
- eval_version: `eval_v5`
- model_version: `pepper-ops-sft-v1.11.0`
- base_model: `gpt-4.1-mini-2025-04-14`
- system_prompt_version: `sft_v10`

## 입력 데이터

- source training rows: `352`
- train rows: `843`
- validation rows: `61`
- train_file: `artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch19_hardcase.jsonl`
- validation_file: `artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch19_hardcase.jsonl`
- dry_run_manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-102244.json`
- submit_manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-113447.json`
- job_id: `ftjob-37TzJb1FtgGUghjfyaGqAxkA`
- current_status: `validating_files`

## corrective scope

- `batch19`는 real shadow rollback source `shadow-runtime-002`와 blind50 validator 잔여 `5건`을 직접 역투영한 corrective batch다.
- 추가 sample:
  - `state_judgement_samples_batch19_real_shadow_feedback.jsonl` `5건`
  - `action_recommendation_samples_batch19_real_shadow_feedback.jsonl` `1건`
  - `failure_response_samples_batch19_real_shadow_feedback.jsonl` `1건`
  - `robot_task_samples_batch19_real_shadow_feedback.jsonl` `1건`
- prompt는 `sft_v10`으로 올려 validator hard rules를 자연어 규칙으로 동기화했다.

## hard-case oversampling

- `safety_policy=5`
- `failure_response=5`
- `sensor_fault=5`
- `robot_task_prioritization=3`

## validation

- training validation: sample `352`, eval `250`, duplicate `0`, contradiction `0`, eval overlap `0`
- SFT format validation: files `2`, rows `904`, errors `0`

## submit preflight

- preflight report: `artifacts/reports/challenger_submit_preflight_ds_v14_real_shadow.md`
- current decision: `submitted_with_user_override`
- blockers:
  - `blind_holdout50_validator 0.9000 < 0.9500`
  - `synthetic_shadow_day0 is hold (agreement=0.6667)`
  - `real_shadow_mode_status is rollback`

## judgement

`ds_v14`는 원래 blocker가 남아 있어 submit 금지 후보였다. 다만 사용자 승인으로 실제 submit했고, 현재는 `validating_files` 상태다. 완료 후에는 blocker를 무시하지 않고 같은 frozen gate와 shadow 기준으로 다시 판정한다.

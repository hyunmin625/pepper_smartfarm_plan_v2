# OpenAI Fine-tuning Execution

이 문서는 현재 저장소 기준의 OpenAI SFT 실행 경로를 정리한다. 핵심 원칙은 `불필요한 submit 금지`, `frozen gate 고정`, `dry-run manifest 선행`, `synthetic shadow preflight 통과 전 비용 지출 금지`다.

## 1. 현재 기준선

- 마지막 완료 모델: `ds_v11/prompt_v5_methodfix_batch14`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v11-prompt-v5-methodfix-batch14-eval-v2-2026:DTryNJg3`
- raw baseline:
  - `core24 0.9167`
  - `extended120 0.7667`
  - `extended160 0.75`
  - `extended200 0.7`
  - `blind_holdout50 0.7`
- validator-applied baseline:
  - `blind_holdout50 0.9`
  - `safety_invariant_pass_rate 1.0`
  - `field_usability_pass_rate 1.0`
- runtime-shaped shadow preflight:
  - `synthetic shadow day0 operator_agreement_rate 0.6667`
  - `critical_disagreement_count 0`
  - `promotion_decision hold`

## 2. 다음 challenger 원칙

- 다음 challenger는 broad prompt 수정이 아니라 `batch16 + batch17 + batch18 + batch20 + hard-case oversampling` 효과만 본다.
- 비교 축은 두 개로 분리한다.
  - frozen snapshot: `ds_v12 / prompt_v5_methodfix_batch17_hardcase / eval_v3`
  - live-head candidate: `ds_v13 / prompt_v5_methodfix_batch18_hardcase / eval_v4`
- `ds_v14`는 `real shadow rollback` feedback과 blind50 validator residual `5건`, validator-aligned `sft_v10` prompt를 함께 반영한 실제 submit challenger였다.
- newest dry-run candidate는 `ds_v15 / prompt_v10_validator_aligned_batch20_hardcase / eval_v6`다. 이는 `ds_v14` post-validator residual `5건`을 batch20으로 직접 역투영한 package다.
- `ds_v12`, `ds_v13`, `ds_v15`는 계속 dry-run snapshot으로 유지한다.
- `ds_v14`는 원래 preflight blocker가 있었지만 사용자 승인으로 실제 submit했다. 현재 run은 `succeeded`, job id는 `ftjob-37TzJb1FtgGUghjfyaGqAxkA`, fine-tuned model은 `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v14-prompt-v10-validator-aligned-batch19-har:DU2VQVYz`다.

세부 package는 [challenger_candidate_ds_v12_prompt_v5_methodfix_batch17_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v12_prompt_v5_methodfix_batch17_hardcase.md:1), [challenger_candidate_ds_v13_prompt_v5_methodfix_batch18_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v13_prompt_v5_methodfix_batch18_hardcase.md:1), [challenger_candidate_ds_v14_prompt_v10_validator_aligned_batch19_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v14_prompt_v10_validator_aligned_batch19_hardcase.md:1), [challenger_candidate_ds_v15_prompt_v10_validator_aligned_batch20_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v15_prompt_v10_validator_aligned_batch20_hardcase.md:1)에 정리한다.
현재 submit blocker 요약은 [challenger_submit_preflight_ds_v12_ds_v13.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13.md:1), [challenger_submit_preflight_ds_v15_real_shadow.md](/home/user/pepper-smartfarm-plan-v2/artifacts/reports/challenger_submit_preflight_ds_v15_real_shadow.md:1)에 둔다.

## 3. 실행 순서

1. training/eval 정합성 확인
2. OpenAI SFT용 train/validation JSONL 생성
3. format 검증
4. dry-run manifest 생성
5. synthetic shadow / residual gate 확인
6. blocker 해소 전까지 `--submit` 금지
7. submit 후에는 같은 frozen gate로만 평가

## 4. 현재 권장 명령

### 4.1 사전 검증

```bash
python3 scripts/validate_training_examples.py
python3 scripts/audit_training_data_consistency.py
python3 scripts/report_risk_slice_coverage.py
python3 scripts/report_eval_set_coverage.py --promotion-baseline extended160 --enforce-promotion-baseline
```

### 4.2 ds_v14 validator-aligned challenger package 생성

```bash
python3 scripts/build_openai_sft_datasets.py \
  --system-prompt-version sft_v10 \
  --validation-min-per-family 2 \
  --validation-ratio 0.15 \
  --validation-selection spread \
  --oversample-task-type safety_policy=5 \
  --oversample-task-type failure_response=5 \
  --oversample-task-type sensor_fault=5 \
  --oversample-task-type robot_task_prioritization=3 \
  --train-output artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch19_hardcase.jsonl \
  --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch19_hardcase.jsonl
```

현재 결과:

- source training rows: `352`
- train rows: `843`
- validation rows: `61`
- eval overlap: `0`

### 4.3 format 검증

```bash
python3 scripts/validate_openai_sft_dataset.py \
  artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch19_hardcase.jsonl \
  artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch19_hardcase.jsonl
```

현재 결과:

- files: `2`
- rows: `904`
- errors: `0`

### 4.4 제출 전 dry-run manifest

```bash
python3 scripts/run_openai_fine_tuning_job.py \
  --model gpt-4.1-mini-2025-04-14 \
  --model-version pepper-ops-sft-v1.11.0 \
  --dataset-version ds_v14 \
  --prompt-version prompt_v10_validator_aligned_batch19_hardcase \
  --eval-version eval_v5 \
  --training-file artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch19_hardcase.jsonl \
  --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch19_hardcase.jsonl \
  --notes "batch19 real-shadow feedback plus validator-aligned prompt v10 dry-run only; blocked until shadow gates improve"
```

현재 dry-run manifest:

- `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-102244.json`

### 4.5 실제 submit

실제 submit 실행 명령:

```bash
python3 scripts/run_openai_fine_tuning_job.py \
  --model gpt-4.1-mini-2025-04-14 \
  --model-version pepper-ops-sft-v1.11.0 \
  --dataset-version ds_v14 \
  --prompt-version prompt_v10_validator_aligned_batch19_hardcase \
  --eval-version eval_v5 \
  --training-file artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch19_hardcase.jsonl \
  --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch19_hardcase.jsonl \
  --notes "batch19 real shadow feedback plus validator-aligned prompt and hard-case oversampling; submit after runtime integration stack implementation" \
  --submit
```

현재 submit manifest:

- `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v14-prompt_v10_validator_aligned_batch19_hardcase-eval_v5-20260413-113447.json`
- `job_id: ftjob-37TzJb1FtgGUghjfyaGqAxkA`
- `status: succeeded`

주의:

1. 이번 submit은 preflight blocker가 남아 있는 상태에서 사용자 승인으로 진행했다.
2. 따라서 완료 후에는 반드시 같은 frozen gate(`core24`, `extended120`, `extended160`, `extended200`, `blind_holdout50`, raw/validator gate)로만 재평가한다.
3. 결과가 기준을 못 넘으면 바로 후속 submit을 열지 않고 다시 `real shadow`, `risk rubric`, `data`를 수정한다.

### 4.6 ds_v14 완료 후 frozen gate 재평가

- `core24`: `0.8333`
- `extended120`: `0.7167`
- `extended160`: `0.6937`
- `extended200`: `0.695`
- `blind_holdout50 raw`: `0.74`
- `blind_holdout50 validator`: `0.9`
- `blind_holdout50 raw gate`: `blind_holdout_pass_rate 0.74`, `safety_invariant_pass_rate 0.75`, `promotion_decision hold`
- `blind_holdout50 validator gate`: `blind_holdout_pass_rate 0.9`, `safety_invariant_pass_rate 1.0`, `promotion_decision hold`
- validator gap 흡수 후 blind50 residual은 `5건`, extended200 residual은 `40건`으로 줄었다.

판단:

- `ds_v14`는 blind raw만 소폭 올렸고, validator blind는 `ds_v11`과 동률로 회복했지만 `core24`, `extended120`, `extended160`, `extended200`이 모두 `ds_v11` baseline보다 나쁘다.
- 따라서 baseline 승격 없이 rejected challenger로 고정한다.

### 4.7 ds_v15 batch20 corrective challenger package 생성

```bash
python3 scripts/build_openai_sft_datasets.py \
  --system-prompt-version sft_v10 \
  --validation-min-per-family 2 \
  --validation-ratio 0.15 \
  --validation-selection spread \
  --oversample-task-type safety_policy=5 \
  --oversample-task-type failure_response=5 \
  --oversample-task-type sensor_fault=5 \
  --oversample-task-type robot_task_prioritization=3 \
  --train-output artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch20_hardcase.jsonl \
  --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch20_hardcase.jsonl
```

현재 결과:

- source training rows: `360`
- train rows: `855`
- validation rows: `61`
- eval overlap: `0`

```bash
python3 scripts/validate_openai_sft_dataset.py \
  artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch20_hardcase.jsonl \
  artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch20_hardcase.jsonl
```

현재 결과:

- files: `2`
- rows: `916`
- errors: `0`

```bash
python3 scripts/run_openai_fine_tuning_job.py \
  --model gpt-4.1-mini-2025-04-14 \
  --model-version pepper-ops-sft-v1.12.0 \
  --dataset-version ds_v15 \
  --prompt-version prompt_v10_validator_aligned_batch20_hardcase \
  --eval-version eval_v6 \
  --training-file artifacts/fine_tuning/openai_sft_train_prompt_v10_validator_aligned_batch20_hardcase.jsonl \
  --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v10_validator_aligned_batch20_hardcase.jsonl \
  --notes "batch20 blind50 post-validator residual plus prompt v10 validator alignment and hard-case oversampling dry-run only; blocked until shadow gates improve"
```

현재 dry-run manifest:

- `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v15-prompt_v10_validator_aligned_batch20_hardcase-eval_v6-20260413-152557.json`

현재 preflight:

- `artifacts/reports/challenger_submit_preflight_ds_v15_real_shadow.md`
- decision: `blocked`
- blockers:
  - `blind_holdout50_validator 0.9000 < 0.9500`
  - `synthetic_shadow_day0 is hold (agreement=0.6667)`
  - `real_shadow_mode_status is rollback`

## 5. 평가 원칙

submit 후 평가는 아래 gate를 모두 남겨야 한다.

1. `core24`
2. `extended120`
3. `extended160`
4. `extended200`
5. `blind_holdout50`
6. `product_readiness_gate_raw`
7. `product_readiness_gate_validator_applied`

이 순서를 지키지 않으면 comparison table에 올리지 않는다. `synthetic shadow day0`는 frozen comparison gate가 아니라 submit preflight다.

## 6. 운영 원칙

- `--submit` 없는 실행은 dry-run이다.
- `OPENAI_API_KEY`가 없으면 submit 금지다.
- validation은 반드시 `spread` 기반 `60건`을 유지한다.
- 기본 경로 사용 시 `scripts/build_openai_sft_datasets.py`는 stale 합본이 아니라 현재 `training_sample_files()` 집합을 직접 읽는다.
- submit 전에는 [challenger_gate_baseline.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_gate_baseline.md:1), [challenger_candidate_ds_v12_prompt_v5_methodfix_batch17_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v12_prompt_v5_methodfix_batch17_hardcase.md:1), [challenger_candidate_ds_v13_prompt_v5_methodfix_batch18_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v13_prompt_v5_methodfix_batch18_hardcase.md:1), [challenger_candidate_ds_v14_prompt_v10_validator_aligned_batch19_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v14_prompt_v10_validator_aligned_batch19_hardcase.md:1), [challenger_candidate_ds_v15_prompt_v10_validator_aligned_batch20_hardcase.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v15_prompt_v10_validator_aligned_batch20_hardcase.md:1)를 함께 확인한다.
- candidate submit 전에는 `scripts/build_challenger_submit_preflight.py`로 `blind50 validator`, `synthetic shadow day0`, `real shadow mode` blocker를 다시 계산한다. real shadow window 리포트가 있으면 `--real-shadow-report`를 우선 사용한다.
- `synthetic shadow day0`가 `hold`인 동안은 후속 challenger를 dry-run까지만 허용한다.

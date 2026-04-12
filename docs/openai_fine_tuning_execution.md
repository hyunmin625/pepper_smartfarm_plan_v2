# OpenAI Fine-tuning Execution

이 문서는 현재 저장소 기준의 OpenAI SFT 실행 경로를 정리한다. 핵심 원칙은 `불필요한 submit 금지`, `frozen gate 고정`, `dry-run manifest 선행`이다.

## 1. 현재 기준선

- 마지막 완료 모델: `ds_v9/prompt_v5_methodfix`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v9-prompt-v5-methodfix-eval-v1-20260412-1257:DTgUbJHJ`
- raw baseline:
  - `core24 0.875`
  - `extended120 0.7083`
  - `extended160 0.575`
  - `extended200 0.51`
  - `blind_holdout50 0.32`
- validator-applied baseline:
  - `extended200 0.755`
  - `blind_holdout50 0.76`
  - `safety_invariant_pass_rate 1.0`
  - `field_usability_pass_rate 1.0`
- `ds_v10/prompt_v8`은 `cancelled`이며 비교 대상이 아니다.

## 2. 다음 challenger 원칙

- 다음 submit은 `1회`만 허용한다.
- broad prompt 변경이 아니라 `batch14 residual fix` 반영 여부만 본다.
- 다음 candidate는 아래로 고정한다.
  - `dataset_version=ds_v11`
  - `prompt_version=prompt_v5_methodfix_batch14`
  - `eval_version=eval_v2`
  - `system_prompt_version=sft_v5`
  - `model_version=pepper-ops-sft-v1.8.0`

세부 package는 [challenger_candidate_ds_v11_prompt_v5_methodfix_batch14.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v11_prompt_v5_methodfix_batch14.md:1)에 정리한다.

## 3. 실행 순서

1. training/eval 정합성 확인
2. OpenAI SFT용 train/validation JSONL 생성
3. format 검증
4. dry-run manifest 생성
5. 사용자 승인 후 `--submit`
6. sync로 active run 상태 기록
7. 같은 frozen gate로 평가

## 4. 현재 권장 명령

### 4.1 사전 검증

```bash
python3 scripts/validate_training_examples.py
python3 scripts/audit_training_data_consistency.py
python3 scripts/report_risk_slice_coverage.py
python3 scripts/report_eval_set_coverage.py --promotion-baseline extended160 --enforce-promotion-baseline
```

### 4.2 batch14 challenger draft 생성

```bash
python3 scripts/build_openai_sft_datasets.py \
  --system-prompt-version sft_v5 \
  --validation-min-per-family 2 \
  --validation-ratio 0.15 \
  --validation-selection spread \
  --train-output artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl \
  --validation-output artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl
```

현재 결과:

- source training rows: `288`
- train rows: `238`
- validation rows: `50`
- eval overlap: `0`

### 4.3 format 검증

```bash
python3 scripts/validate_openai_sft_dataset.py \
  artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl \
  artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl
```

현재 결과:

- files: `2`
- rows: `288`
- errors: `0`

### 4.4 dry-run manifest 생성

```bash
python3 scripts/run_openai_fine_tuning_job.py \
  --model gpt-4.1-mini-2025-04-14 \
  --model-version pepper-ops-sft-v1.8.0 \
  --dataset-version ds_v11 \
  --prompt-version prompt_v5_methodfix_batch14 \
  --eval-version eval_v2 \
  --training-file artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl \
  --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl \
  --notes "batch14 residual fix with spread validation 50; dry-run only"
```

현재 dry-run manifest:

- `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-000731.json`

### 4.5 실제 submit

실제 비용 지출은 아래처럼 `--submit`을 붙일 때만 허용한다.

```bash
python3 scripts/run_openai_fine_tuning_job.py \
  --submit \
  --model gpt-4.1-mini-2025-04-14 \
  --model-version pepper-ops-sft-v1.8.0 \
  --dataset-version ds_v11 \
  --prompt-version prompt_v5_methodfix_batch14 \
  --eval-version eval_v2 \
  --training-file artifacts/fine_tuning/openai_sft_train_prompt_v5_methodfix_batch14.jsonl \
  --validation-file artifacts/fine_tuning/openai_sft_validation_prompt_v5_methodfix_batch14.jsonl
```

현재 제출 상태:

- experiment: `ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-001407`
- job_id: `ftjob-dTfcY631bh5HJJKJnI5Xi0ML`
- submit manifest: `artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v11-prompt_v5_methodfix_batch14-eval_v2-20260413-001407.json`
- latest sync status: `queued`
- events_path: `artifacts/fine_tuning/events/ftjob-dTfcY631bh5HJJKJnI5Xi0ML.jsonl`

## 5. 평가 원칙

submit 후 평가는 아래 gate를 모두 남겨야 한다.

1. `core24`
2. `extended120`
3. `extended160`
4. `extended200`
5. `blind_holdout50`
6. `product_readiness_gate_raw`
7. `product_readiness_gate_validator_applied`

이 순서를 지키지 않으면 comparison table에 올리지 않는다.

## 6. 운영 원칙

- `--submit` 없는 실행은 dry-run이다.
- `OPENAI_API_KEY`가 없으면 submit 금지다.
- validation은 반드시 `spread` 기반 `50건`을 유지한다.
- 기본 경로 사용 시 `scripts/build_openai_sft_datasets.py`는 stale 합본이 아니라 현재 `training_sample_files()` 집합을 직접 읽는다.
- submit 전에는 [challenger_gate_baseline.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_gate_baseline.md:1)와 [challenger_candidate_ds_v11_prompt_v5_methodfix_batch14.md](/home/user/pepper-smartfarm-plan-v2/artifacts/fine_tuning/challenger_candidate_ds_v11_prompt_v5_methodfix_batch14.md:1)를 함께 확인한다.
- submit 후에는 manifest sync와 frozen gate 평가가 끝나기 전까지 후속 challenger를 만들지 않는다.

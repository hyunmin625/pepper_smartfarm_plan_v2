# OpenAI Fine-tuning Execution

이 문서는 `3.3 학습 실행`의 실제 실행 경로를 정리한다.

## 1. 실행 순서

1. 내부 seed 검증
2. OpenAI SFT용 chat-format train/validation JSONL 생성
3. dry-run manifest 생성
4. 필요 시 `--submit`으로 파일 업로드와 fine-tuning job 생성
5. job status / events sync
6. 비교표 갱신
7. fine-tuned model eval 실행

OpenAI SFT dataset 한 줄은 top-level에 `messages`만 가져야 한다. 내부 추적용 `metadata` 같은 필드는 학습 JSONL에 넣지 않고 run manifest와 failure log에 남긴다.

현재 `scripts/build_openai_sft_datasets.py`는 `--system-prompt-version`을 지원한다. 기본값은 `sft_v2`이고, 다음 라운드 draft는 `sft_v3`로 분리 관리한다.

## 2. 실행 명령

```bash
python3 scripts/validate_training_examples.py
python3 scripts/build_openai_sft_datasets.py
python3 scripts/validate_openai_sft_dataset.py \
  artifacts/fine_tuning/openai_sft_train.jsonl \
  artifacts/fine_tuning/openai_sft_validation.jsonl
python3 scripts/run_openai_fine_tuning_job.py
python3 scripts/render_fine_tuning_comparison_table.py
```

실제 job 생성은 아래처럼 `--submit`을 명시적으로 넣을 때만 수행한다.

```bash
python3 scripts/run_openai_fine_tuning_job.py --submit
```

`prompt_v3` draft를 반영한 학습 파일을 만들 때는 아래처럼 실행한다.

```bash
python3 scripts/build_openai_sft_datasets.py --system-prompt-version sft_v3
```

status sync는 다음 명령으로 수행한다.

```bash
python3 scripts/sync_openai_fine_tuning_job.py --manifest artifacts/fine_tuning/runs/<experiment>.json
python3 scripts/render_fine_tuning_comparison_table.py
```

현재 최신 fine-tuned model:

- job_id: `ftjob-MiiLGncQBHRXL2NZoBYWxMcc`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v3-prompt-v3-eval-v1-20260412-033726:DTXjV3Hg`

baseline 보관본:

- job_id: `ftjob-45KiYE5G2J125jSNg2QqakYm`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v1-prompt-v1-eval-v1-20260412-004953:DTV5z1FR`

직전 champion 보관본:

- job_id: `ftjob-ULBuPHoPBbAMah5rPdd2i334`
- fine_tuned_model: `ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v2-prompt-v2-eval-v1-20260412-021539:DTWRpIbI`

`3.4 파인튜닝 결과 검증`은 아래 명령으로 실행한다.

```bash
python3 scripts/evaluate_fine_tuned_model.py \
  --system-prompt-version sft_v3 \
  --model ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v3-prompt-v3-eval-v1-20260412-033726:DTXjV3Hg \
  --output-prefix artifacts/reports/fine_tuned_model_eval_ds_v3_prompt_v3
```

- 최신 champion 검증 기본값은 `sft_v3` prompt다.
- v1 baseline 비교는 아래처럼 legacy prompt로 별도 실행하거나, 이미 보관된 `artifacts/reports/fine_tuned_model_eval_legacy_prompt.*`를 사용한다.

```bash
python3 scripts/evaluate_fine_tuned_model.py \
  --system-prompt-version legacy \
  --model ft:gpt-4.1-mini-2025-04-14:hyunmin:ft-sft-gpt41mini-ds-v1-prompt-v1-eval-v1-20260412-004953:DTV5z1FR \
  --output-prefix artifacts/reports/fine_tuned_model_eval_legacy_prompt
```

- 최신 ds_v3/prompt_v3 eval 결과는 `pass_rate 0.6667`, `strict_json_rate 1.0`이다.
- legacy baseline은 `pass_rate 0.5417`이므로 현재 champion은 동일 eval `24건` 기준 `+0.1250` 개선됐다.
- 직전 ds_v2/prompt_v2 champion `0.625` 대비도 `+0.0417` 개선됐다.

재실행 시 run manifest가 덮어써지지 않도록 기본 실험명에는 시각 태그(`YYYYMMDD-HHMMSS`)가 붙는다. 필요하면 `--run-tag`로 명시할 수 있다.

## 3. 산출물

- `artifacts/fine_tuning/openai_sft_train.jsonl`
- `artifacts/fine_tuning/openai_sft_validation.jsonl`
- `artifacts/fine_tuning/runs/*.json`
- `artifacts/fine_tuning/events/*.jsonl`
- `artifacts/fine_tuning/failure_cases.jsonl`
- `artifacts/fine_tuning/fine_tuning_comparison_table.md`
- `artifacts/reports/fine_tuned_model_eval_latest.json`
- `artifacts/reports/fine_tuned_model_eval_latest.jsonl`
- `artifacts/reports/fine_tuned_model_eval_latest.md`
- `artifacts/reports/fine_tuned_model_eval_ds_v2_prompt_v2.{json,jsonl,md}`
- `artifacts/reports/fine_tuned_model_eval_ds_v3_prompt_v3.{json,jsonl,md}`
- `artifacts/reports/fine_tuned_model_eval_legacy_prompt.{json,jsonl,md}`
- `artifacts/reports/fine_tuned_model_eval_prompt_v2.{json,jsonl,md}`
- `artifacts/reports/fine_tuned_model_eval_prompt_v3.{json,jsonl,md}`

## 4. 운영 원칙

- `--submit`이 없는 기본 실행은 dry-run이다.
- 실제 API 호출 전에는 `.env`에 `OPENAI_API_KEY`가 있어야 한다.
- validation 파일은 같은 chat-format JSONL을 사용하고, training과 중복 라인을 넣지 않는다.
- OpenAI 학습 파일은 `messages` 외 top-level 필드를 허용하지 않는다.
- 실패 job은 `failure_cases.jsonl`에 누적 기록한다.
- `fine_tuned_model_eval_latest.*`는 현재 champion(ds_v3/prompt_v3) 결과를 가리키고, baseline은 `fine_tuned_model_eval_legacy_prompt.*`에 고정 보관한다.

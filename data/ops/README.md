# Shadow Mode Ops Case Files

이 디렉터리는 실제 운영 shadow case JSONL을 일자별로 쌓는 위치다.

## 파일명

- `shadow_mode_cases_YYYYMMDD.jsonl`
- 같은 날 추가분은 `shadow_mode_cases_YYYYMMDD_partN.jsonl`

## request_id

실제 운영 case는 아래 형식을 사용한다.

- `prod-shadow-YYYYMMDD-NNN`
- 예: `prod-shadow-20260425-001`

`request_id`는 전체 audit window에서 유니크해야 한다. seed, offline replay, synthetic case ID를 실제 운영 window에 재사용하지 않는다.

## rehearsal 파일

운영 파이프라인 리허설용 파일은 아래 명령으로 만든다.

```bash
python3 scripts/generate_shadow_ops_rehearsal_day.py --date YYYYMMDD --count 12
python3 scripts/validate_shadow_cases.py --cases-file data/ops/shadow_mode_rehearsal_YYYYMMDD.jsonl
python3 scripts/run_shadow_mode_ops_pipeline.py \
  --cases-file data/ops/shadow_mode_rehearsal_YYYYMMDD.jsonl \
  --validate-only
```

리허설 파일은 `rehearsal-shadow-YYYYMMDD-NNN` request_id와 `shadow-rehearsal-YYYYMMDD` eval_set_id를 사용한다. 이는 비용 없는 경로 검증용이며 `--real-case` 검증이나 승격 근거로 사용하지 않는다.

실제 운영 window에서 발견된 disagreement는 `data/ops/shadow_residual_backlog_YYYYMMDD.jsonl`에 따로 남긴다. row 구조는 `schemas/shadow_residual_backlog_schema.json`, 처리 기준은 `docs/real_shadow_residual_backlog.md`를 따른다.

```bash
python3 scripts/validate_shadow_residual_backlog.py \
  --backlog-file data/ops/shadow_residual_backlog_YYYYMMDD.jsonl \
  --source-cases-file data/ops/shadow_mode_cases_YYYYMMDD.jsonl
```

작성 시작용 예시는 `data/ops/shadow_residual_backlog_template.jsonl`에 둔다.

## 검증

실제 운영 파일은 적재 전에 검증한다.

```bash
python3 scripts/validate_shadow_cases.py \
  --cases-file data/ops/shadow_mode_cases_YYYYMMDD.jsonl \
  --existing-audit-log artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl \
  --real-case
```

검증 기준은 필수 필드, task/context 정렬, operator outcome, request_id 중복, seed/offline eval_set_id 금지다.

## 적재와 리포트

로컬 ops-api PostgreSQL stack이 실행 중일 때는 전체 파이프라인을 한 번에 실행한다.

```bash
python3 scripts/run_shadow_mode_ops_pipeline.py \
  --base-url http://127.0.0.1:8000 \
  --cases-file data/ops/shadow_mode_cases_YYYYMMDD.jsonl \
  --real-case \
  --gate hold \
  --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151.json \
  --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846.json
```

실제 현장 case만 real window 승격 근거로 인정한다. seed pack과 template은 경로 검증용이다.

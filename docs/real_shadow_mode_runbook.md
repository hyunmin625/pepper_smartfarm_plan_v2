# Real Shadow Mode Runbook

이 문서는 공사 완료 후 실제 운영 로그를 `shadow mode` 형식으로 누적하고, submit/승격 판단까지 연결하는 최소 실행 절차를 정의한다.

## 목적

- synthetic/offline shadow와 실제 운영 shadow를 분리한다.
- `not_run` 상태를 빨리 벗어나 `real shadow mode evidence`를 수집한다.
- `ds_v12`, `ds_v13` 같은 dry-run challenger의 submit blocker를 운영 로그 기준으로 다시 계산한다.

## 입력 단위

실제 shadow mode 케이스 JSONL은 아래 구조를 따른다.

- `request_id`
- `task_type`
- `metadata`
- `context`
- `output`
- `observed`

형식은 `data/examples/shadow_mode_runtime_cases.jsonl`과 동일하다. 차이는 synthetic seed가 아니라 실제 운영 시점의 `context`, 실제 AI 출력, 실제 운영자 조치를 담는다는 점이다.

바로 시작할 때는 `data/ops/shadow_mode_cases_template.jsonl`을 복사해 일자별 파일로 만든다.

## 실행 절차

### 1. 일자별 capture

```bash
python3 scripts/run_shadow_mode_capture_cases.py \
  --cases-file data/ops/shadow_mode_cases_20260414.jsonl \
  --audit-log artifacts/runtime/llm_orchestrator/shadow_mode_prod_20260414.jsonl \
  --validator-audit-log artifacts/runtime/llm_orchestrator/output_validator_prod_20260414.jsonl \
  --output-prefix artifacts/reports/shadow_mode_prod_20260414
```

기본 동작은 기존 로그를 비우고 새 일자 리포트를 만든다.

### 2. 같은 일자에 추가 적재

```bash
python3 scripts/run_shadow_mode_capture_cases.py \
  --cases-file data/ops/shadow_mode_cases_20260414_part2.jsonl \
  --audit-log artifacts/runtime/llm_orchestrator/shadow_mode_prod_20260414.jsonl \
  --validator-audit-log artifacts/runtime/llm_orchestrator/output_validator_prod_20260414.jsonl \
  --output-prefix artifacts/reports/shadow_mode_prod_20260414 \
  --append
```

### 3. 다일자 window 요약

```bash
python3 scripts/build_shadow_mode_window_report.py \
  --audit-log artifacts/runtime/llm_orchestrator/shadow_mode_prod_20260414.jsonl \
  --audit-log artifacts/runtime/llm_orchestrator/shadow_mode_prod_20260415.jsonl \
  --output-prefix artifacts/reports/shadow_mode_prod_window_20260414_20260415
```

## 판단 기준

- `critical_disagreement_count > 0`이면 `rollback`
- `operator_agreement_rate < 0.9`이면 `hold`
- `citation_coverage < 0.95`이면 `hold`
- 7일 이상 안정적이면 `promote` 검토

## challenger submit 연결

실제 shadow window가 생기면 `scripts/build_challenger_submit_preflight.py`에 `--real-shadow-report`로 연결한다.

스크립트가 아래처럼 자동 변환한다.

- `not_run`: 실제 shadow 로그 없음
- `hold`: 실제 shadow window 리포트가 `hold`
- `pass`: 실제 shadow window 리포트가 `promote`
- `rollback`: 실제 shadow window 리포트가 `rollback`

예시:

```bash
python3 scripts/build_challenger_submit_preflight.py \
  --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151.json \
  --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846.json \
  --real-shadow-report artifacts/reports/shadow_mode_prod_window_20260414_20260415.json \
  --output-prefix artifacts/reports/challenger_submit_preflight_prod_window
```

## 현재 해석

- 현재 저장소 기준 synthetic shadow `day0`는 `hold`다.
- offline replay는 `promote`지만 실제 운영 shadow 대체가 아니다.
- 따라서 지금은 `real shadow mode`를 최소 일자 단위로 쌓는 경로를 먼저 열어 두는 단계다.

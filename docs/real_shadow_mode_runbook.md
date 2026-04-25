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

권장 경로는 ops-api를 통한 적재다. 이 경로가 `POST /shadow/cases/capture`, `/shadow/window`, auth/audit/rotation guard를 모두 통과하므로 실제 운영 흐름에 가장 가깝다.

### 0. ops-api PostgreSQL stack 실행

```bash
bash scripts/run_ops_api_postgres_stack.sh
```

다른 터미널에서 shadow case를 적재한다.

```bash
.venv/bin/python scripts/push_shadow_cases_to_ops_api.py \
  --base-url http://127.0.0.1:8000 \
  --cases-file data/ops/shadow_mode_cases_20260425.jsonl \
  --append \
  --batch-size 25 \
  --gate hold
```

seed pack으로 경로만 확인할 때는 아래처럼 실행한다.

```bash
.venv/bin/python scripts/push_shadow_cases_to_ops_api.py \
  --base-url http://127.0.0.1:8000 \
  --cases-file data/examples/shadow_mode_runtime_day0_seed_cases.jsonl \
  --append \
  --batch-size 12 \
  --gate hold
```

ops-api 기본 audit log는 `artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl`이다. window artifact는 아래 명령으로 고정한다.

```bash
python3 scripts/build_shadow_mode_window_report.py \
  --audit-log artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl \
  --output-prefix artifacts/reports/shadow_mode_ops_api_window_YYYYMMDD
```

### 1. 일자별 capture

아래 direct capture 경로는 ops-api 없이 audit log 형식만 검증할 때 사용한다. 실제 운영 후보 판단은 위 ops-api 적재 경로를 우선한다.

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

## 2026-04-25 경로 확인

- ops-api PostgreSQL stack을 실행한 뒤 `push_shadow_cases_to_ops_api.py`로 day0 seed `12건`을 추가 적재했다.
- 누적 audit log: `artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl`
- window report: `artifacts/reports/shadow_mode_ops_api_seed_window_20260425.json`, `artifacts/reports/shadow_mode_ops_api_seed_window_20260425.md`
- 결과: `decision_count 24`, `operator_agreement_rate 0.6667`, `critical_disagreement_count 0`, `promotion_decision hold`
- preflight 연결: `artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13_ops_api_seed_window_20260425.json`, `artifacts/reports/challenger_submit_preflight_ds_v12_ds_v13_ops_api_seed_window_20260425.md`
- preflight 결과: `real_shadow_mode_status hold`, `ds_v12 blocked`, `ds_v13 blocked`
- 해석: 적재/집계 경로는 동작하지만, seed residual이 반복되므로 승격 판단은 계속 `hold`다. 실제 운영 case는 request_id를 일자/zone/action 기준으로 유니크하게 만든다.

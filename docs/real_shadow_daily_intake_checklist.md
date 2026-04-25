# Real Shadow Daily Intake Checklist

실제 운영 shadow case를 하루 단위로 수집한 뒤 승격 판단과 corrective backlog까지 연결하는 체크리스트다. seed, offline replay, rehearsal 파일은 이 절차의 대체물이 아니다.

## 1. 파일 준비

- [ ] 당일 파일명을 `data/ops/shadow_mode_cases_YYYYMMDD.jsonl`로 고정한다.
- [ ] 모든 `request_id`가 `prod-shadow-YYYYMMDD-NNN` 형식인지 확인한다.
- [ ] `metadata.eval_set_id`가 `shadow-prod-YYYYMMDD` 형식인지 확인한다.
- [ ] `observed.operator_agreement`, `critical_disagreement`, `manual_override_used`, `growth_stage`가 채워졌는지 확인한다.

## 2. 입력 검증

```bash
python3 scripts/validate_shadow_cases.py \
  --cases-file data/ops/shadow_mode_cases_YYYYMMDD.jsonl \
  --existing-audit-log artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl \
  --real-case
```

- [ ] errors가 `[]`인지 확인한다.
- [ ] 기존 audit log와 `request_id` 중복이 없는지 확인한다.

## 3. ops-api 적재와 window report

```bash
python3 scripts/run_shadow_mode_ops_pipeline.py \
  --base-url http://127.0.0.1:8000 \
  --cases-file data/ops/shadow_mode_cases_YYYYMMDD.jsonl \
  --real-case \
  --gate hold \
  --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v12-prompt_v5_methodfix_batch17_hardcase-eval_v3-20260413-035151.json \
  --candidate-manifest artifacts/fine_tuning/runs/ft-sft-gpt41mini-ds_v13-prompt_v5_methodfix_batch18_hardcase-eval_v4-20260413-075846.json
```

- [ ] `/shadow/cases/capture` 적재가 성공했는지 확인한다.
- [ ] `artifacts/reports/shadow_mode_ops_api_real_window_YYYYMMDD.{json,md}`가 생성됐는지 확인한다.
- [ ] `promotion_decision`이 `hold`, `rollback`, `promote` 중 무엇인지 기록한다.

## 4. residual backlog 작성

operator disagreement 또는 policy mismatch가 있으면 `data/ops/shadow_residual_backlog_YYYYMMDD.jsonl`에 row를 추가한다.

```bash
python3 scripts/validate_shadow_residual_backlog.py \
  --backlog-file data/ops/shadow_residual_backlog_YYYYMMDD.jsonl \
  --source-cases-file data/ops/shadow_mode_cases_YYYYMMDD.jsonl
```

- [ ] owner를 `data_and_model`, `risk_rubric_and_data`, `robot_contract_and_model`, `runtime_validator_gap`, `ops_process` 중 하나로 지정한다.
- [ ] `expected_fix.fix_type`을 하나로 고정한다.
- [ ] `fixed` 상태는 실제 재검증 전까지 `verified`로 닫지 않는다.

## 5. backlog summary

```bash
python3 scripts/report_shadow_residual_backlog.py \
  --backlog-file data/ops/shadow_residual_backlog_YYYYMMDD.jsonl \
  --output-json artifacts/reports/shadow_residual_backlog_YYYYMMDD.json \
  --output-md artifacts/reports/shadow_residual_backlog_YYYYMMDD.md
```

- [ ] `critical_residual_count`가 0인지 확인한다.
- [ ] `unverified_fix_count`가 0인지 확인한다.
- [ ] owner별 다음 조치가 실제 파일 경로로 연결됐는지 확인한다.

## 6. 대시보드 확인

- [ ] `/dashboard`의 Runtime Gate 카드에서 `shadow_residuals`가 기대 수치와 맞는지 확인한다.
- [ ] `Shadow Mode > Real Shadow Residuals` 카드에서 최근 residual이 보이는지 확인한다.
- [ ] residual이 남아 있으면 submit 후보를 열지 않는다.

## 7. 리허설 전용 명령

현장 case 없이 경로만 점검할 때만 사용한다.

```bash
python3 scripts/generate_shadow_ops_rehearsal_day.py --date YYYYMMDD --count 12
python3 scripts/run_phase_p_quality_gate.py
```

리허설 파일은 승격 판단이나 real backlog source case로 사용하지 않는다.

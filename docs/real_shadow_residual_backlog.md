# Real Shadow Residual Backlog

이 문서는 실제 운영 shadow window에서 드러난 모델/정책/운영 불일치를 corrective backlog로 옮기는 기준이다. seed pack, offline replay, rehearsal 파일은 경로 검증 자료이며, 이 backlog의 승격 근거가 아니다.

## 목적

- 실제 현장 case의 operator disagreement를 누락 없이 추적한다.
- residual owner를 `data_and_model`, `risk_rubric_and_data`, `robot_contract_and_model`, `runtime_validator_gap`, `ops_process`로 분리한다.
- 다음 조치를 training sample, rubric update, validator rule, retriever source, ops runbook, code fix 중 하나로 고정한다.

## 저장 위치

권장 파일명은 아래 형식이다.

- `data/ops/shadow_residual_backlog_YYYYMMDD.jsonl`
- rolling window 단위 묶음은 `data/ops/shadow_residual_backlog_window_YYYYMMDD_YYYYMMDD.jsonl`

각 row는 [schemas/shadow_residual_backlog_schema.json](../schemas/shadow_residual_backlog_schema.json)을 따른다.

## 항목 기준

필수 필드는 다음과 같다.

- `residual_id`: `shadow-residual-YYYYMMDD-NNN`
- `source_window_id`: window report id 또는 artifact stem
- `source_case_request_id`: 원본 실제 운영 shadow case의 `request_id`
- `owner`: corrective ownership
- `severity`: 운영 위험도
- `status`: `new -> triaged -> queued -> fixed -> verified`
- `failure_modes`: 예: `missing_create_alert`, `wrong_risk_level`, `inspect_crop_enum_drift`
- `expected_fix`: 조치 유형과 대상 파일

## 운영 절차

1. `scripts/run_shadow_mode_ops_pipeline.py --real-case`로 실제 case를 PostgreSQL ops-api에 적재한다.
2. 생성된 `shadow_mode_ops_api_real_window_YYYYMMDD` 리포트에서 disagreement와 policy mismatch를 확인한다.
3. operator 기대와 모델 출력이 다르면 backlog row를 추가한다.
4. owner별로 다음 조치를 묶는다. 모델 출력이 바뀌어야 하는 건 training/data backlog, 안전 규칙으로 강제할 수 있는 건 validator backlog, 운영 절차 문제는 ops runbook backlog로 분리한다.
5. fix가 반영되면 같은 유형의 실제 shadow case에서 재발 여부를 확인한 뒤 `verified`로 닫는다.

## 예시

```json
{
  "residual_id": "shadow-residual-20260425-001",
  "source_window_id": "shadow_mode_ops_api_real_window_20260425",
  "source_case_request_id": "prod-shadow-20260425-017",
  "source_report_path": "artifacts/reports/shadow_mode_ops_api_real_window_20260425.json",
  "zone_id": "gh-01-zone-a",
  "task_type": "action_recommendation",
  "owner": "data_and_model",
  "severity": "high",
  "status": "new",
  "failure_modes": ["missing_create_alert", "fertigation_review_too_early"],
  "expected_fix": {
    "fix_type": "training_sample",
    "summary": "Add real shadow corrective examples for GT Master dry-back review before fertigation adjustment.",
    "target_paths": ["data/examples/action_recommendation_samples_batch_next_real_shadow.jsonl"]
  },
  "evidence": {
    "model_output_summary": "adjust_fertigation was recommended before alert and human check.",
    "operator_expected_summary": "create_alert + request_human_check first, no fertigation change until inspection.",
    "validator_reason_codes": [],
    "citations": [],
    "notes": "Actual production case only; do not replace with seed replay."
  },
  "created_at": "2026-04-25T00:00:00Z",
  "updated_at": null
}
```

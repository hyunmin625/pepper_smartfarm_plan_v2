# Training Dataset Build

이 문서는 `3.2 데이터 파일 생성`의 기준 문서다. 목적은 task family별 seed/eval 파일을 합본 JSONL과 통계 리포트로 재생성하는 절차를 고정하는 것이다.

## 1. 입력 범위

- training seed: `qa_reference/state_judgement/action_recommendation/forbidden_action/failure_response/robot_task/reporting` family의 `data/examples/*_samples*.jsonl`
- eval seed: `evals/*_eval_set.jsonl`, `evals/edge_case_eval_set.jsonl`, `evals/seasonal_eval_set.jsonl`

## 2. 생성 명령

```bash
python3 scripts/validate_training_examples.py
python3 scripts/build_training_jsonl.py --include-source-file
python3 scripts/build_eval_jsonl.py --include-source-file
python3 scripts/report_training_sample_stats.py
python3 scripts/audit_training_data_consistency.py
```

## 3. 생성 산출물

- `artifacts/training/combined_training_samples.jsonl`
- `artifacts/training/combined_eval_cases.jsonl`
- `artifacts/reports/training_sample_stats.json`

## 4. 현재 기준 결과

- training seed: `17 files`, `147 rows`
- eval seed: `7 files`, `24 rows`
- duplicate sample id: `0`
- duplicate row: `0`
- potential contradiction: `0`

## 5. 운영 원칙

- 합본 생성 전에 항상 `validate_training_examples.py`를 먼저 통과시킨다.
- 수동 검토 대상은 `training_sample_stats.json`의 longest sample과 낮은 빈도 `task_type`을 우선 본다.
- 학습용 합본은 source file trace를 유지해 나중에 오류 샘플을 원본 파일까지 역추적할 수 있게 한다.

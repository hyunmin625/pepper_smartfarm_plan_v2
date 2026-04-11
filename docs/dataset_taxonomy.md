# Dataset Taxonomy

이 문서는 `2.2 데이터셋 분류 체계 정의`를 위해 적고추 전문가 AI 학습/평가 데이터를 task family 기준으로 분류한다.

## 1. 분류 원칙

- 자주 바뀌는 재배 기준은 RAG 청크로 관리하고, 학습 데이터는 출력 형식과 판단 패턴을 안정화하는 데 쓴다.
- 같은 센서 상태라도 목적이 다르면 별도 task type으로 분리한다.
- 학습용 seed와 평가셋은 같은 taxonomy를 공유하되, eval은 기대 조건을 더 엄격하게 둔다.

## 2. Task Family

| task_type | 목적 | 현재 seed 파일 | 현재 eval 파일 |
|---|---|---|---|
| `qa_reference` | 질의응답형 설명과 citation 학습 | `data/examples/qa_reference_samples.jsonl` | 없음 |
| `state_judgement` | 상태 요약, 위험도, follow-up 생성 | `data/examples/state_judgement_samples.jsonl` | `evals/expert_judgement_eval_set.jsonl` |
| `action_recommendation` | 추천 행동과 승인 필요 여부 생성 | `data/examples/action_recommendation_samples.jsonl` | `evals/action_recommendation_eval_set.jsonl` |
| `forbidden_action` | 위험 행동 차단 또는 승인 필요 판정 | `data/examples/forbidden_action_samples.jsonl` | `evals/forbidden_action_eval_set.jsonl` |
| `failure_response` | 센서/장치/통신 장애 시 안전한 fallback 생성 | `data/examples/failure_response_samples.jsonl` | `evals/failure_response_eval_set.jsonl` |
| `robot_task_prioritization` | 수확/점검 후보의 우선순위와 skip reason 생성 | `data/examples/robot_task_samples.jsonl` | `evals/robot_task_eval_set.jsonl` |
| `alert_report` | 운영자용 알람/보고서 문구 생성 | `data/examples/reporting_samples.jsonl` | 없음 |

## 3. 학습 목적별 묶음

- `sft_core`: `state_judgement`, `action_recommendation`, `forbidden_action`
- `sft_recovery`: `failure_response`
- `sft_robot`: `robot_task_prioritization`
- `sft_reporting`: `qa_reference`, `alert_report`
- `eval_core`: `expert_judgement_eval_set`, `action_recommendation_eval_set`, `forbidden_action_eval_set`
- `eval_recovery`: `failure_response_eval_set`
- `eval_robot`: `robot_task_eval_set`

## 4. 입력 공통 구성

모든 task는 가능한 한 아래 맥락을 공통으로 가진다.

- `growth_stage`
- `state_summary`
- `sensor_quality` 또는 장애 정보
- `retrieved_context`
- 필요 시 `recent_events`, `active_constraints`, `operator_notes`

## 5. 남은 확장

1. `qa_reference` 평가셋 추가
2. `alert_report` 평가셋 추가
3. 운영 로그가 쌓이면 `preference`와 `correction` 묶음 추가
4. 계절별/품종별 slice dataset 정의

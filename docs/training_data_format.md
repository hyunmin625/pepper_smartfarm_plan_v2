# Training Data Format

이 문서는 `2.3 학습 데이터 포맷 정의`를 위해 seed JSONL의 공통 형식을 정의한다.

## 1. 공통 행 구조

학습용 JSONL 한 줄은 아래 구조를 따른다.

```json
{
  "sample_id": "action-rec-001",
  "task_type": "action_recommendation",
  "input": {},
  "preferred_output": {}
}
```

- `sample_id`: 파일 전체에서 유일한 식별자
- `task_type`: [dataset_taxonomy.md](/home/user/pepper-smartfarm-plan-v2/docs/dataset_taxonomy.md)의 task family
- `input`: 모델에 넣을 상태, 질의, 장애, 운영 맥락
- `preferred_output`: 모델이 따라야 할 구조화 응답

## 2. Input Message 포맷

공통 권장 필드:

- `farm_id`
- `zone_id`
- `growth_stage`
- `state_summary`
- `recent_events`
- `active_constraints`
- `retrieved_context`

질의응답형은 `question`, 장애대응형은 `failure_type`, 로봇형은 `candidates`, 보고서형은 `alert_context`를 추가한다.

## 3. Preferred Output 포맷

### 3.1 상태판단 / 행동추천

- `situation_summary`
- `risk_level`
- `diagnosis`
- `recommended_actions`
- `requires_human_approval`
- `follow_up`
- `confidence`
- `retrieval_coverage`
- `citations`

### 3.2 금지행동

- `decision`
- `risk_level`
- `blocked_action_type`
- `reason`
- `required_follow_up`
- `citations`

### 3.3 장애대응

- `situation_summary`
- `risk_level`
- `recommended_actions`
- `fallback_mode`
- `follow_up`
- `confidence`
- `retrieval_coverage`
- `citations`

### 3.4 로봇 우선순위

- `situation_summary`
- `risk_level`
- `robot_tasks`
- `skipped_candidates`
- `requires_human_approval`
- `follow_up`
- `confidence`
- `retrieval_coverage`
- `citations`

### 3.5 알람/보고서

- `report_type`
- `title`
- `summary`
- `sections`
- `urgency`
- `citations`

## 4. 템플릿 기준

- 상태판단 템플릿: `state_judgement_samples.jsonl`
- 행동추천 템플릿: `action_recommendation_samples.jsonl`
- 금지행동 템플릿: `forbidden_action_samples.jsonl`
- 로봇 우선순위 템플릿: `robot_task_samples.jsonl`
- 장애대응 템플릿: `failure_response_samples.jsonl`

## 5. JSON Schema 포함 방식

- 상태 입력은 `schemas/state_schema.json`을 기준으로 요약하거나 축약 필드를 넣는다.
- 행동 출력은 가능한 한 `schemas/action_schema.json` 필드명을 재사용한다.
- 운영형 모델 목표와 허용 action 목록은 `docs/fine_tuning_objectives.md`를 기준으로 고정한다.
- 평가셋은 전체 스키마를 반복 복사하지 않고 `expected`에 핵심 제약만 넣는다.
- 스키마가 아직 없는 task는 먼저 field contract를 문서화하고, 실제 구현 시 JSON schema로 승격한다.

## 6. 평가셋 행 구조

```json
{
  "eval_id": "action-eval-001",
  "category": "action_recommendation",
  "task_type": "action_recommendation",
  "input_state": {},
  "retrieved_context": [],
  "expected": {},
  "grading_notes": ""
}
```

평가셋은 자유 응답 전체를 고정하지 않고 `required_action_types`, `forbidden_action_types`, `must_include_citations` 같은 제약 중심으로 채점한다.

# Training Example Seeds

이 디렉터리는 적고추 전문가 AI Agent의 파인튜닝 후보 데이터를 관리한다.

## 파일

- `qa_reference_samples.jsonl`: citation이 필요한 질의응답형 설명 seed
- `state_judgement_samples.jsonl`: 센서 상태와 RAG 문맥을 보고 상태를 판단하는 예시
- `action_recommendation_samples.jsonl`: 추천 행동과 승인 필요 여부를 구조화해 출력하는 예시
- `forbidden_action_samples.jsonl`: 위험하거나 승인 없이는 실행하면 안 되는 행동을 차단하는 예시
- `failure_response_samples.jsonl`: 센서/장치/통신 장애 시 fallback과 안전 대응을 생성하는 예시
- `robot_task_samples.jsonl`: 수확/점검 후보의 로봇 작업 우선순위를 정하는 예시
- `reporting_samples.jsonl`: 운영자 알람과 보고서 문구를 생성하는 예시
- `synthetic_sensor_scenarios.jsonl`: 실측 데이터가 없을 때 offline runner와 eval에 넣을 합성 센서 상태 시나리오
- `sensor_catalog_seed.json`: zone별 설치 위치, protocol, calibration, model_profile까지 포함한 현장형 수집 카탈로그 seed

## 작성 원칙

- 자주 바뀌는 기준값은 샘플에 고정하지 않고 RAG citation으로 연결한다.
- 출력은 구조화된 JSON을 유지한다.
- 위험 상황에서는 자동 실행보다 보수적 판단, 승인 요청, follow_up을 우선한다.
- 센서 품질이 나쁘면 장치 제어 추천을 제한한다.
- 합성 시나리오는 실제 운영 이벤트와 유사한 추세/센서 품질 문제를 재현해야 한다.
- 카탈로그 seed는 실제 장비 선정 전까지 수집 계약과 `sensor-ingestor` 설정 초안의 기준점 역할을 한다.
- seed 검증은 `python3 scripts/validate_training_examples.py`로 수행한다.

## 다음 확장

1. 생육 단계별 최소 20개 상태판단 샘플 작성
2. hard block 유형별 금지행동 샘플 작성
3. 품종별/계절별 행동추천 샘플 추가
4. 운영자 승인/거절 로그가 생기면 preference pair로 확장
5. 합성 센서 시나리오를 계절/재배형태별로 30건 이상으로 확장

# Training Example Seeds

이 디렉터리는 적고추 전문가 AI Agent의 파인튜닝 후보 데이터를 관리한다.

## 파일

- `state_judgement_samples.jsonl`: 센서 상태와 RAG 문맥을 보고 상태를 판단하는 예시
- `forbidden_action_samples.jsonl`: 위험하거나 승인 없이는 실행하면 안 되는 행동을 차단하는 예시

## 작성 원칙

- 자주 바뀌는 기준값은 샘플에 고정하지 않고 RAG citation으로 연결한다.
- 출력은 구조화된 JSON을 유지한다.
- 위험 상황에서는 자동 실행보다 보수적 판단, 승인 요청, follow_up을 우선한다.
- 센서 품질이 나쁘면 장치 제어 추천을 제한한다.

## 다음 확장

1. 생육 단계별 최소 20개 상태판단 샘플 작성
2. hard block 유형별 금지행동 샘플 작성
3. approval_required 샘플과 hard_block 샘플 분리
4. 운영자 승인/거절 로그가 생기면 preference pair로 확장

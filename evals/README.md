# Expert Judgement Evals

이 디렉터리는 적고추 스마트팜 운영 전문가 AI Agent의 판단 품질을 검증하기 위한 평가셋을 관리한다.

## 현재 평가셋

- `expert_judgement_eval_set.jsonl`: 전문가 판단 초기 평가셋

## 평가 목적

평가셋은 모델이 아래 요구를 만족하는지 확인한다.

- JSON 출력 구조를 지킨다.
- 생육 단계와 센서 맥락을 반영한다.
- RAG 근거가 필요한 판단에는 citation을 포함한다.
- 센서 품질이 나쁘면 자동 실행을 보수적으로 제한한다.
- 금지 행동을 추천하지 않는다.
- 승인 필요 상황을 명확히 구분한다.

## 초기 카테고리

- `state_judgement`: 정상 상태와 관찰 판단
- `climate_risk`: 고온, 결로, 과습, 광 스트레스
- `rootzone_diagnosis`: 과습, 과건조, 뿌리 갈변, 배지 이상
- `nutrient_risk`: EC/pH, 배액률, 양분 흡수 이상
- `sensor_fault`: missing, stale, outlier, calibration error
- `pest_disease_risk`: 병해충 위험과 비전 의심 증상
- `harvest_drying`: 수확, 건조, 저장 판단
- `safety_policy`: 작업자, 로봇, 장치 안전 정책

## 다음 확장

1. 각 카테고리별 최소 20개 케이스 작성
2. 정상/주의/위험/차단 케이스 균형화
3. 생육 단계별 케이스 분리
4. RAG citation 정답 chunk 지정
5. 평가 실행 스크립트 작성

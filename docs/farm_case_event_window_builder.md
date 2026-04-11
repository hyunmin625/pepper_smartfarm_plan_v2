# Farm Case Event Window Builder

이 문서는 운영 로그를 `farm_case_candidate`로 만들기 전, 센서/장치/작업자 이벤트를 하나의 `event_window`로 묶는 규칙을 정의한다.

## 목적

- 원시 로그를 그대로 쓰지 않고 판단 가능한 사건 단위로 정리한다.
- action, 센서 변화, 결과의 시간 순서를 명확히 남긴다.
- `farm_case` 승격 전에 재현 가능한 근거 구간을 확보한다.

## 입력 이벤트

- 센서 이상/위험 알람: 고온, 과습, EC 상승, 병해충 카운트 증가, 건조실 과습
- 장치 명령: 관수, 환기, 차광, 난방, 제습, CO2, 건조 운전
- 작업자 개입: 방제, 수확, 제거, 재정식, 수동 override
- AI 판단 로그: 추천 action, block, approval 요청
- 결과 확인: 회복, 실패, 확산, 품질 저하, 출하 보류

## 기본 윈도우 규칙

- anchor event는 최초 위험 알람 또는 작업자 첫 개입 시점으로 잡는다.
- pre-window는 anchor 이전 상태를 보기 위해 포함한다.
- post-window는 action 이후 결과를 보기 위해 포함한다.
- 기본 시간 범위:
  - 기후/환경제어: `-6h ~ +12h`
  - 근권/양액 이상: `-12h ~ +24h`
  - 병해충/병징: `-24h ~ +72h`
  - 활착 실패/생리장해: `-24h ~ +96h`
  - 수확 후 건조/저장: `-12h ~ +48h`
- hard cap:
  - 단일 event window는 최대 `120h`
  - 같은 원인으로 24시간 이상 끊김 없이 이어지는 경우만 연장

## 병합과 분리 규칙

- 같은 `zone_id`, 같은 `risk_tag`, 같은 작기에서 anchor 간격이 4시간 이하면 하나로 병합한다.
- 장치 action이 완전히 다르거나 원인 태그가 달라지면 분리한다.
- 센서 fault는 재배 사건과 분리해 별도 window로 관리한다.
- 장마 후 역병처럼 강우 예보와 병징이 이어진 경우는 동일 window로 묶되, `causality_tags`에 전이 근거를 남긴다.

## 포함 조건

- 포함 로그:
  - anchor 전후 센서 추세
  - 해당 구간 장치 명령과 수동 개입
  - AI 추천과 승인/거절 결과
  - 결과 판정 근거 메모, 사진 판독, 검사 결과
- 제외 로그:
  - 시간 동기화가 안 된 이벤트
  - `sensor_quality=bad` 핵심 센서만으로 만든 판단
  - 사건과 무관한 정기 작업

## 품질 게이트

- `sensor_quality=good`: 자동 후보 생성 가능
- `sensor_quality=partial`: 후보 생성 가능, 리뷰 시 수동 확인 필수
- `sensor_quality=bad`: `review_status=draft`만 허용, RAG 승격 금지
- action 이후 결과 관찰 구간이 없으면 `outcome=unknown`으로 고정한다.

## event_window 출력 계약

- 식별: `event_window_id`, `farm_id`, `zone_id`
- 시간: `anchor_at`, `event_start_at`, `event_end_at`
- 맥락: `trigger_type`, `growth_stage`, `cultivar`, `season`, `cultivation_type`
- 근거: `sensor_window_refs`, `operation_log_refs`, `ai_decision_refs`, `sensor_quality`
- 태그: `sensor_tags`, `risk_tags`, `operation_tags`, `causality_tags`, `visual_tags`
- 결과: `action_taken`, `outcome`, `outcome_evidence`

## 후보 생성 규칙

1. `event_window`를 만든다.
2. review에 필요한 핵심 태그와 요약을 붙여 `farm_case_candidate`로 변환한다.
3. `review_status=approved` 전까지는 운영 RAG에 넣지 않는다.
4. 반복되는 동일 패턴은 개별 case 누적보다 `internal_sop` 승격 후보로 전환한다.

## 샘플 매핑

- [farm_case_candidate_samples.jsonl](../data/examples/farm_case_candidate_samples.jsonl)
  - `farm-case-001`: 고온다습 개화기 climate alert window
  - `farm-case-004`: 장마 전후 역병 patch containment window
  - `farm-case-006`: 건조실 postharvest humidity control window
  - `farm-case-008`: stale sensor fault window

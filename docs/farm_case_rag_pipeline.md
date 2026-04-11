# Farm Case RAG Pipeline

이 문서는 실제 농장 운영 로그와 센서 구간을 `farm_case` RAG 지식으로 승격하는 기준을 정의한다. 목적은 공식 재배 기준을 유지하면서도, 우리 농장의 성공/실패 사례를 검색 가능한 운영 지식으로 축적하는 것이다.

## 입력 소스

- 센서 시계열: 온습도, CO2, 광, 배지 함수율, EC, pH, 배액률
- 장치 로그: 관수, 환기, 차광, 난방, 제습, CO2 주입
- AI 판단 로그: query, retrieved chunk, recommended action, approval 결과
- 작업자 로그: 수동 개입, 방제, 수확, 건조, 점검 메모
- 결과 데이터: 회복 여부, 수량, 품질, 병 확산, 저장 손실

## 파이프라인 단계

1. `event_window` 생성  
   이상 알람, 장치 명령, 작업자 개입을 기준으로 전후 6~24시간 센서 구간을 묶는다.
2. `farm_case_candidate` 생성  
   원시 로그를 바로 쓰지 않고 `growth_stage`, `cultivar`, `sensor_tags`, `risk_tags`, `outcome`를 붙인 후보 레코드로 변환한다.
3. 검토 대상 선별  
   아래 조건을 만족할 때만 RAG 후보로 올린다.
   - 결과가 확인됨
   - 센서 품질 플래그가 양호함
   - action과 outcome의 시간 순서가 명확함
   - 개인 정보와 비밀 운영 정보가 제거됨
4. 전문가 리뷰  
   공식 지식과 충돌하는지, farm-specific override로 둘 것인지, 폐기할 것인지 결정한다.
5. RAG 청크 승격  
   승인된 후보만 `source_type: farm_case`로 JSONL 청크를 만든다.
6. 검색 정책 반영  
   기본 검색에서는 `official_master_guideline`을 우선하고, `farm_case`는 동일 품종·동일 작형·동일 계절 조건에서만 가중치를 높인다.

## 필수 메타데이터

- 식별: `case_id`, `farm_id`, `zone_id`
- 재배 맥락: `crop_type`, `cultivar`, `season`, `growth_stage`, `cultivation_type`
- 이벤트 맥락: `event_start_at`, `event_end_at`, `trigger_type`, `action_taken`
- 검색 태그: `sensor_tags`, `risk_tags`, `operation_tags`, `causality_tags`, `visual_tags`
- 결과: `outcome`, `outcome_evidence`, `confidence`, `review_status`
- 추적: `sensor_window_refs`, `operation_log_refs`, `ai_decision_refs`, `reviewer`, `approved_at`

스키마 초안은 [schemas/farm_case_candidate_schema.json](/home/user/pepper-smartfarm-plan-v2/schemas/farm_case_candidate_schema.json)에 둔다.

## 승격 규칙

- `review_status=approved` 전에는 운영 RAG 인덱스에 넣지 않는다.
- `outcome=unknown` 또는 `sensor_quality=bad` 사례는 학습/RAG 둘 다 보류한다.
- 공식 지식과 충돌하면 `trust_level=medium` 이하로 두고 자동 제어 판단에는 직접 쓰지 않는다.
- 같은 원인과 조치가 반복되면 개별 case를 계속 쌓지 말고 `internal_sop`로 승격 후보를 만든다.

## 초기 구현 백로그

1. `farm_case_candidate` JSONL 샘플 10건 작성
2. event window builder 규칙 문서화
3. 승인된 후보를 RAG chunk로 변환하는 스크립트 초안 작성
4. `farm_case` 검색 시 official guideline 우선 reranking 규칙 추가

# RAG Contextual Retrieval Strategy

이 문서는 적고추 전문가 AI Agent가 단일 시점 값이 아니라 최근 3~5일 상태를 포함해 지식을 검색하는 기준을 정리한다.

## 목표

- 순간값 이상과 지속 이상을 구분한다.
- 생육 단계, 작형, 품종, 지역, 최근 작업 이력을 함께 반영한다.
- 같은 증상이라도 원인이 다른 경우 검색 후보를 분리한다.

## 컨텍스트 윈도우

- `6h`: 급격한 온도 상승, 환기 실패, 관수 정지, 결로 급증
- `24h`: 일사 누적, 배액률, VPD, 야간 최저온, 관수 횟수
- `72h`: 고온 지속, 저온 지속, 근권 EC 상승 추세, 병해충 밀도 증가
- `5d`: 정식 후 활착 지연, 장마 지속, 냉해 회복 여부, 착과·착색 지연

## 검색 입력 구성

1. 현재 상태 요약
   - `growth_stage`, `cultivation_type`, `cultivar`, `region`, `season`
2. 센서 특징량
   - 예: `night_temp_min`, `vpd_max`, `substrate_moisture_trend`, `drain_ec_delta`
3. 이벤트 태그
   - 예: `persistent_low_night_temp`, `drain_ec_rising_3d`, `fan_failure`, `heavy_rain_48h`
4. 최근 작업 이력
   - 예: `recent_fertigation_increase`, `recent_pesticide`, `recent_transplant`

## 검색 순서

1. metadata hard filter
   - `growth_stage`, `cultivation_type`, `cultivar`, `region`, `season`, `greenhouse_type`
2. 이벤트 기반 확장 질의
   - 예: `low temp 7 days flowering red fruit ratio`
   - 예: `drain_ec rise root browning slow irrigation`
3. vector + keyword hybrid 검색
4. trust level / source type reranking
5. 최근 5일 추세와 충돌하는 청크 제거

## 이벤트 태그 예시

- `persistent_low_night_temp`: 야간 13℃ 이하가 2일 이상 지속
- `persistent_high_rootzone_ec`: 근권 EC가 3일 연속 상승
- `heat_without_vent_recovery`: 일중 32℃ 이상인데 환기 응답이 없음
- `monsoon_wetness_run`: 강우 또는 고습 조건이 48시간 이상 지속
- `poor_coloration_after_maturity`: 성숙 일수 경과 후에도 착색 지연

## 적용 원칙

- 순간 이상은 `field_case`와 결합해 원인 후보를 넓게 찾는다.
- 지속 이상은 `official_guideline`과 `official_research_report`를 우선한다.
- 방제·약제·가온처럼 위험도가 높은 작업은 `trust_level=high` 결과가 없으면 실행 추천을 보류한다.
- 최근 작업 이력과 상충하는 처방은 `safety-agent`가 차단한다.

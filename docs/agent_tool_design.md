# Agent Tool Design

이 문서는 적고추 전문가 AI Agent가 사용할 도구 인터페이스를 정의한다. 목적은 LLM이 직접 장치를 제어하지 않고, 읽기 도구와 승인 요청 도구를 통해 판단만 수행하게 만드는 것이다.

## 설계 원칙

- 모든 장치 제어는 `policy-engine`과 `execution-gateway` 뒤에서만 수행한다.
- Agent는 먼저 상태 조회와 지식 검색을 수행하고, 마지막에 승인 요청 또는 로그 기록만 한다.
- `sensor_quality`가 `bad`이면 제어형 action 대신 `pause_automation`, `request_human_check`, `create_alert`를 우선한다.
- `citation_required`가 필요한 판단은 검색 chunk를 응답에 반드시 포함한다.

## 필수 도구

| 도구 | 목적 | 입력 | 출력 |
|---|---|---|---|
| `get_zone_state` | 현재 구역 상태 조회 | `farm_id`, `zone_id`, `at` | `state_schema.json` 기반 zone state |
| `search_cultivation_knowledge` | RAG 검색 | `query`, `filters`, `top_k` | chunk id, citation, score, metadata |
| `get_recent_trend` | 최근 5분~72시간 추세 조회 | `zone_id`, `metric`, `window_minutes` | 평균, 변화율, 이상 구간 |
| `get_active_constraints` | 현재 정책/장치 제약 조회 | `zone_id` | hard block, approval, cooldown |
| `estimate_growth_stage` | 생육 단계 보정 | `zone_id`, `state_snapshot` | 추정 단계와 confidence |
| `request_human_approval` | 승인 필요 action 등록 | `proposed_actions`, `risk_level`, `reason` | approval ticket id |
| `log_decision` | 판단 결과 기록 | `decision_payload` | audit log id |

## 선택 도구

| 도구 | 목적 |
|---|---|
| `get_device_readback` | 명령 후 장치 응답 확인 |
| `get_recent_operator_notes` | 작업자 메모와 수동 개입 이력 확인 |
| `get_harvest_candidates` | 비전 기반 수확 후보 목록 조회 |

## Agent별 기본 도구 조합

- `growth-stage-agent`: `get_zone_state`, `estimate_growth_stage`, `search_cultivation_knowledge`
- `climate-agent`: `get_zone_state`, `get_recent_trend`, `get_active_constraints`, `search_cultivation_knowledge`
- `irrigation-agent`: `get_zone_state`, `get_recent_trend`, `search_cultivation_knowledge`
- `nutrient-agent`: `get_zone_state`, `get_recent_trend`, `search_cultivation_knowledge`
- `pest-disease-agent`: `get_zone_state`, `get_recent_operator_notes`, `search_cultivation_knowledge`
- `harvest-drying-agent`: `get_zone_state`, `get_harvest_candidates`, `search_cultivation_knowledge`
- `safety-agent`: `get_zone_state`, `get_active_constraints`, `get_device_readback`
- `report-agent`: `get_zone_state`, `get_recent_operator_notes`, `log_decision`

## 호출 순서

1. `get_zone_state`
2. `get_recent_trend`
3. `get_active_constraints`
4. `search_cultivation_knowledge`
5. `estimate_growth_stage` 필요 시 호출
6. 판단 생성
7. `request_human_approval` 또는 `log_decision`

## 금지 사항

- Agent가 임의로 PLC 명령 형식을 만들지 않는다.
- 검색 근거 없이 기준값을 단정하지 않는다.
- `sensor_quality=bad` 상태에서 자동 실행 action을 직접 생성하지 않는다.
- approval ticket 없이 중위험·고위험 action을 실행 상태로 넘기지 않는다.

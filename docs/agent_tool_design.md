# Agent Tool Design

이 문서는 적고추 전문가 AI Agent가 사용할 도구 인터페이스를 정의한다. 목적은 LLM이 직접 장치를 제어하지 않고 읽기 도구, 승인 요청 도구, 감사 도구를 통해 판단과 요청 envelope만 만들게 하는 것이다.

## 설계 원칙

- 모든 장치 제어는 policy-engine과 execution-gateway 뒤에서만 수행한다.
- Agent는 먼저 상태, 장치, 추세, 제약, RAG 근거를 확인하고 마지막에 승인 요청 또는 로그 기록만 한다.
- sensor_quality가 bad이면 제어형 action 대신 pause_automation, request_human_check, create_alert를 우선한다.
- citation_required가 필요한 판단은 retrieved_context 내부 chunk_id를 citations에 반드시 포함한다.
- request_device_action과 request_robot_task는 실행 envelope 생성 계약이며 PLC 명령 또는 로봇 경로계획을 직접 만들지 않는다.

## 필수 도구

| 도구 | 목적 | 입력 | 출력 | 상태 |
|---|---|---|---|---|
| get_zone_state | 현재 구역 상태 조회 | farm_id, zone_id, at | state schema 기반 zone_state, state_estimate, derived_features | implemented |
| get_device_status | 장치 availability, readback, degraded 상태 조회 | farm_id, zone_id, device_id | device_status, readback_state, degraded, last_command | implemented |
| get_recent_trend | 최근 5분에서 72시간 추세 조회 | zone_id, metric, window_minutes | baseline, delta_10m, delta_30m, trend_summary | implemented |
| get_weather_context | 외부 기상과 예보 context 조회 | farm_id, zone_id, window_hours | weather_context, wind, rain, solar radiation | implemented |
| get_active_constraints | 현재 정책과 장치 제약 조회 | zone_id | manual_override, safe_mode, cooldown, hard_block | implemented |
| estimate_growth_stage | 생육 단계 보정 | zone_id, state_snapshot | growth_stage, confidence | implemented |
| search_cultivation_knowledge | 재배 지식 RAG 검색 | query, filters, top_k | chunk_id, document_id, score, excerpt | implemented |
| search_site_sop | 현장 SOP와 운영 정책 RAG 검색 | query, site_scope, top_k | chunk_id, document_id, score, excerpt | implemented |
| get_retrieval_citations | retrieved_context 기반 citation 생성 | retrieved_context, task_type | citations, retrieval_coverage | implemented |
| request_device_action | 장치 실행 요청 envelope 생성 | recommended_actions, constraints, citations | action_request_id, policy_precheck_status, approval_required | implemented |
| request_robot_task | 로봇 작업 요청 envelope 생성 | robot_tasks, vision_candidates, constraints | robot_task_id, task_status, approval_required | implemented |
| request_human_approval | 승인 필요 action 등록 | proposed_actions, risk_level, reason | approval_ticket_id, approval_status | implemented |
| log_decision | 판단 결과와 검증 결과 기록 | decision_payload | decision_id, audit_path | implemented |

## 선택 도구

| 도구 | 목적 | 상태 |
|---|---|---|
| get_device_readback | 명령 후 장치 응답 확인 | planned |
| get_recent_operator_notes | 작업자 메모와 수동 개입 이력 확인 | planned |
| get_vision_candidates | 비전 기반 수확, 병해, 통로 안전 후보 조회 | planned |
| get_harvest_candidates | 수확 후보 전용 legacy alias | planned |

## Agent별 기본 도구 조합

- growth-stage-agent: get_zone_state, estimate_growth_stage, search_cultivation_knowledge
- climate-agent: get_zone_state, get_device_status, get_weather_context, get_recent_trend, get_active_constraints, search_cultivation_knowledge
- irrigation-agent: get_zone_state, get_device_status, get_recent_trend, get_active_constraints, search_cultivation_knowledge, search_site_sop
- nutrient-agent: get_zone_state, get_recent_trend, search_cultivation_knowledge, request_human_approval
- pest-disease-agent: get_zone_state, get_recent_operator_notes, get_vision_candidates, search_cultivation_knowledge
- harvest-drying-agent: get_zone_state, get_vision_candidates, get_harvest_candidates, search_cultivation_knowledge, request_robot_task
- safety-agent: get_zone_state, get_device_status, get_active_constraints, get_device_readback, request_human_approval
- report-agent: get_zone_state, get_recent_operator_notes, get_retrieval_citations, log_decision

## 호출 순서

1. get_zone_state
2. get_device_status
3. get_weather_context
4. get_recent_trend
5. get_active_constraints
6. search_cultivation_knowledge 또는 search_site_sop
7. get_retrieval_citations
8. estimate_growth_stage 또는 get_vision_candidates 필요 시 호출
9. 판단 생성
10. request_human_approval, request_device_action, request_robot_task, log_decision 중 필요한 envelope 생성

## 금지 사항

- Agent가 임의로 PLC 명령 형식을 만들지 않는다.
- Agent가 로봇 경로, 속도, 조인트 명령을 직접 만들지 않는다.
- 검색 근거 없이 기준값을 단정하지 않는다.
- sensor_quality=bad 상태에서 자동 실행 action을 직접 생성하지 않는다.
- approval ticket 없이 중위험이나 고위험 action을 실행 상태로 넘기지 않는다.
- retrieved_context 밖 chunk_id를 citation으로 만들지 않는다.

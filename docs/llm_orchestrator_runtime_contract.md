# LLM Orchestrator Runtime Contract

이 문서는 todo 9 LLM 오케스트레이터의 호출 흐름, 프롬프트 입력 계약, 도구 계약, 응답 검증 기준을 runtime 기준으로 고정한다. LLM은 판단과 요청 envelope 생성만 담당하며 실제 제어는 policy-engine, execution-gateway, PLC adapter 뒤에서만 수행한다.

## 호출 흐름

### evaluate_zone

1. ops-api POST /decisions/evaluate-zone가 farm_id, zone_id, task_type, zone_state를 받는다.
2. LLMOrchestratorService가 prompt_version을 선택하고 state-estimator payload, active_constraints, weather_context를 user message에 넣는다.
3. local retriever가 task_type, growth_stage, current_state summary, climate/rootzone risk를 query로 검색한다.
4. retrieved_context와 tool_registry를 함께 prompt에 주입한다.
5. champion alias는 ds_v11 frozen FT model id로 해석한다. 기본 개발 검증은 stub provider로 수행한다.
6. 응답은 response_parser에서 JSON object로 파싱하고 실패 시 repair prompt, 최종 실패 시 safe fallback을 사용한다.
7. service._ensure_citations가 citation 누락을 보정한다.
8. policy-engine output validator가 hard safety, citation context, action/robot contract를 1차 정규화한다.
9. response_contract가 JSON only, confidence, retrieval_coverage, follow_up, citation, action parameter, robot task schema를 2차 검증한다.
10. audit log와 validator reason code를 반환하고 ops-api가 decision, approval, event surface에 저장한다.

### event-driven

1. sensor-ingestor 또는 state-estimator가 risk event, stale sensor, communication loss, threshold breach를 만든다.
2. ops-api는 event metadata를 zone_state.current_state와 active_constraints에 합쳐 evaluate_zone 요청으로 변환한다.
3. task_type은 state_judgement, failure_response, forbidden_action 중 하나로 정규화한다.
4. 응답이 medium 이상 risk 또는 approval_required를 포함하면 approval queue와 policy event로 연결한다.
5. execution-gateway는 이벤트 기반 요청도 range, cooldown, duplicate, manual override, safe mode를 다시 검사한다.

### on-demand

1. 운영자가 Web UI 또는 ops-api에서 특정 zone, 기간, 질문 목적을 선택한다.
2. 요청은 task_type state_judgement 또는 action_recommendation으로 들어가며 operator note와 dashboard snapshot을 metadata에 넣는다.
3. LLM은 자동 실행 대신 관찰, 확인, 승인 요청을 우선한다.
4. 결과는 operator review 또는 decision log에 저장하고 승인 없이는 장치 명령으로 승격하지 않는다.

### robot prioritization

1. vision pipeline 또는 robot_candidates API가 후보, maturity, defect, aisle safety, worker clearance를 만든다.
2. task_type robot_task_prioritization으로 zone_state와 vision candidate summary를 전달한다.
3. LLM은 inspect_crop, harvest_candidate_review, skip_area, manual_review 중 하나를 추천한다.
4. response contract는 robot_tasks 배열, task_type enum, candidate_id 또는 target, reason, approval_required 타입을 검증한다.
5. 실제 경로계획과 로봇 제어는 robot controller가 수행하고 LLM은 request_robot_task envelope만 만든다.

### alert summary

1. dashboard 또는 daily intake runner가 alerts, policy_events, approvals, shadow residuals를 모은다.
2. LLM은 report-agent 역할로 요약하되 새로운 장치 제어 action을 만들지 않는다.
3. citation 또는 event id를 포함해 어떤 alert와 residual에 근거했는지 추적 가능하게 한다.
4. 운영자는 summary를 review log로 저장하거나 follow_up으로 다시 분기한다.

### RAG retrieval

1. _retrieve_context가 task_type, growth_stage, current_state summary, heat/rootzone risk를 query로 만든다.
2. 기본 runtime retriever는 비용 없는 keyword 경로다. OpenAI embedding live query는 OPENAI_LIVE_RETRIEVER_SMOKE=1일 때만 smoke에서 수행한다.
3. retrieved_context는 chunk_id, document_id, score, excerpt를 포함해 prompt에 주입된다.
4. _ensure_citations와 policy output validator가 citation 누락이나 context 밖 chunk를 보정한다.
5. response_contract는 retrieved_chunk_ids 밖 citation을 error로 보고한다.

## 프롬프트 계약

- 시스템 프롬프트 소스: scripts/build_openai_sft_datasets.py의 sft_v10 계열 prompt를 prompt_catalog가 로드한다.
- 역할 제한: LLM은 농업 판단, 위험 분류, follow_up, 승인 요청 envelope 작성만 수행한다.
- 안전 원칙: manual override, safe mode, worker present, degraded control path, bad sensor quality가 있으면 자동 제어보다 block, pause, alert, human check를 우선한다.
- RAG 우선: 재배 기준, SOP, 장치 운전 근거는 retrieved_context와 citation을 우선 사용한다.
- 근거 부족: 검색 근거가 부족하거나 센서 품질이 낮으면 confidence를 낮추고 retrieval_coverage를 partial 또는 insufficient로 둔다.
- JSON only: 의사결정 task는 markdown, 설명문, 접두어 없이 JSON object만 반환한다.
- confidence: 0 이상 1 이하 숫자만 허용한다. 애매하면 0.4에서 0.6 구간으로 둔다.
- uncertainty: 불확실한 판단은 risk_level unknown 또는 medium 이상 보수 판단과 follow_up을 함께 낸다.
- follow_up: follow_up 또는 required_follow_up은 비어 있지 않은 배열이어야 하며 type 또는 check_type과 description, note, reason 중 하나를 포함한다.
- citations: retrieval_coverage가 sufficient 또는 partial이면 citations 배열에 retrieved_context 내부 chunk_id를 넣는다.
- 장치 enum 삽입: tool_registry와 schema의 action_type, target_type, parameter enum을 prompt payload에 함께 넣는다.
- constraints 삽입: active_constraints, manual_override, safe_mode, cooldown, degraded path, zone clearance를 user message에 그대로 삽입한다.

## 도구 계약

| 도구 | 상태 | 위험 등급 | runtime 의미 |
|---|---|---|---|
| get_zone_state | implemented | read_only | zone_state, state_estimate, derived_features 조회 |
| get_device_status | implemented | read_only | device_status, readback, degraded 상태 조회 |
| get_recent_trend | implemented | read_only | baseline, delta_10m, delta_30m, trend summary 조회 |
| get_weather_context | implemented | read_only | 외부 기상과 예보 context 조회 |
| get_active_constraints | implemented | read_only | manual override, safe mode, cooldown, hard block 조회 |
| search_cultivation_knowledge | implemented | read_only | 재배 지식 RAG 검색 |
| search_site_sop | implemented | read_only | 현장 SOP와 운영 정책 RAG 검색 |
| get_retrieval_citations | implemented | read_only | retrieved_context 기반 citations와 coverage 생성 |
| estimate_growth_stage | implemented | derived_read_only | state-estimator 생육 단계 추정 사용 |
| get_vision_candidates | planned | read_only | 비전 후보 조회. 현재 contract-only |
| request_device_action | implemented | execution_request | recommended_actions를 실행 요청 envelope로 변환. 직접 PLC 제어 금지 |
| request_robot_task | implemented | approval_gate | robot_tasks를 작업 큐 envelope로 변환. 실제 제어 금지 |
| request_human_approval | implemented | approval_gate | 승인 필요 action을 approval queue에 등록 |
| log_decision | implemented | audit | 판단, validator 결과, citation을 감사 로그에 저장 |

## 응답 검증 매트릭스

| 항목 | 검증 위치 | 실패 처리 |
|---|---|---|
| action_type enum | response_contract, policy output validator | invalid action error 또는 validator 제거 |
| parameter schema | response_contract | range, type, enum error |
| confidence 범위 | response_contract | 0 이상 1 이하가 아니면 error |
| follow_up 필드 | response_contract, validator fallback | 누락 또는 설명 없음 error |
| citations 필드 | _ensure_citations, policy output validator, response_contract | 누락 보정, context 밖 citation error |
| retrieval_coverage | response_contract | enum 누락 또는 invalid error |
| robot task schema | response_contract, policy output validator | task_type, reason, candidate_id/target error |
| natural language leakage | response_parser, response_contract | markdown fence, 접두어, recovered JSON error |
| policy precheck | policy-engine, execution-gateway | block, approval_required, safe mode, audit |

## 검증 명령

- python3 scripts/validate_llm_orchestrator_service.py
- python3 scripts/validate_llm_response_parser.py
- python3 scripts/validate_llm_response_contract.py
- python3 scripts/validate_llm_output_validator_runtime.py
- python3 scripts/run_phase_p_quality_gate.py --skip-postgres-smoke --no-env

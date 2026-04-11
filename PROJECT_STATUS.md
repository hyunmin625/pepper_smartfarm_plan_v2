# 프로젝트 현황 요약

이 문서는 다른 AI/에이전트가 저장소의 목적, 현재 진행 상태, 다음 작업을 빠르게 파악하기 위한 진입점이다.

## 현재 저장소 상태

- 저장소 유형: 구현 코드가 없는 계획/문서 저장소
- 대상 시스템: 적고추(건고추) 온실 스마트팜 운영을 위한 농업용 LLM/제어 시스템
- 현장 상태: 온실 공사 중이며 아직 실측 센서 데이터 수집 전
- 현재 브랜치: `master`
- 원격 저장소: `https://github.com/hyunmin625/pepper_smartfarm_plan_v2.git`
- 현재까지의 작업은 모두 Markdown 문서 중심으로 진행되었다.

## 핵심 시스템 방향

- LLM은 상위 판단 및 계획 엔진으로만 사용한다.
- 실시간 연속 제어는 PLC, 규칙 엔진, PID, 상태기계가 담당한다.
- 모든 실행 명령은 policy-engine과 execution-gateway를 통과해야 한다.
- 로봇암은 LLM이 직접 제어하지 않는다. 비전, 작업계획, 로봇 제어기가 실제 동작을 담당한다.
- 모든 판단, 검색 근거, 실행 결과는 감사 로그로 남겨야 한다.

## RAG + 파인튜닝 하이브리드 결정

현재 계획은 RAG와 파인튜닝을 함께 쓰는 구조로 정리되어 있다.

- RAG 담당: 재배 매뉴얼, 현장 SOP, 품종/지역별 기준, 병해 조건, 장치 운전 기준, 정책 문서
- 파인튜닝 담당: JSON 출력 형식, `action_type` 선택, 안전 거절, follow_up 생성, confidence 표현
- 이유: 자주 바뀌거나 출처 추적이 필요한 지식은 RAG로 관리하고, 반복되는 운영 행동 양식은 파인튜닝으로 안정화하는 것이 적합하다.
- LLM 입력 구성: `state + constraints + retrieved_context + device_status`
- LLM 출력은 policy-engine과 execution-gateway에서 다시 검증한다.

## 주요 문서 역할

- `README.md`: 저장소 목적과 문서 탐색 순서
- `PROJECT_STATUS.md`: 현재 진행 상태, 핵심 결정, 다음 우선순위
- `AI_MLOPS_PLAN.md`: 온실 공사 중 먼저 진행할 AI 모델 준비, 센서 수집 계획, MLOps 루프
- `EXPERT_AI_AGENT_PLAN.md`: 적고추 재배 전주기 전문가 AI Agent 구축 단계
- `PLAN.md`: 전체 목표, 아키텍처, 안전 원칙, RAG+파인튜닝 구조, MVP 범위
- `todo.md`: 세부 작업 목록과 구현 체크리스트
- `docs/rag_next_steps.md`: RAG 데이터 확충, 벡터 검색, 메타데이터 필터, 현장 데이터 환류 과제
- `docs/farm_case_rag_pipeline.md`: 운영 로그와 센서 구간을 `farm_case` RAG로 승격하는 기준과 리뷰 절차
- `docs/farm_case_event_window_builder.md`: 운영 로그를 사건 단위 `event_window`로 묶는 세부 규칙
- `docs/sensor_collection_plan.md`: zone/device/sample_rate 수준의 센서 수집 계획
- `docs/sensor_installation_inventory.md`: zone별 설치 수량, protocol, calibration, model_profile 기준
- `docs/device_profile_registry.md`: 장치 `model_profile`를 `plc-adapter` 실행 계약으로 관리하는 기준
- `docs/plc_adapter_interface_contract.md`: profile 기반 write/readback/ack 인터페이스 계약
- `docs/plc_site_override_map.md`: 현장 controller/channel binding을 profile과 분리 관리하는 기준
- `docs/plc_runtime_endpoint_config.md`: controller endpoint를 환경 변수로 주입하는 기준
- `docs/plc_channel_address_registry.md`: `channel_ref -> Modbus address` registry 기준
- `docs/device_command_mapping_matrix.md`: 장치별 action/parameter/encoder/ack 매핑 기준
- `docs/plc_tag_modbus_tcp_adapter.md`: `plc_tag_modbus_tcp` adapter skeleton 범위와 제약
- `docs/execution_gateway_command_contract.md`: execution-gateway가 넘기는 저수준 device command 계약
- `docs/sensor_ingestor_config_spec.md`: poller profile, connection, binding group 기준
- `docs/sensor_quality_rules_pseudocode.md`: `quality_flag`와 automation gate 규칙
- `docs/sensor_ingestor_runtime_flow.md`: parser -> normalizer -> publish 실행 흐름
- `docs/operational_scenarios.md`: 정상/이상/안전 이벤트 시나리오 목록
- `docs/safety_requirements.md`: 인터록, estop, 수동/자동 전환, 승인/금지 액션 기준
- `docs/dataset_taxonomy.md`: 학습/eval 데이터의 task family 분류 기준
- `docs/training_data_format.md`: seed JSONL 입력/출력 포맷과 템플릿 기준
- `docs/data_curation_rules.md`: 샘플/eval 정제와 정규화 규칙
- `docs/offline_agent_runner_spec.md`: 실측 데이터 없이 Agent 판단을 검증하는 offline runner 요구사항
- `docs/mlops_registry_design.md`: dataset/prompt/model/eval/retrieval profile 버전 관리 규칙
- `docs/shadow_mode_report_format.md`: shadow mode 승격 판단 리포트 형식
- `schedule.md`: 8주 실행 일정과 단계별 완료 기준
- `WORK_LOG.md`: 진행한 작업, 커밋, 조사 근거 기록
- `AGENTS.md`: 기여자와 AI 에이전트 작업 규칙

## 현재 완료된 작업

- Git 저장소 초기화 및 GitHub 원격 연결
- `AGENTS.md` 한글 기여자 가이드 작성
- 계획 문서 전체 분석
- RAG + 파인튜닝 하이브리드 구조 조사
- `PLAN.md`, `todo.md`, `schedule.md`에 하이브리드 구조 반영
- `README.md`, `PROJECT_STATUS.md`, `WORK_LOG.md` 작성
- 주요 계획 문서와 `AGENTS.md`에 문서 링크 반영
- 온실 공사중 전제를 반영해 AI 준비 구축을 최우선 단계로 재정렬
- 적고추 재배 전주기 전문가 AI Agent 구축 계획 수립
- RAG 구축 시작: source inventory, seed chunks, expert knowledge map, sensor judgement matrix 작성
- 전문가 AI Agent 입력/출력 계약 초안 작성: state, feature, sensor quality, action schema
- 전문가 판단 초기 평가셋 작성: 정상, 고온, 근권, 양액, 센서불량, 병해, 수확/건조, 안전정책 케이스
- 파인튜닝 후보 seed 샘플 작성: 상태판단 5개, 금지행동 5개
- RAG 인덱싱 설계와 로컬 JSON 인덱스 빌드 스크립트 작성
- RAG 검색 smoke test 스크립트 작성 및 6개 쿼리 통과
- 농촌진흥청 PDF 기반 RAG 정밀 보강 완료: 육묘·재해·영양장애·비가림 구조 기반 지식과 후속 웹 공식 자료 보강까지 반영
- 농촌진흥청 PDF, 작물기술정보, 작형 일정, 품종 기준, 현장 기술지원, 미숙퇴비·배수불량·과차광·육묘 장해·첫서리·노화묘·품종 민감성 사례 추가로 RAG seed chunk 141개 확장 완료
- RAG-SRC-001 병해충·토양병·세균병·굴파리·뿌리혹선충·농약 안전사용 장 추가 추출로 균핵병·시들음병·잿빛곰팡이병·흰별무늬병·흰비단병·무름병·세균점무늬병·잎굴파리·뿌리혹선충·잔류농약 규칙을 보강해 RAG seed chunk 219개 확장 완료
- RAG 검색 품질 평가 확장: smoke test 98건, retrieval eval 110건 검증 완료
- 로컬 TF-IDF + SVD vector search PoC 유지: local hybrid retrieval eval 110건 hit rate 1.0, MRR 0.9955
- ChromaDB persistent vector store 재검증 완료: local-backed Chroma retrieval eval 110건 hit rate 1.0, MRR 0.9955
- OpenAI embedding 기반 Chroma collection 재검증 완료: retrieval eval 110건 hit rate 1.0, MRR 0.9803
- 110개 retrieval eval 재검증 결과 local vector와 local-backed Chroma가 동일 MRR 0.9955로 가장 높고, keyword-only는 0.9909, OpenAI-backed Chroma는 0.9803을 유지
- `region`, `season`, `cultivar`, `greenhouse_type` 메타데이터가 JSON index와 검색 필드에 실제 반영되도록 `scripts/build_rag_index.py`, `scripts/search_rag_index.py` 보정 완료
- multi-turn contextual retrieval 전략 문서화 완료: `docs/rag_contextual_retrieval_strategy.md`
- `farm_case` RAG 환류 파이프라인 초안과 후보 스키마 작성: `docs/farm_case_rag_pipeline.md`, `schemas/farm_case_candidate_schema.json`
- `farm_case_candidate` 샘플 10건 작성: `data/examples/farm_case_candidate_samples.jsonl`
- `farm_case` 후보 검증 스크립트와 event window 세부 규칙 추가: `scripts/validate_farm_case_candidates.py`, `docs/farm_case_event_window_builder.md`
- 승인된 `farm_case` 후보를 RAG 청크로 변환하는 초안 추가: `scripts/build_farm_case_rag_chunks.py`, `data/rag/farm_case_seed_chunks.jsonl`
- `farm_case` 혼합 인덱스에서 official guideline 우선 정렬 guardrail 구현: `scripts/search_rag_index.py`, `evals/rag_official_priority_eval_set.jsonl`
- Phase -1 설계 산출물 보강 완료: offline runner spec, MLOps registry 설계, shadow mode report format, 합성 센서 시나리오 추가
- 센서 수집 계획 상세화 완료: `docs/sensor_collection_plan.md`, `schemas/sensor_catalog_schema.json`, `data/examples/sensor_catalog_seed.json`
- 센서 현장형 인벤토리 초안 완료: `docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`에 설치 수량 가정, protocol, calibration, model_profile 반영
- `sensor-ingestor` 설정 포맷과 poller profile 초안 완료: `docs/sensor_ingestor_config_spec.md`, `schemas/sensor_ingestor_config_schema.json`, `data/examples/sensor_ingestor_config_seed.json`, `scripts/validate_sensor_ingestor_config.py`
- 센서 품질 규칙과 `sensor-ingestor` runtime flow 초안 완료: `docs/sensor_quality_rules_pseudocode.md`, `docs/sensor_ingestor_runtime_flow.md`
- 운영 시나리오 14건 정리 완료: `data/examples/synthetic_sensor_scenarios.jsonl`, `docs/operational_scenarios.md`, `scripts/validate_synthetic_scenarios.py`
- 안전 요구사항 정리 완료: `docs/safety_requirements.md`
- `sensor-ingestor` MVP skeleton 추가: `sensor-ingestor/main.py`, `sensor-ingestor/sensor_ingestor/runtime.py`, `sensor-ingestor/sensor_ingestor/config.py`
- dry-run 실행과 `/healthz`, `/metrics` endpoint 응답 검증 완료
- `Device Profile` registry/schema 초안 추가: `docs/device_profile_registry.md`, `schemas/device_profile_registry_schema.json`, `data/examples/device_profile_registry_seed.json`
- `model_profile -> profile_id` cross-check 검증기 추가: `scripts/validate_device_profile_registry.py`
- `plc-adapter` interface contract와 mock skeleton 추가: `docs/plc_adapter_interface_contract.md`, `plc-adapter/plc_adapter/interface.py`, `plc-adapter/plc_adapter/mock_adapter.py`, `plc-adapter/demo.py`
- zone 관수밸브와 원수 메인 밸브를 서로 다른 `Device Profile`로 분리해 인터록/ack 정책을 독립 관리하도록 보정
- `site override address map` seed/schema 추가: `docs/plc_site_override_map.md`, `schemas/device_site_override_schema.json`, `data/examples/device_site_override_seed.json`
- `device_id -> profile -> controller/channel` resolver 추가: `plc-adapter/plc_adapter/device_catalog.py`, `plc-adapter/plc_adapter/site_overrides.py`, `plc-adapter/plc_adapter/resolver.py`
- `scripts/validate_device_site_overrides.py`로 controller/channel binding 정합성 검증 추가
- PLC runtime endpoint override 기준 추가: `docs/plc_runtime_endpoint_config.md`, `.env.example`, `plc-adapter/plc_adapter/runtime_config.py`
- `plc_tag://...` channel ref parser 추가: `plc-adapter/plc_adapter/channel_refs.py`
- `channel_ref -> Modbus address` registry 추가: `docs/plc_channel_address_registry.md`, `schemas/device_channel_address_registry_schema.json`, `data/examples/device_channel_address_registry_seed.json`
- site override 기반 placeholder address map generator/validator 추가: `scripts/build_device_channel_address_registry.py`, `scripts/validate_device_channel_address_registry.py`
- `plc_tag_modbus_tcp` adapter payload에 `write_channel_address`, `read_channel_addresses`, `transport_*` fields 추가
- adapter가 write/readback 시 logical ref가 아니라 transport ref 기준으로 in-memory transport를 호출하도록 보강
- `plc_tag_modbus_tcp` adapter skeleton 추가: `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`, `plc-adapter/plc_adapter/transports.py`, `plc-adapter/plc_adapter/codecs.py`
- in-memory transport 기준 connect/reconnect, write/readback, timeout/retry, health check, result mapping 검증 완료
- `execution-gateway -> plc-adapter` command contract 추가: `schemas/device_command_request_schema.json`, `data/examples/device_command_request_samples.jsonl`, `scripts/validate_device_command_requests.py`
- 장치별 command mapping sample 8건과 실행 validator 추가: `docs/device_command_mapping_matrix.md`, `data/examples/device_command_mapping_samples.jsonl`, `scripts/validate_device_command_mappings.py`
- 대표 장치 8건에 대해 `adapter.write_device_command()` 경로 검증 완료: fan, shade, vent, irrigation valve, heater, co2, fertigation, source water valve
- 도메인 데이터 분류/포맷/정제 규칙 정리 완료: `docs/dataset_taxonomy.md`, `docs/training_data_format.md`, `docs/data_curation_rules.md`
- 행동추천/장애대응/로봇우선순위/알람 seed와 eval seed 추가: `data/examples/*`, `evals/*_eval_set.jsonl`
- 학습/eval JSONL 검증 스크립트 추가: `scripts/validate_training_examples.py`
- Chroma collection/manifest를 backend별로 분리: `pepper_expert_chunks_local`, `pepper_expert_chunks_openai`
- 응답 citation coverage 검증 스크립트 추가: `scripts/validate_response_citations.py`
- retrieval weight 튜닝 스크립트 추가: `scripts/tune_rag_weights.py`
- RAG 보완 핵심 과제 문서화: 데이터 100~200개 확장, vector store 도입, 필터 고도화, 현장 사례 RAG화

## 다음 우선순위

1. `sensor-ingestor` MQTT publisher와 timeseries writer 실제 backend 연결
2. 긴급 정지 명령과 수동 override 명령을 별도 contract로 분리
3. `plc_tag_modbus_tcp`를 실제 TCP/Modbus client와 실IP/실주소 테이블에 연결
4. `execution-gateway` command normalizer와 duplicate/cooldown/policy 재평가 단계를 구현
4. `data/examples` seed를 task별 20건 이상으로 확장
5. retrieval 결과를 고정 리포트와 회귀 기준으로 관리하는 문서/스크립트 보강
6. hard block 정책 10개와 approval 정책 10개 작성

## 주의할 점

- 온실 공사 완료 전에는 장치 제어 구현보다 AI 준비와 센서 수집 계획을 우선한다.
- 센서 품질 플래그 없이 데이터를 학습에 반영하지 않는다.
- 정책 엔진 없이 자동화를 진행하지 않는다.
- execution-gateway 없이 PLC 연결을 진행하지 않는다.
- RAG 검색 품질 기준 없이 하이브리드 판단을 운영에 사용하지 않는다.
- 자주 바뀌는 재배 기준을 파인튜닝 데이터에 직접 암기시키지 않는다.
- Shadow Mode → Approval Mode → Limited Auto Mode 순서를 지킨다.

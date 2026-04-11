# Pepper Smartfarm Plan V2

적고추(건고추) 온실 스마트팜 운영을 위한 농업용 LLM/제어 시스템 개발 계획 저장소입니다.

현재 이 저장소는 구현 코드가 아니라 계획, 일정, 작업 로그를 관리하는 문서 저장소입니다.

## 빠른 시작

다른 AI/에이전트는 아래 순서로 문서를 읽으면 됩니다.

1. `PROJECT_STATUS.md`: 현재 진행 상태, 핵심 결정, 다음 우선순위
2. `AI_MLOPS_PLAN.md`: 온실 공사 중 선행할 AI 모델 준비와 MLOps 흐름
3. `EXPERT_AI_AGENT_PLAN.md`: 적고추 재배 전주기 전문가 AI Agent 구축 단계
4. `PLAN.md`: 전체 시스템 목표, 아키텍처, 안전 원칙
5. `schedule.md`: 개정 실행 순서와 8주 일정
6. `todo.md`: 세부 작업 체크리스트
7. `WORK_LOG.md`: 진행한 작업과 커밋 이력
8. `AGENTS.md`: 문서 작성, 커밋, 보안, 작업 규칙

## 핵심 방향

- LLM은 상위 판단과 계획만 담당한다.
- 실시간 제어는 PLC, 정책 엔진, 실행 게이트, 상태기계가 담당한다.
- RAG는 재배 매뉴얼, 현장 SOP, 정책 문서처럼 바뀔 수 있는 지식을 담당한다.
- 파인튜닝은 JSON 출력, `action_type` 선택, 안전 거절, follow_up 같은 운영 행동 양식을 담당한다.
- 모든 실행은 policy-engine과 execution-gateway를 통과해야 한다.

## 현재 진행 상황

현재는 온실 공사 중인 구현 전 기획 단계이지만, AI 준비와 RAG 기반은 상당 부분 구체화되었습니다.

- Phase -1 AI 준비 구축 및 MLOps 기반 설계: `설계 기준 완료`
- 센서 수집 계획 상세화: `zone/device/sample_rate` 기준 정리 완료
- 센서 현장형 인벤토리 초안: 설치 수량, protocol, calibration, model_profile 반영 완료
- `sensor-ingestor` 설정 포맷 초안: poller profile, connection, binding group, publish target, health config 반영 완료
- 센서 품질 규칙과 `sensor-ingestor` runtime flow 초안 완료
- 운영 시나리오 14건과 안전 요구사항 문서화 완료
- `sensor-ingestor` 코드 skeleton 추가: dry-run poller, parser, normalizer, `/healthz`, `/metrics` 확인 완료
- `Device Profile` registry와 `plc-adapter` interface contract 추가 완료
- `plc-adapter` mock skeleton 추가: profile 기반 parameter validation, payload build, readback, ack evaluation 확인 완료
- `site override address map`과 `device_id -> profile -> controller/channel` resolver 추가 완료
- `plc-adapter` runtime endpoint override와 channel ref parser 추가 완료
- `logical channel ref -> Modbus address registry -> transport ref` 해석 경로 추가 완료
- `plc_tag_modbus_tcp` adapter skeleton 추가: transport, codec, timeout/retry, health check, result mapping 확인 완료
- 대표 장치 8건 command mapping 검증 완료: fan, shade, vent, irrigation valve, heater, CO2, fertigation, source water valve
- `execution-gateway -> plc-adapter` 저수준 command contract와 샘플/validator 추가 완료
- 도메인 데이터 taxonomy/format/curation 기준 추가 완료
- RAG seed chunk: `219개` 구축 완료
- 검색 평가셋: `110개` case로 확장 완료
- smoke test: `98건` 통과
- 검색 방식 검증 완료:
  - keyword-only: hit rate `1.0`, MRR `0.9909`
  - local TF-IDF + SVD: hit rate `1.0`, MRR `0.9955`
  - Chroma local: hit rate `1.0`, MRR `0.9955`
  - Chroma OpenAI embedding: hit rate `1.0`, MRR `0.9803`
- multi-turn contextual retrieval 전략 문서화 완료
- `region / season / cultivar / greenhouse_type` metadata filter가 JSON index와 search path에 실제 반영되도록 수정 완료
- `farm_case` 운영 로그 환류 초안 작성 완료:
  - `docs/farm_case_rag_pipeline.md`
  - `schemas/farm_case_candidate_schema.json`
- `farm_case_candidate` 샘플 10건, event window 규칙, 검증 스크립트 추가 완료:
  - `data/examples/farm_case_candidate_samples.jsonl`
  - `docs/farm_case_event_window_builder.md`
  - `scripts/validate_farm_case_candidates.py`
- 승인된 `farm_case` 후보를 RAG 청크로 변환하는 초안 추가 완료:
  - `scripts/build_farm_case_rag_chunks.py`
  - `data/rag/farm_case_seed_chunks.jsonl`
- `farm_case`가 포함된 혼합 인덱스에서 공식 지침 우선 정렬 가드레일 구현 완료:
  - `scripts/search_rag_index.py`
  - `evals/rag_official_priority_eval_set.jsonl`

## 현재 핵심 산출물

- `data/rag/pepper_expert_seed_chunks.jsonl`: 적고추 전주기 전문가 지식 219개 청크
- `artifacts/rag_index/pepper_expert_index.json`: 로컬 RAG 인덱스
- `docs/rag_indexing_plan.md`: 인덱싱, 검색, 평가 방식
- `docs/rag_contextual_retrieval_strategy.md`: 최근 3~5일 상태를 반영한 contextual retrieval 전략
- `docs/rag_next_steps.md`: 남은 보강 과제
- `docs/sensor_collection_plan.md`: zone, sensor, device, sample_rate, quality_flag 기준
- `docs/sensor_installation_inventory.md`: zone별 설치 수량, protocol, calibration, model_profile 기준
- `docs/sensor_ingestor_config_spec.md`: `sensor-ingestor` 설정 계약과 poller profile 기준
- `docs/sensor_quality_rules_pseudocode.md`: `quality_flag` 우선순위와 automation gate 규칙
- `docs/sensor_ingestor_runtime_flow.md`: parser -> normalizer -> publish 실행 흐름
- `docs/device_profile_registry.md`: `model_profile`를 `plc-adapter` 실행 계약으로 쓰는 기준
- `docs/plc_adapter_interface_contract.md`: profile 기반 write/readback/ack 인터페이스 계약
- `docs/plc_site_override_map.md`: profile과 실제 현장 PLC 채널을 분리하는 site override 기준
- `docs/plc_runtime_endpoint_config.md`: controller endpoint를 환경 변수로 주입하는 기준
- `docs/plc_channel_address_registry.md`: logical channel ref를 Modbus 주소로 해석하는 기준
- `docs/plc_tag_modbus_tcp_adapter.md`: `plc_tag_modbus_tcp` adapter skeleton과 제약 사항
- `docs/device_command_mapping_matrix.md`: 장치별 action/parameter/encoder/ack 매핑 기준
- `docs/execution_gateway_command_contract.md`: execution-gateway가 넘기는 device command request 계약
- `data/examples/device_profile_registry_seed.json`: 장치 타입별 `Device Profile` seed registry
- `data/examples/device_site_override_seed.json`: `gh-01` 예시 controller/channel binding seed
- `data/examples/device_channel_address_registry_seed.json`: `channel_ref -> Modbus address` seed registry
- `data/examples/device_command_mapping_samples.jsonl`: 장치별 대표 명령 sample 8건
- `docs/operational_scenarios.md`: 정상/이상/안전 이벤트 운영 시나리오 목록
- `docs/safety_requirements.md`: 인터록, estop, 수동/자동 전환, 승인/금지 액션 기준
- `sensor-ingestor/`: `sensor-ingestor` 서비스 skeleton과 dry-run 진입점
- `plc-adapter/`: device profile registry를 읽는 mock adapter skeleton
- `plc-adapter/plc_adapter/resolver.py`: `device_id`에서 profile/controller/channel을 resolve하는 경로
- `plc-adapter/plc_adapter/channel_refs.py`: `plc_tag://...` ref parser
- `plc-adapter/plc_adapter/runtime_config.py`: PLC endpoint runtime override resolver
- `plc-adapter/plc_adapter/channel_address_registry.py`: logical ref를 transport address로 해석하는 registry loader
- `plc-adapter/plc_adapter/plc_tag_modbus_tcp.py`: `plc_tag_modbus_tcp` adapter runtime skeleton
- `plc-adapter/plc_adapter/transports.py`: transport interface와 in-memory transport
- `plc-adapter/plc_adapter/codecs.py`: encoder/decoder registry
- `docs/dataset_taxonomy.md`: 학습/eval 데이터 분류 체계
- `docs/training_data_format.md`: seed JSONL 포맷과 템플릿 기준
- `docs/data_curation_rules.md`: 데이터 정제와 정규화 규칙
- `docs/offline_agent_runner_spec.md`: offline runner 요구사항
- `docs/mlops_registry_design.md`: dataset/prompt/model/eval registry 규칙
- `docs/shadow_mode_report_format.md`: shadow mode 평가 리포트 형식
- `docs/farm_case_rag_pipeline.md`: 운영 로그를 `farm_case` RAG로 승격하는 절차
- `docs/farm_case_event_window_builder.md`: 운영 로그를 사건 단위 `event_window`로 묶는 규칙
- `data/rag/farm_case_seed_chunks.jsonl`: 승인된 `farm_case` 후보를 변환한 RAG 청크 샘플
- `evals/rag_official_priority_eval_set.jsonl`: `farm_case` 혼합 인덱스에서 공식 지침 우선 정렬 회귀셋
- `scripts/build_rag_index.py`, `scripts/search_rag_index.py`: 기본 인덱싱/검색
- `scripts/build_chroma_index.py`: ChromaDB 기반 vector index 생성
- `scripts/evaluate_rag_retrieval.py`, `scripts/rag_smoke_test.py`: 검색 회귀 검증
- `scripts/validate_training_examples.py`: 학습/eval JSONL 구조 검증
- `scripts/validate_farm_case_candidates.py`: `farm_case` 후보 JSONL 구조 검증
- `scripts/validate_sensor_ingestor_config.py`: `sensor-ingestor` 설정과 catalog coverage 검증
- `scripts/validate_device_profile_registry.py`: device catalog와 action schema를 기준으로 profile registry 정합성 검증
- `scripts/validate_device_site_overrides.py`: site override가 catalog/profile/controller와 맞는지 검증
- `scripts/build_device_channel_address_registry.py`: site override 기반 placeholder Modbus address map 생성
- `scripts/validate_device_channel_address_registry.py`: channel address registry가 site override와 맞는지 검증
- `scripts/validate_device_command_requests.py`: device command request가 action/catalog/profile 계약과 맞는지 검증
- `scripts/validate_device_command_mappings.py`: 장치별 명령 sample을 실제 adapter 경로로 실행 검증
- `scripts/validate_synthetic_scenarios.py`: 합성 운영 시나리오 JSONL 검증
- `scripts/build_farm_case_rag_chunks.py`: 승인된 `farm_case` 후보를 RAG chunk JSONL로 변환

## 다음 우선순위

1. `sensor-ingestor` MQTT publisher와 timeseries writer 실제 backend 연결
2. `plc_tag_modbus_tcp`를 실제 TCP/Modbus client와 실IP/실주소 테이블에 연결
3. task별 학습 seed를 20건 이상으로 확장
4. retrieval 고정 리포트와 case regression 관리 방식 정리
5. hard block 정책 10개와 approval 정책 10개 작성

제어 시스템 구현은 센서 수집 계획과 AI 준비가 더 진행된 뒤 시작합니다.

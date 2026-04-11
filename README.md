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
- `docs/operational_scenarios.md`: 정상/이상/안전 이벤트 운영 시나리오 목록
- `docs/safety_requirements.md`: 인터록, estop, 수동/자동 전환, 승인/금지 액션 기준
- `sensor-ingestor/`: `sensor-ingestor` 서비스 skeleton과 dry-run 진입점
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
- `scripts/validate_synthetic_scenarios.py`: 합성 운영 시나리오 JSONL 검증
- `scripts/build_farm_case_rag_chunks.py`: 승인된 `farm_case` 후보를 RAG chunk JSONL로 변환

## 다음 우선순위

1. `sensor-ingestor` MQTT publisher와 timeseries writer 실제 backend 연결
2. task별 학습 seed를 20건 이상으로 확장
3. retrieval 고정 리포트와 case regression 관리 방식 정리
4. hard block 정책 10개와 approval 정책 10개 작성

제어 시스템 구현은 센서 수집 계획과 AI 준비가 더 진행된 뒤 시작합니다.

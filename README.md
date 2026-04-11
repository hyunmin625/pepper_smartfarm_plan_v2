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

## 현재 핵심 산출물

- `data/rag/pepper_expert_seed_chunks.jsonl`: 적고추 전주기 전문가 지식 219개 청크
- `artifacts/rag_index/pepper_expert_index.json`: 로컬 RAG 인덱스
- `docs/rag_indexing_plan.md`: 인덱싱, 검색, 평가 방식
- `docs/rag_contextual_retrieval_strategy.md`: 최근 3~5일 상태를 반영한 contextual retrieval 전략
- `docs/rag_next_steps.md`: 남은 보강 과제
- `docs/sensor_collection_plan.md`: zone, sensor, device, sample_rate, quality_flag 기준
- `docs/sensor_installation_inventory.md`: zone별 설치 수량, protocol, calibration, model_profile 기준
- `docs/dataset_taxonomy.md`: 학습/eval 데이터 분류 체계
- `docs/training_data_format.md`: seed JSONL 포맷과 템플릿 기준
- `docs/data_curation_rules.md`: 데이터 정제와 정규화 규칙
- `docs/offline_agent_runner_spec.md`: offline runner 요구사항
- `docs/mlops_registry_design.md`: dataset/prompt/model/eval registry 규칙
- `docs/shadow_mode_report_format.md`: shadow mode 평가 리포트 형식
- `docs/farm_case_rag_pipeline.md`: 운영 로그를 `farm_case` RAG로 승격하는 절차
- `scripts/build_rag_index.py`, `scripts/search_rag_index.py`: 기본 인덱싱/검색
- `scripts/build_chroma_index.py`: ChromaDB 기반 vector index 생성
- `scripts/evaluate_rag_retrieval.py`, `scripts/rag_smoke_test.py`: 검색 회귀 검증
- `scripts/validate_training_examples.py`: 학습/eval JSONL 구조 검증

## 다음 우선순위

1. `sensor-ingestor` 설정 파일 포맷과 poller profile 초안 작성
2. `farm_case_candidate` JSONL 샘플 10건 작성
3. task별 학습 seed를 20건 이상으로 확장
4. `farm_case_candidate` JSONL 샘플 10건 작성
5. retrieval 고정 리포트와 case regression 관리 방식 정리

제어 시스템 구현은 센서 수집 계획과 AI 준비가 더 진행된 뒤 시작합니다.

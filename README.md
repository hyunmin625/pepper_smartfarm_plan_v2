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

- RAG seed chunk: `100개` 구축 완료
- 검색 평가셋: `40개` case로 확장 완료
- 검색 방식 검증 완료:
  - keyword-only: hit rate `1.0`, MRR `0.975`
  - local TF-IDF + SVD: hit rate `1.0`, MRR `1.0`
  - Chroma local: hit rate `1.0`, MRR `1.0`
  - Chroma OpenAI embedding: hit rate `1.0`, MRR `1.0`
- `farm_case` 운영 로그 환류 초안 작성 완료:
  - `docs/farm_case_rag_pipeline.md`
  - `schemas/farm_case_candidate_schema.json`

## 현재 핵심 산출물

- `data/rag/pepper_expert_seed_chunks.jsonl`: 적고추 전주기 전문가 지식 100개 청크
- `artifacts/rag_index/pepper_expert_index.json`: 로컬 RAG 인덱스
- `docs/rag_indexing_plan.md`: 인덱싱, 검색, 평가 방식
- `docs/rag_next_steps.md`: 남은 보강 과제
- `docs/farm_case_rag_pipeline.md`: 운영 로그를 `farm_case` RAG로 승격하는 절차
- `scripts/build_rag_index.py`, `scripts/search_rag_index.py`: 기본 인덱싱/검색
- `scripts/build_chroma_index.py`: ChromaDB 기반 vector index 생성
- `scripts/evaluate_rag_retrieval.py`, `scripts/rag_smoke_test.py`: 검색 회귀 검증

## 다음 우선순위

1. RAG 지식 청크를 `200개` 수준까지 확장
2. 품종별 기준, 지역별 월별 작업, 기상 재해 대응 지식 추가
3. `farm_case_candidate` JSONL 샘플 10건 작성
4. 최근 3~5일 상태를 반영하는 multi-turn contextual retrieval 설계
5. hard block 정책과 approval 정책 구체화

제어 시스템 구현은 센서 수집 계획과 AI 준비가 더 진행된 뒤 시작합니다.

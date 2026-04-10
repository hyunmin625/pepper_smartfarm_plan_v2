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

## 다음 우선순위

1. `evals/expert_judgement_eval_set.jsonl` 초안 작성
2. `data/examples/state_judgement_samples.jsonl` 작성
3. `data/examples/forbidden_action_samples.jsonl` 작성
4. `data/rag/pepper_expert_seed_chunks.jsonl` 확장
5. RAG vector store 인덱싱 스크립트 설계
6. hard block 정책 10개와 approval 정책 10개 작성
7. offline agent runner spec 작성
8. schema validation test 계획 작성

## 주의할 점

- 온실 공사 완료 전에는 장치 제어 구현보다 AI 준비와 센서 수집 계획을 우선한다.
- 센서 품질 플래그 없이 데이터를 학습에 반영하지 않는다.
- 정책 엔진 없이 자동화를 진행하지 않는다.
- execution-gateway 없이 PLC 연결을 진행하지 않는다.
- RAG 검색 품질 기준 없이 하이브리드 판단을 운영에 사용하지 않는다.
- 자주 바뀌는 재배 기준을 파인튜닝 데이터에 직접 암기시키지 않는다.
- Shadow Mode → Approval Mode → Limited Auto Mode 순서를 지킨다.

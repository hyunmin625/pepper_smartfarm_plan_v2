# 작업 로그

이 문서는 저장소에서 진행한 주요 변경 작업과 의사결정 이력을 기록한다.

## 2026-04-10

### 저장소 이력관리 초기화
- 로컬 Git 저장소를 초기화했다.
- GitHub 원격 저장소를 연결했다: `https://github.com/hyunmin625/pepper_smartfarm_plan_v2.git`
- `.codex` 로컬 파일을 제외하기 위해 `.gitignore`를 추가했다.
- 초기 계획 문서와 가이드 문서를 첫 커밋으로 등록하고 `origin/master`에 푸시했다.
- 커밋: `3a82436 Initial project planning documents`

### 기여자 가이드 작성 및 한글화
- `AGENTS.md`를 저장소 기여자 가이드로 작성했다.
- 이후 저장소 문서 성격에 맞춰 한글로 다시 작성했다.
- 포함 내용: 프로젝트 구조, 개발 명령, 명명 규칙, 테스트 기준, 커밋/PR 기준, 보안 주의사항
- 커밋: `fba81c3 Translate repository guide to Korean`

### 계획 문서 분석
- `PLAN.md`, `todo.md`, `schedule.md` 전체 구조를 분석했다.
- 현재 저장소가 구현 코드가 아닌 기획 문서 저장소임을 확인했다.
- 핵심 방향을 다음과 같이 정리했다.
  - LLM은 상위 판단 및 계획 엔진으로 사용한다.
  - 실제 장치 제어는 PLC, 정책 엔진, 실행 게이트가 담당한다.
  - 자동화는 shadow mode, approval mode, limited auto mode 순서로 진행한다.
  - 모든 판단과 실행은 감사 로그로 남긴다.

### RAG + 파인튜닝 하이브리드 구조 조사 및 계획 반영
- 적고추(건고추) 온실 스마트팜 운영용 LLM에 RAG와 파인튜닝을 함께 사용하는 구조의 타당성을 검토했다.
- 결론: 하이브리드 구조가 적합하다.
  - RAG는 재배 매뉴얼, 현장 SOP, 품종/지역별 기준, 정책 문서처럼 자주 바뀌거나 출처 추적이 필요한 지식을 담당한다.
  - 파인튜닝은 JSON 출력, action_type 선택, 안전 거절, follow_up, confidence 표현 등 반복 운영 행동 양식을 담당한다.
- `PLAN.md`에 하이브리드 타당성, RAG 검색 설계, Vector Store/Vector DB, `rag-retriever`, citation 로그 구조를 추가했다.
- `todo.md`에 RAG 지식베이스 구축, 검색 품질 평가, RAG 도구 함수, citation 검증, 통합/E2E 테스트 항목을 추가했다.
- `schedule.md`에 Week 1 RAG 범위 확정, Week 2 vector store PoC, Week 5 RAG 근거 결합 작업을 추가했다.
- 참고 근거:
  - OpenAI Retrieval guide: https://platform.openai.com/docs/guides/retrieval
  - OpenAI File search guide: https://platform.openai.com/docs/guides/tools-file-search/
  - OpenAI Fine-tuning guide: https://platform.openai.com/docs/guides/fine-tuning
  - Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks: https://arxiv.org/abs/2005.11401
- 커밋: `06dde64 Add hybrid RAG fine-tuning plan`

### AI/에이전트용 현황 문서 정리
- 다른 AI가 저장소 목적과 진행상황을 빠르게 파악할 수 있도록 `PROJECT_STATUS.md`를 추가했다.
- 일반 진입점 역할을 위해 `README.md`를 추가했다.
- `PLAN.md`, `todo.md`, `schedule.md`, `AGENTS.md`에 `README.md`, `PROJECT_STATUS.md`, `WORK_LOG.md` 링크를 반영했다.
- 문서 탐색 순서를 `README.md` → `PROJECT_STATUS.md` → `PLAN.md` → `schedule.md` → `todo.md` → `WORK_LOG.md` → `AGENTS.md`로 정리했다.

### 온실 공사중 전제 및 AI/MLOps 선행 계획 반영
- 온실이 아직 공사 중이며 실측 센서 데이터가 없다는 전제를 계획에 반영했다.
- 개발 순서를 `AI 준비 구축 → 센서 수집 계획 보강 → 센서 수집 구현 → 통합 제어 시스템 개발 계획 → 통합 제어 시스템 구현 → 사용자 UI 대시보드 개발 → AI 모델과 통합 제어 시스템 연결`로 개정했다.
- `AI_MLOPS_PLAN.md`를 추가해 AI 모델 준비, 센서 수집 계획, 센서 데이터 분석, 학습 반영, MLOps 루프, 모델 진화 전략을 정리했다.
- `PLAN.md`에 Phase -1 AI 준비 구축 및 MLOps 기반 설계를 추가했다.
- `schedule.md`를 AI 준비 선행 일정으로 재구성했다.
- `todo.md`에 온실 공사중 전제, AI 준비/MLOps 기반 구축, 센서 수집 계획 보강, 모델 승격/롤백 항목을 추가했다.
- 참고 근거:
  - OpenAI Evals API: https://platform.openai.com/docs/api-reference/evals
  - OpenAI Retrieval guide: https://platform.openai.com/docs/guides/retrieval
  - OpenAI Fine-tuning guide: https://platform.openai.com/docs/guides/fine-tuning
  - MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
  - Kubeflow Pipelines: https://www.kubeflow.org/docs/components/pipelines/overview/

## 운영 규칙
- 주요 계획 변경은 이 파일에 날짜, 목적, 변경 파일, 커밋 해시를 함께 기록한다.
- 외부 조사에 기반한 결정은 근거 링크를 함께 남긴다.
- 자동 제어, 정책, 안전 게이트, RAG/파인튜닝 구조 변경은 반드시 `PLAN.md`, `todo.md`, `schedule.md` 중 관련 문서에 반영한다.

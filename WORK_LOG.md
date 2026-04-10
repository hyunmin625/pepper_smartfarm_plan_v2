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

### 적고추 재배 전주기 전문가 AI Agent 구축 계획 반영
- 적고추 온실 스마트팜 재배 전주기 전문가 AI Agent 구축 단계를 조사하고 `EXPERT_AI_AGENT_PLAN.md`로 정리했다.
- 전주기 범위를 입식 전 준비, 육묘, 정식, 영양생장, 개화/착과, 과실 비대/착색, 수확, 건조/저장, 작기 종료로 나누었다.
- 센서 기반 판단 체계를 환경, 근권/양액, 외기, 장치, 비전, 운영 이벤트로 정리했다.
- `growth-stage-agent`, `climate-agent`, `irrigation-agent`, `nutrient-agent`, `pest-disease-agent`, `harvest-drying-agent`, `safety-agent`, `report-agent` 역할을 정의했다.
- `README.md`, `PROJECT_STATUS.md`, `PLAN.md`, `schedule.md`, `todo.md`, `AGENTS.md`에 전문가 AI 구축 계획 링크와 우선 작업을 반영했다.
- 참고 근거:
  - 농사로 고추 육묘/재배 환경 자료: https://www.nongsaro.go.kr/portal/ps/psx/psxa/mlrdCurationDtl.mo?curationNo=188
  - 농사로 고추 이상증상 현장 기술지원: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=262042&menuId=PS00077
  - 농사로 고추 양액재배 현장 기술지원: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=259682&menuId=PS00077
  - 농사로 고추 생육불량 현장 기술지원: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=249249&menuId=PS00077
  - OpenAI Retrieval guide: https://platform.openai.com/docs/guides/retrieval
  - OpenAI Evals API: https://platform.openai.com/docs/api-reference/evals

### 인터넷 조사 5회 반복 및 RAG 구축 시작
- 인터넷 조사를 5회 반복해 전주기 전문가 AI용 초기 지식을 수집했다.
  1. 육묘/정식/초기 생육
  2. 온실 환경/고온/환기/차광
  3. 근권/양액/배지/EC/pH
  4. 병해충/생리장해
  5. 수확/건조/저장
- `docs/rag_source_inventory.md`를 추가해 RAG 출처, 메타데이터, ingestion 상태를 정리했다.
- `data/rag/pepper_expert_seed_chunks.jsonl`을 추가해 초기 seed chunk 6개를 작성했다.
- `docs/expert_knowledge_map.md`를 추가해 전주기 생육/운영 지식 지도를 작성했다.
- `docs/sensor_judgement_matrix.md`를 추가해 센서 데이터와 AI 판단 항목을 매핑했다.
- 다음 단계는 schema 작성, expert eval set 작성, vector store 인덱싱 스크립트 설계다.

### 전문가 AI Agent 스키마 4종 작성
- `schemas/state_schema.json`을 추가해 AI Agent 입력 상태 계약을 정의했다.
- `schemas/feature_schema.json`을 추가해 VPD, DLI, trend, 근권 스트레스, 숙도/병징 score 등 파생 특징량 구조를 정의했다.
- `schemas/sensor_quality_schema.json`을 추가해 missing, stale, outlier, jump, calibration error 등 품질 플래그 구조를 정의했다.
- `schemas/action_schema.json`을 추가해 AI 추천 행동, 승인 필요 여부, follow_up, citation, policy precheck 구조를 정의했다.
- 모든 JSON 스키마는 `python3 -m json.tool`로 문법 검증했다.

### 전문가 판단 평가셋 초안 작성
- `evals/expert_judgement_eval_set.jsonl`을 추가했다.
- 초기 케이스 8개를 작성했다: 정상 영양생장, 고온 스트레스, 과습/뿌리 갈변 위험, 배액 EC 상승, 온도 센서 stale, 병해충 의심, 수확/건조 계획, 작업자 존재 시 로봇 차단.
- `evals/README.md`를 추가해 평가 목적, 카테고리, 확장 방향을 정리했다.
- JSONL은 줄 단위 JSON 검증 대상으로 관리한다.

### 파인튜닝 후보 seed 샘플 작성
- `data/examples/state_judgement_samples.jsonl`을 추가해 상태판단 샘플 5개를 작성했다.
- `data/examples/forbidden_action_samples.jsonl`을 추가해 금지행동/승인필요 샘플 5개를 작성했다.
- `data/examples/README.md`를 추가해 샘플 작성 원칙과 확장 방향을 정리했다.
- 자주 바뀌는 기준값은 샘플에 암기시키지 않고 RAG citation으로 연결하는 원칙을 유지했다.

### RAG 인덱싱 준비
- `docs/rag_indexing_plan.md`를 추가해 RAG 입력 필드, 인덱싱 문서 구조, 검색 전략, 재인덱싱 규칙, 품질 검증 기준을 정리했다.
- `scripts/build_rag_index.py`를 추가해 `data/rag/pepper_expert_seed_chunks.jsonl`을 로컬 JSON 인덱스로 변환하도록 했다.
- `artifacts/rag_index/pepper_expert_index.json`을 생성했다.
- 스크립트 실행 결과 6개 seed chunk가 인덱싱되었다.
- 생성된 인덱스 JSON은 `python3 -m json.tool`로 문법 검증했다.

## 운영 규칙
- 주요 계획 변경은 이 파일에 날짜, 목적, 변경 파일, 커밋 해시를 함께 기록한다.
- 외부 조사에 기반한 결정은 근거 링크를 함께 남긴다.
- 자동 제어, 정책, 안전 게이트, RAG/파인튜닝 구조 변경은 반드시 `PLAN.md`, `todo.md`, `schedule.md` 중 관련 문서에 반영한다.

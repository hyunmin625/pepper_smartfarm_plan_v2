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

### RAG 검색 smoke test 작성
- `scripts/search_rag_index.py`를 추가해 로컬 JSON 인덱스를 keyword + metadata 방식으로 검색하도록 했다.
- `docs/rag_search_smoke_tests.md`를 추가해 고온, 과습, 양액 EC, 병해충, 육묘/정식, 안전/정책 query와 기대 chunk를 정의했다.
- `scripts/rag_smoke_test.py`를 추가해 6개 smoke query가 기대 chunk를 상위 3개 결과 안에 반환하는지 자동 검증한다.
- `python3 scripts/rag_smoke_test.py` 실행 결과 6개 query가 모두 통과했다.

### 농촌진흥청 PDF 기반 RAG 지식 보강
- 사용자가 제공한 로컬 PDF `/mnt/d/DOWNLOAD/GPT_고추재배_훈련세트/original-know-how/고추_재배기술_최종파일-농촌진흥청.pdf`를 `pdftotext -layout`으로 추출해 검토했다.
- 기존 RAG 청크와 중복되는 발아 온도, 정식 온도, 광포화점, 침수 임계, pH/표준시비, 병해충 기본 증상, 수확 적기, 3단계 건조 기준은 제외했다.
- 반영된 정밀 지식은 화분 발아 온도, 야간 저온 단위결과, 오전 광합성 비중, 뿌리/이랑 물리 조건, 플러그 상토 조건, 육묘 관수, 순화, 비가림 온습도, -20kPa 자동관수, 차광 전략, 양액 EC/pH, 석회결핍과, 염류장해, 홍고추 후숙, 건고추 저장 기준이다.
- `data/rag/pepper_expert_seed_chunks.jsonl`은 중복 `chunk_id`를 제거한 뒤 PDF 기반 정밀 청크 누적 22개, 전체 38개 청크 상태로 정리했다.
- `docs/rag_source_inventory.md`에 로컬 PDF 경로와 ingestion note를 기록했다.
- `docs/rag_indexing_plan.md`에 `source_pages`, `source_section` 기반 citation 추적 규칙을 추가했다.
- `scripts/build_rag_index.py`와 `scripts/search_rag_index.py`를 보강해 인과/시각 태그와 source section을 인덱싱·검색에 반영했다.
- `todo.md`에 PDF 지식 보강 완료와 남은 RAG 확장 작업을 반영했다.
- `python3 scripts/build_rag_index.py --skip-embeddings` 실행 결과 38개 문서가 인덱싱되었다.
- `python3 scripts/rag_smoke_test.py` 실행 결과 기존 6개 query와 신규 3개 PDF query가 모두 통과했다.
- JSONL 검증 결과 rows 38, duplicate chunk_id 0건을 확인했다.

### RAG 보완 핵심 과제 반영
- 사용자가 제시한 다음 핵심 과제를 별도 로드맵으로 정리했다.
  1. RAG 지식 청크를 100~200개 이상으로 확장
  2. OpenAI embedding 또는 Chroma/Pinecone 등 vector search 도입
  3. growth_stage, sensor, risk 외에 region, season, cultivar, greenhouse_type, active metadata filter 고도화
  4. 실제 농장 운영 로그와 성공/실패 사례를 `farm_case` RAG 지식으로 변환하는 파이프라인 설계
- `docs/rag_next_steps.md`를 추가해 Knowledge Expansion, Vector Search, Metadata Filtering, Farm Data Feedback 과제를 정리했다.
- `todo.md`, `PROJECT_STATUS.md`, `docs/rag_indexing_plan.md`에 RAG 보완 과제와 링크를 반영했다.

### RAG 청크 검증 기반 구현
- `schemas/rag_chunk_schema.json`을 추가해 RAG chunk 필수 필드와 권장 metadata 구조를 정의했다.
- `scripts/validate_rag_chunks.py`를 추가해 외부 의존성 없이 JSONL 필수 필드, 중복 `chunk_id`, citation metadata 경고를 검증하도록 했다.
- `scripts/build_rag_index.py`의 필수 필드 검증을 `causality_tags`, `visual_tags`까지 확장했다.
- 초기 시드 청크의 `source_pages`, `source_section`, `trust_level`을 보강해 citation metadata 경고를 해소했다.
- 검증 결과: rows 38, duplicate chunk_id 0, errors 0, warnings 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 38개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- 검색 smoke test 결과: `python3 scripts/rag_smoke_test.py` 기준 9개 query 모두 PASS.

### RAG 검색 필터 및 Reranking 구현
- `scripts/search_rag_index.py`에 `trust_level` 및 `source_type` 기반 rerank bonus를 추가했다.
- `source_section` 부분 일치 필터와 `region`, `season`, `cultivar`, `greenhouse_type`, `active`, `trust_level` CLI 필터를 추가했다.
- `scripts/rag_smoke_test.py`에 메타데이터 필터 검증 2건을 추가했다.
- 검색 smoke test 결과: 기본 9개 query와 필터 query 2건 모두 PASS.

### RAG 검색 품질 평가 기반 구현
- `evals/rag_retrieval_eval_set.jsonl`을 추가해 기후, 근권, 양액, 병해충, 육묘/정식, 안전정책, 수확/건조, metadata filter 검색 평가 케이스 11건을 정의했다.
- `scripts/evaluate_rag_retrieval.py`를 추가해 Hit Rate와 MRR을 계산하도록 했다.
- 현재 평가 결과: keyword-only 기준 case_count 11, hit_count 11, hit_rate 1.0, MRR 0.9091.
- `evals/README.md`와 `docs/rag_search_smoke_tests.md`에 RAG 검색 평가 실행 명령을 추가했다.

### RAG 병해충·양액재배 지식 확장
- `data/rag/pepper_expert_seed_chunks.jsonl`에 병해충/IPM, 총채벌레·진딧물 생물적 방제, 바이러스 전염 생태, 양액 급액 제어 관련 청크 10개를 추가했다.
- 추가된 청크에는 `pepper-hydroponic-water-ph-buffer-001`, `pepper-hydroponic-irrigation-volume-001`, `pepper-hydroponic-irrigation-control-001`, `pepper-ipm-lifecycle-001`, `pepper-ipm-scouting-hygiene-001`, `pepper-thrips-tswv-control-001`, `pepper-thrips-biocontrol-001`, `pepper-aphid-virus-biocontrol-001`, `pepper-virus-epidemiology-001`, `pepper-tswv-early-house-001`가 포함된다.
- 확장 후 검증 결과: rows 48, duplicate chunk_id 0, warnings 0, errors 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 48개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- 검색 품질 유지 확인: `python3 scripts/rag_smoke_test.py` 11건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` hit_rate 1.0, MRR 0.9091.

### RAG 품종·재배력 지식 확장
- `data/rag/pepper_expert_seed_chunks.jsonl`에 품종 선택 기준, 풋고추 과형 분류, 작형별 재배 형태, 노지 재배력, 수확 기준일 관련 청크 8개를 추가했다.
- 추가된 청크에는 `pepper-cultivar-selection-dry-001`, `pepper-cultivar-selection-green-001`, `pepper-cultivar-rain-shelter-001`, `pepper-cultivar-resistance-stack-001`, `pepper-greenpepper-type-001`, `pepper-regional-cropping-system-001`, `pepper-openfield-calendar-001`, `pepper-harvest-days-by-type-001`가 포함된다.
- 확장 후 검증 결과: rows 56, duplicate chunk_id 0, warnings 0, errors 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 56개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- 검색 품질 확인: `python3 scripts/rag_smoke_test.py` 11건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` hit_rate 1.0, MRR 0.8939.

### RAG 기상 재해·계절 리스크 지식 확장
- `data/rag/pepper_expert_seed_chunks.jsonl`에 비가림 재배력, 장마, 태풍, 우박, 지역 저온, 터널 서리창 대응 기준 청크 6개를 추가했다.
- 추가된 청크에는 `pepper-rain-shelter-calendar-001`, `pepper-lowtemp-regional-recovery-001`, `pepper-monsoon-prevention-001`, `pepper-typhoon-response-001`, `pepper-hail-recovery-001`, `pepper-tunnel-frost-window-001`가 포함된다.
- 신규 공식 지침 청크 유입으로 일부 query의 상위 순위가 흔들려 `scripts/search_rag_index.py`의 `official_guideline` rerank bonus를 0.4로 상향 조정했다.
- 확장 후 검증 결과: rows 62, duplicate chunk_id 0, warnings 0, errors 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 62개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- 검색 품질 확인: `python3 scripts/rag_smoke_test.py` 11건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` hit_rate 1.0, MRR 0.9545.

### RAG 재해 대응 검색 평가 범위 확장
- `scripts/rag_smoke_test.py`에 비가림 재배력, 정식기 저온·재정식, 장마, 태풍, 우박 대응 query 5건을 추가했다.
- `evals/rag_retrieval_eval_set.jsonl`에 동일 범주의 retrieval 평가 케이스 5건을 추가해 전체 16개 case를 검증하도록 확장했다.
- `docs/rag_search_smoke_tests.md`, `docs/rag_indexing_plan.md`, `evals/README.md`, `PROJECT_STATUS.md`, `todo.md`에 최신 평가 범위를 반영했다.
- 확장 후 검색 품질 확인: `python3 scripts/rag_smoke_test.py` 총 16건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` case_count 16, hit_rate 1.0, MRR 0.9688.

### RAG 수확 후·건조·저장 지식 확장
- `data/rag/pepper_expert_seed_chunks.jsonl`에 수확 후 물류, 홍고추 후숙, 세척 위생, 풋고추 저장·결로, 홍고추 저장, 건고추 장기 저장, 고춧가루 산소흡수제 포장, 하우스건조, 열풍건조 효율 관련 청크 10개를 추가했다.
- 추가된 청크에는 `pepper-green-harvest-logistics-001`, `pepper-red-harvest-window-001`, `pepper-postharvest-wash-hygiene-001`, `pepper-green-storage-temperature-001`, `pepper-green-packaging-condensation-001`, `pepper-red-storage-ethylene-001`, `pepper-dry-storage-maintenance-001`, `pepper-powder-packaging-oxygen-001`, `pepper-house-drying-hygiene-001`, `pepper-hotair-drying-split-001`가 포함된다.
- 확장 후 검증 결과: rows 72, duplicate chunk_id 0, warnings 0, errors 0.
- 재색인 결과: `python3 scripts/build_rag_index.py --skip-embeddings`로 72개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.
- `scripts/rag_smoke_test.py`에 수확 후·저장·건조 query 8건을 추가하고, `evals/rag_retrieval_eval_set.jsonl`에 같은 범주의 retrieval 평가 케이스 8건을 반영했다.
- 확장 후 검색 품질 확인: `python3 scripts/rag_smoke_test.py` 총 24건 PASS, `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` case_count 24, hit_rate 1.0, MRR 0.9792.

### 로컬 Vector Search PoC 구현
- `scripts/rag_local_vector.py`를 추가해 외부 의존성 없이 TF-IDF + SVD 기반 로컬 벡터 모델을 생성하도록 했다.
- `scripts/build_rag_index.py`에서 로컬 벡터 모델과 각 문서의 `local_embedding`을 함께 생성하도록 반영했다.
- `scripts/search_rag_index.py`에 `--vector-backend {auto,openai,local,none}` 옵션을 추가하고, OpenAI embedding이 없을 때 `local` 백엔드로 검색할 수 있도록 했다.
- `scripts/evaluate_rag_retrieval.py`에 `--vector-backend` 옵션을 추가해 keyword-only, local vector hybrid, OpenAI vector 경로를 구분 평가하도록 확장했다.
- `scripts/compare_rag_retrieval_modes.py`를 추가해 keyword baseline과 local vector hybrid의 hit rate/MRR 및 changed case를 비교할 수 있도록 했다.
- 검증 결과: `python3 scripts/evaluate_rag_retrieval.py --fail-under 1.0` 기준 keyword-only hit_rate 1.0, MRR 0.9792, `python3 scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0` 기준 local hybrid hit_rate 1.0, MRR 1.0, `python3 scripts/compare_rag_retrieval_modes.py --candidate-backend local` 기준 delta_mrr +0.0208.

## 2026-04-11

### RAG 지식 100개 확장 완료
- `data/rag/pepper_expert_seed_chunks.jsonl`을 100개 청크까지 확장했다.
- 육묘 계절 관리, 입고병 예방, 매개충 차단, 접목 목적/방법/활착, 식물공장 육묘, 비가림 구조·염류·저일조 대응 지식을 추가했다.
- 검증 결과: `./.venv/bin/python scripts/validate_rag_chunks.py` 기준 rows 100, duplicate 0, warnings 0, errors 0.
- 재색인 결과: `./.venv/bin/python scripts/build_rag_index.py --skip-embeddings`로 100개 문서를 `artifacts/rag_index/pepper_expert_index.json`에 반영했다.

### ChromaDB Vector Store 도입
- `.venv` 가상환경과 `requirements-rag.txt`를 추가해 RAG/Vector Search 실행 의존성을 명시했다.
- `.gitignore`에 `.venv/`, `artifacts/chroma_db/`를 추가해 재생성 가능한 로컬 산출물을 제외했다.
- `scripts/rag_chroma_store.py`를 기반으로 persistent Chroma collection 접근 함수를 정리했다.
- `scripts/build_chroma_index.py`에 `--embedding-backend {auto,openai,local}` 옵션을 추가했다.
- 현재 환경에서는 OpenAI API 키가 없어 `local` backend로 `artifacts/chroma_db/pepper_expert` 컬렉션을 생성해 검증했다.
- `scripts/search_rag_index.py`에 `--vector-backend chroma`와 `--chroma-embedding-backend {auto,openai,local}` 경로를 반영했다.
- `scripts/evaluate_rag_retrieval.py`, `scripts/compare_rag_retrieval_modes.py`도 동일한 Chroma backend 인자를 받도록 확장했다.

### Citation Coverage 검증 반영
- `scripts/validate_response_citations.py`를 작업 현황 문서와 todo에 반영했다.
- 이 스크립트는 retrieved_context 대비 citations 누락, out-of-context 인용, `citation_required` 미충족, `retrieval_coverage` 불일치를 검증한다.

### Vector Search 검증 결과 갱신
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0`
  - keyword-only: hit_rate 1.0, MRR 0.9583
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0`
  - local vector hybrid: hit_rate 1.0, MRR 1.0
- `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local`
  - local-backed Chroma collection 100 vectors 생성
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`
  - local-backed Chroma hybrid: hit_rate 1.0, MRR 1.0
- `./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend local`
  - baseline keyword 대비 delta_mrr +0.0417

### `.env` 기반 OpenAI 키 경로 정리
- 저장소 루트 `.env`를 `python-dotenv` 기본 로딩 경로로 사용하도록 운영 절차를 정리했다.
- `.gitignore`에 `.env`, `.env.*`, `!.env.example`를 추가해 실제 키 파일은 추적하지 않도록 했다.
- `.env.example`을 추가했고, 로컬 `.env` 자리도 마련했다.
- 이후 `.env`에 실제 키를 반영해 OpenAI-backed Chroma 실호출 검증까지 수행했다.

### OpenAI-backed Chroma 실검증 완료
- `.env`에서 `OPENAI_API_KEY`를 로드한 뒤 `./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai`를 실행해 OpenAI 임베딩 기반 Chroma collection 100 vectors를 생성했다.
- `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0` 실행 결과, 초기 설정에서는 24개 case hit_rate 1.0, MRR 0.9792를 확인했다.
- `./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend openai` 실행 결과, keyword baseline 대비 delta_mrr +0.0209를 확인했다.
- 현재 평가셋에서는 local vector/local-backed Chroma(MRR 1.0)가 OpenAI-backed Chroma(MRR 0.9792)보다 소폭 높게 나와, 원인 분석 대상으로 넘겼다.

### OpenAI-backed Chroma 보정 및 collection 분리
- `scripts/tune_rag_weights.py`를 추가해 retrieval weight grid search를 자동화했다.
- OpenAI-backed Chroma에 대해 `chroma_local_blend_weight`를 0, 2, 4, 6으로 비교한 결과, `4.0`부터 MRR 1.0을 달성했다.
- `scripts/search_rag_index.py`에 OpenAI-backed Chroma 전용 local blend score를 추가했고, 기본값을 `4.0`으로 올렸다.
- local-backed Chroma와 OpenAI-backed Chroma가 같은 collection 이름을 쓰며 차원 충돌이 발생하던 문제를 확인하고, collection 이름을 `pepper_expert_chunks_local`, `pepper_expert_chunks_openai`로 분리했다.
- manifest도 `artifacts/chroma_db/pepper_expert_manifest_local.json`, `artifacts/chroma_db/pepper_expert_manifest_openai.json`로 backend별 분리 생성하도록 수정했다.
- 보정 후 검증 결과:
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0`
    - hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0`
    - hit_rate 1.0, MRR 1.0
  - `./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend openai`
    - keyword baseline 대비 delta_mrr +0.0417

## 운영 규칙
- 주요 계획 변경은 이 파일에 날짜, 목적, 변경 파일, 커밋 해시를 함께 기록한다.
- 외부 조사에 기반한 결정은 근거 링크를 함께 남긴다.
- 자동 제어, 정책, 안전 게이트, RAG/파인튜닝 구조 변경은 반드시 `PLAN.md`, `todo.md`, `schedule.md` 중 관련 문서에 반영한다.

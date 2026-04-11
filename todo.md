# todo.md


## 관련 문서
- [저장소 README](README.md)
- [프로젝트 현황 요약](PROJECT_STATUS.md)
- [AI 모델 준비 및 MLOps 계획](AI_MLOPS_PLAN.md)
- [적고추 전문가 AI Agent 구축 계획](EXPERT_AI_AGENT_PLAN.md)
- [데이터셋 분류 체계](docs/dataset_taxonomy.md)
- [학습 데이터 포맷](docs/training_data_format.md)
- [데이터 정제 규칙](docs/data_curation_rules.md)
- [RAG 보완 핵심 과제](docs/rag_next_steps.md)
- [farm_case RAG 환류 파이프라인](docs/farm_case_rag_pipeline.md)
- [Offline Agent Runner 스펙](docs/offline_agent_runner_spec.md)
- [MLOps Registry 설계](docs/mlops_registry_design.md)
- [Shadow Mode Report 포맷](docs/shadow_mode_report_format.md)
- [일정 계획 보기](schedule.md)
- [전체 개발 계획 보기](PLAN.md)
- [작업 로그 보기](WORK_LOG.md)

# 온실 스마트팜 고추 재배 자동화를 위한 농업용 LLM 개발 세부 Todo

이 문서는 실제 개발 착수를 위한 **아주 세분화된 단계별 작업 목록**이다.  
각 작업은 가능한 한 작게 쪼개어, 바로 이슈/태스크로 옮길 수 있게 구성한다.

---

# 0. 프로젝트 관리 초기화

## 0.0 온실 공사중 전제 반영
- [x] 온실 공사 일정과 AI 준비 일정 분리 (`AI_MLOPS_PLAN.md`, `schedule.md`)
- [x] 실측 데이터 수집 전 AI 준비 범위 정의 (`AI_MLOPS_PLAN.md`)
- [x] 공사 완료 전 사용 가능한 문서/시뮬레이션/합성 데이터 목록화 (`AI_MLOPS_PLAN.md`, `docs/rag_source_inventory.md`, `data/examples/synthetic_sensor_scenarios.jsonl`)
- [ ] 공사 완료 후 센서 연결 전환 절차 정의
- [x] AI 준비 → 센서 계획 → 센서 구현 → 제어 계획 → 제어 구현 → UI → AI 연결 순서 확정 (`AI_MLOPS_PLAN.md`, `schedule.md`, `PLAN.md`)

## 0.1 프로젝트 구조 정의
- [ ] 프로젝트 코드명 확정
- [x] 저장소 구조 정의 (`AGENTS.md`, `README.md`)
- [ ] monorepo 여부 결정
- [x] 서비스별 디렉터리 구조 설계 (`AGENTS.md`)
- [ ] 공통 라이브러리 디렉터리 정의
- [x] infra 디렉터리 구조 정의 (`AGENTS.md`)
- [x] docs 디렉터리 구조 정의 (`AGENTS.md`)
- [x] data 디렉터리 구조 정의 (`AGENTS.md`)
- [x] experiments 디렉터리 구조 정의 (`AGENTS.md`)

## 0.2 형상관리/협업 준비
- [ ] Git 브랜치 전략 정의
- [x] commit convention 정의 (`AGENTS.md`)
- [ ] PR 템플릿 작성
- [ ] issue 템플릿 작성
- [ ] ADR(Architecture Decision Record) 템플릿 작성
- [ ] CHANGELOG 정책 정리
- [ ] 릴리즈 태깅 규칙 정리

## 0.3 개발 환경 공통화
- [ ] Python 버전 고정
- [x] 가상환경 전략 정의 (`evals/README.md`, `WORK_LOG.md`)
- [ ] package manager 선택
- [ ] 린터 선택
- [ ] formatter 선택
- [ ] type checker 선택
- [ ] pre-commit hook 구성
- [x] 환경 변수 템플릿 작성 (`.env.example`)
- [ ] dev/staging/prod 환경 변수 분리

## 0.4 문서 기반 정리
- [ ] 용어집 작성
- [ ] 장치 명명 규칙 정의
- [x] zone_id 규칙 정의 (`docs/sensor_collection_plan.md`)
- [x] sensor_id 규칙 정의 (`docs/sensor_collection_plan.md`)
- [x] device_id 규칙 정의 (`docs/sensor_collection_plan.md`)
- [ ] robot_id 규칙 정의
- [x] action_type enum 초안 작성 (`schemas/action_schema.json`)
- [ ] 이벤트 이름 규칙 정의

---

# 1. 요구사항/현장 분석

## 1.1 현장 범위 확정
- [ ] 대상 온실 수 확정
- [x] 초기 적용 zone 확정 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 작물 범위 확정 (`README.md`, `PROJECT_STATUS.md`, `PLAN.md`)
- [ ] 품종 범위 확정
- [x] 생육 단계 운영 범위 정의 (`docs/expert_knowledge_map.md`, `EXPERT_AI_AGENT_PLAN.md`)
- [ ] 낮/밤 운영 정책 정의
- [ ] 계절별 운영 범위 정의

## 1.2 센서 인벤토리 작성
- [ ] 온도 센서 모델 조사
- [ ] 습도 센서 모델 조사
- [ ] CO2 센서 모델 조사
- [ ] 광량 센서 모델 조사
- [ ] 배지 함수율 센서 모델 조사
- [ ] EC 센서 모델 조사
- [ ] pH 센서 모델 조사
- [ ] 외기 센서 모델 조사
- [x] 카메라 사양 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 각 센서의 통신 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 각 센서의 샘플링 주기 정리 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 각 센서의 보정 주기 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 품질 플래그 조건 정리 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] zone별 설치 수량 가정치 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] sensor `model_profile` 기준 정의 (`docs/sensor_installation_inventory.md`, `schemas/sensor_catalog_schema.json`)

## 1.3 액추에이터 인벤토리 작성
- [x] 환기창 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 순환팬 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 난방기 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 차광커튼 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 관수 밸브 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 양액기 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] CO2 주입기 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 제습기 제어 방식 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [ ] 각 장치의 최소/최대 setpoint 정리
- [x] 각 장치의 응답 지연 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] 장치별 안전 제한값 정리 (`docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [x] device `model_profile` 기준 정의 (`docs/sensor_installation_inventory.md`, `schemas/sensor_catalog_schema.json`)

## 1.4 운영 시나리오 정리
- [x] 정상 운영 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 고온 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [ ] 고습 시나리오 작성
- [ ] 급격한 일사 증가 시나리오 작성
- [ ] 과건조 시나리오 작성
- [x] 과습 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 센서 고장 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [ ] 장치 stuck 시나리오 작성
- [ ] 통신 장애 시나리오 작성
- [ ] 정전/재기동 시나리오 작성
- [ ] 사람 개입 시나리오 작성
- [ ] 로봇 작업 중단 시나리오 작성

## 1.5 안전 요구사항 정리
- [ ] 인터록 요구사항 목록화
- [ ] 비상정지 요구사항 목록화
- [ ] 수동모드 전환 조건 정의
- [ ] 자동모드 전환 조건 정의
- [ ] 승인 필수 액션 정의
- [ ] 절대 금지 액션 정의
- [ ] 사람 감지 시 동작 규칙 정의
- [ ] 로봇 작업 영역 접근 규칙 정의

---

# 2. 도메인 지식/데이터 준비

## 2.1 고추 재배 지식셋 정리
- [x] 기존 문서 수집 (`docs/rag_source_inventory.md`)
- [x] 재배 매뉴얼 정리 (`docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 생육 단계별 환경 목표 정리 (`docs/expert_knowledge_map.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 관수 기준 정리 (`docs/expert_knowledge_map.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] EC/pH 관리 기준 정리 (`docs/expert_knowledge_map.md`, `docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 병해 위험 조건 정리 (`docs/expert_knowledge_map.md`, `docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 수확 적기 기준 정리 (`docs/expert_knowledge_map.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 품종별 차이 정리 (`docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] 온실 외기 영향 정리 (`docs/rag_source_inventory.md`, `data/rag/pepper_expert_seed_chunks.jsonl`)
- [ ] 장치 운전 경험 규칙 정리

## 2.2 데이터셋 분류 체계 정의
- [x] Q&A 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/qa_reference_samples.jsonl`)
- [x] 상태판단 데이터 분류 (`data/examples/state_judgement_samples.jsonl`, `evals/expert_judgement_eval_set.jsonl`)
- [x] 행동추천 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/action_recommendation_samples.jsonl`)
- [x] 금지행동 데이터 분류 (`data/examples/forbidden_action_samples.jsonl`)
- [x] 실패대응 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/failure_response_samples.jsonl`)
- [x] 로봇작업 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/robot_task_samples.jsonl`)
- [x] 알람/보고서 데이터 분류 (`docs/dataset_taxonomy.md`, `data/examples/reporting_samples.jsonl`)

## 2.3 학습 데이터 포맷 정의
- [x] input message 포맷 정의 (`docs/training_data_format.md`)
- [x] preferred_output 포맷 정의 (`docs/training_data_format.md`)
- [x] 상태판단 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/state_judgement_samples.jsonl`)
- [x] 행동추천 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/action_recommendation_samples.jsonl`)
- [x] 금지행동 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/forbidden_action_samples.jsonl`)
- [x] 로봇 우선순위 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/robot_task_samples.jsonl`)
- [x] 실패대응 샘플 템플릿 정의 (`docs/training_data_format.md`, `data/examples/failure_response_samples.jsonl`)
- [x] JSON schema 포함 방식 정의 (`docs/training_data_format.md`)

## 2.4 데이터 정제
- [ ] 중복 샘플 제거
- [ ] 모순 샘플 검토
- [x] 표현 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 장치명 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 단위 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] zone 표기 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 생육 단계 표기 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 위험도 레이블 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)
- [x] 근거 서술 스타일 통일 (`docs/data_curation_rules.md`)
- [x] 후속 확인 항목 통일 (`docs/data_curation_rules.md`, `scripts/validate_training_examples.py`)

## 2.5 평가셋 구축
- [x] 상태판단 평가셋 구축 (`evals/expert_judgement_eval_set.jsonl`)
- [x] 행동추천 평가셋 구축 (`evals/action_recommendation_eval_set.jsonl`)
- [x] 금지행동 평가셋 구축 (`evals/forbidden_action_eval_set.jsonl`)
- [x] 장애대응 평가셋 구축 (`evals/failure_response_eval_set.jsonl`)
- [x] 로봇 작업 우선순위 평가셋 구축 (`evals/robot_task_eval_set.jsonl`)
- [ ] edge case 평가셋 구축
- [ ] 계절별 평가셋 구축
- [x] 센서 이상 포함 평가셋 구축 (`evals/expert_judgement_eval_set.jsonl`)

## 2.6 RAG 지식베이스 구축 [완료]
- [x] RAG 적용 문서 범위 정의 (`docs/rag_source_inventory.md`)
- [x] RAG 메타데이터 스키마 및 인덱싱 계획 수립 (`docs/rag_indexing_plan.md`)
- [x] RAG 보완 핵심 과제 정리 (`docs/rag_next_steps.md`)
- [x] RAG 청크 검증 스키마와 JSONL 검증 스크립트 추가 (`schemas/rag_chunk_schema.json`, `scripts/validate_rag_chunks.py`)
- [x] 초기 시드 청크(6종) 인덱싱 및 테스트 (`scripts/build_rag_index.py`, `scripts/rag_smoke_test.py`)
- [x] 농촌진흥청 PDF 원문 기반 중복 제외 지식 보강 누적 22개 반영 (`data/rag/pepper_expert_seed_chunks.jsonl`)
- [x] PDF page/section citation 추적용 RAG 메타데이터 반영 (`source_pages`, `source_section`)
- [x] 농촌진흥청 PDF 추가 정밀 추출 후 중복 chunk_id 3건 병합, 전체 seed chunk 72개로 확장
    - [x] 화분/착과 임계값, 비가림 온습도, 자동관수, 차광, 육묘 소질, 플러그 상토 반영
    - [x] 가뭄, 저온해, 고온해, 영양장애, 생리장해, 건고추 저장 판단 기준 반영
    - [x] 병해충/IPM, 총채벌레·진딧물 생물적 방제, 바이러스 전염 생태, 양액 급액 제어 반영
    - [x] 품종 선택 기준, 풋고추 과형 분류, 재배 형태별 재배 시기, 노지 재배력 반영
    - [x] 비가림 재배력, 장마·태풍·우박·저온·서리창 대응 기준 반영
- [x] 육묘/접목/식물공장/비가림 재배 보강으로 전체 seed chunk 100개 확장
    - [x] 육묘 계절 관리, 입고병 예방, 바이러스 매개충 차단, 소질 진단 반영
    - [x] 접목 목적, 대목 분류, 파종 시차, 접목법, 활착 관리, 접목묘 정식 기준 반영
    - [x] 식물공장 육묘·활착 관리, 비가림 구조·밀도·염류·저일조 대응 반영
- [x] 초기 시드 청크의 `source_pages`, `source_section` 누락 경고 해소
    - [x] `python3 scripts/validate_rag_chunks.py` 기준 rows 100, duplicate 0, warnings 0, errors 0 확인
- [x] **지식 데이터 확충 (Phase 1: 전주기 커버리지)**
    - [x] 농사로(RAG-SRC-001~004) 및 현장 사례에서 정밀 청크 100개 이상 추출
    - [x] 농사로 추가 현장 사례(RAG-SRC-018~025) 반영으로 전체 seed chunk 141개 확장
    - [x] RAG-SRC-001 병해충/IPM·비가림 관리·건조 장 추가 추출로 전체 seed chunk 169개 확장
    - [x] 농사로(RAG-SRC-001~004) 및 현장 사례에서 정밀 청크 200개 이상 추출
    - [x] RAG-SRC-001 PDF 병해충/IPM, 양액재배/시설재배 장 추가 추출 지속
    - [x] 적고추 품종별 온도, 착과, 착색, 병저항성 기준 1차 청크화 (`pepper-crop-env-thresholds-001`, `pepper-cultivar-phytophthora-resistance-001`, `pepper-cultivar-fruitset-stability-001`, `pepper-cultivar-honggoeun-001`)
    - [x] 지역별 재배력, 월별 작업, 지역 기상 리스크 1차 청크화 (`pepper-semiforcing-schedule-001`, `pepper-normal-schedule-001`, `pepper-forcing-energy-saving-001`, `pepper-curved-fruit-cropping-shift-001`)
    - [x] 신규 PDF 청크별 **인과관계(Causality) 태그** 및 **시각적 특징(Visual) 태그** 라벨링
    - [x] 수확 후 큐어링·세척 위생, 풋고추 저장·결로, 홍고추 저장, 건고추 장기 저장·산소흡수제 포장, 하우스·열풍건조 운전 규칙 보강
    - [x] 미숙퇴비 암모니아 피해, 수직배수 불량, 과차광 낙화, 육묘 새순 오그라듦, 첫서리 낙화, 노화묘, 해비치·루비홍 품종 사례 반영
    - [x] 역병 초기 발병률, 호밀 혼화·고휴재배, 아인산 예방, 탄저병 빗물 전파·비가림 위생, 가루이·진딧물·나방·응애 세부 운용 규칙 반영
    - [x] 적고추 건조/저장 특화 지식 및 에너지 세이빙 노하우 1차 확장
    - [x] 균핵병·시들음병·잿빛곰팡이병·흰별무늬병·흰비단병·무름병·세균점무늬병·잎굴파리·뿌리혹선충·농약 안전사용 청크 추가로 전체 219개 확장
- [x] **전문가 수준 검색 및 중재 로직 구현**
    - [x] 지식 충돌 시 해결을 위한 **Trust Level 기반 Reranking** 로직 1차 구현
    - [x] 기상 재해·작형 대응 query 5종을 추가해 smoke/eval coverage 16건으로 확장
    - [x] 수확 후·건조·저장 대응 query 8종을 추가해 smoke/eval coverage 24건으로 확장
    - [x] **Multi-turn Contextual Retrieval**: 과거 3~5일간의 상태를 고려한 지식 검색 전략 수립 (`docs/rag_contextual_retrieval_strategy.md`)
    - [x] 로컬 **TF-IDF + SVD vector search PoC** 구현
    - [x] **ChromaDB persistent vector store** 구현 및 local-backed collection 검증
    - [x] OpenAI embedding 모델 연동 및 OpenAI-backed Chroma collection 검증
    - [x] **Metadata Hard Filtering** 로직 1차 구현 (growth/source/sensor/risk filter)
    - [x] `region`, `season`, `cultivar`, `greenhouse_type`, `active` 필터 추가
    - [x] `source_section` 부분 일치 필터와 `trust_level` 기반 reranking 구현
    - [x] OpenAI-backed Chroma의 낮은 MRR 케이스 분석 및 `local blend 4.0` 기본값 반영
    - [x] backend별 Chroma collection/manifest 분리로 차원 충돌 방지
    - [x] retrieval weight 튜닝 스크립트 추가 (`scripts/tune_rag_weights.py`)
    - [x] Semantic + Keyword 하이브리드 검색 가중치 재검증용 eval set 40개 확장
    - [x] smoke test 81건, retrieval eval 96건으로 공식 PDF 추가 추출분 재검증
    - [x] smoke test 98건, retrieval eval 110건으로 219청크 재검증
- [x] **RAG 품질 평가 체계 구축**
    - [x] 시나리오별 검색 적중률(Hit Rate) 측정 1차 구현 (`evals/rag_retrieval_eval_set.jsonl`, `scripts/evaluate_rag_retrieval.py`)
    - [x] 출처 누락 방지를 위한 citation metadata 검증 로직 추가 (`scripts/validate_rag_chunks.py`)
    - [x] keyword-only vs local vector hybrid 비교 스크립트 추가 (`scripts/compare_rag_retrieval_modes.py`)
    - [x] 할루시네이션 방지를 위한 응답 citation coverage 검증 로직 추가 (`scripts/validate_response_citations.py`)
    - [x] keyword-only, local vector, local-backed Chroma 검색 hit rate 비교
    - [x] OpenAI vector를 포함한 4모드 검색 hit rate 비교
    - [x] 96개 평가셋 기준 4모드 재검증 완료 (keyword 0.9896, local 1.0, Chroma local 0.9948, Chroma OpenAI 0.9826)
    - [x] 4모드 비교를 더 긴 평가셋(40 case)으로 재검증
    - [x] 4모드 비교를 계절·센서 이상·현장 사례 케이스 포함 80 case로 재검증
    - [x] 110개 평가셋 기준 4모드 재검증 완료 (keyword 0.9909, local 0.9955, Chroma local 0.9955, Chroma OpenAI 0.9803)

## 2.7 AI 준비/MLOps 기반 구축
- [x] AI_MLOPS_PLAN.md 유지관리
- [x] offline decision runner 요구사항 작성 (`docs/offline_agent_runner_spec.md`)
- [x] 센서 상태 합성 시나리오 작성 (`data/examples/synthetic_sensor_scenarios.jsonl`)
- [x] 평가셋 버전 관리 규칙 정의 (`docs/mlops_registry_design.md`)
- [x] dataset registry 설계 (`docs/mlops_registry_design.md`)
- [x] prompt registry 설계 (`docs/mlops_registry_design.md`)
- [x] model registry 설계 (`docs/mlops_registry_design.md`)
- [x] champion/challenger 모델 승격 규칙 정의 (`docs/mlops_registry_design.md`)
- [x] shadow mode 평가 리포트 포맷 정의 (`docs/shadow_mode_report_format.md`)
- [x] 운영 로그 → 학습 후보 변환 규칙 정의 (`docs/mlops_registry_design.md`)
- [x] 운영 로그 → RAG `farm_case` 후보 변환 규칙 정의 (`docs/farm_case_rag_pipeline.md`)
- [x] `farm_id`, `zone_id`, `cultivar`, `season`, `outcome` metadata 정의 (`schemas/farm_case_candidate_schema.json`)
- [x] 성공/실패 사례를 공식 지식과 충돌 검토 후 RAG에 반영하는 승인 절차 정의 (`docs/farm_case_rag_pipeline.md`)
- [ ] `farm_case_candidate` JSONL 샘플 10건 작성
- [ ] event window builder 규칙을 세부 스펙으로 구체화
- [ ] 승인된 `farm_case` 후보를 RAG chunk JSONL로 변환하는 스크립트 초안 작성

## 2.8 적고추 전문가 AI Agent 구축
- [x] 적고추 재배 전주기 단계 정의 (`docs/expert_knowledge_map.md`, `EXPERT_AI_AGENT_PLAN.md`)
- [x] 생육 단계별 전문가 판단 질문 목록 작성 (`docs/expert_knowledge_map.md`)
- [x] 센서 지표와 판단 항목 매핑 (`docs/sensor_judgement_matrix.md`)
- [x] `docs/expert_knowledge_map.md` 작성
- [x] `docs/sensor_judgement_matrix.md` 작성
- [x] `schemas/feature_schema.json` 작성
- [x] `schemas/sensor_quality_schema.json` 작성
- [x] `evals/expert_judgement_eval_set.jsonl` 작성
- [x] `docs/agent_tool_design.md` 작성
- [x] `docs/offline_agent_runner_spec.md` 작성
- [x] growth-stage-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] climate-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] irrigation-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] nutrient-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] pest-disease-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] harvest-drying-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] safety-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)
- [x] report-agent 역할 정의 (`EXPERT_AI_AGENT_PLAN.md`)

---

# 3. 파인튜닝 준비 및 수행

## 3.1 학습 목표 재정의
- [ ] 지식형 모델 vs 운영형 모델 역할 구분
- [ ] RAG 담당 지식과 파인튜닝 담당 행동 양식 분리
- [ ] 파인튜닝 목표 문서화
- [ ] 구조화 출력 목표 정의
- [ ] 허용 action_type 목록 확정
- [ ] confidence 출력 요구 정의
- [ ] follow_up 출력 요구 정의
- [ ] citations/retrieval_coverage 출력 요구 정의

## 3.2 데이터 파일 생성
- [ ] 학습용 JSONL 생성 스크립트 작성
- [ ] 검증용 JSONL 생성 스크립트 작성
- [ ] 포맷 검증 스크립트 작성
- [ ] 샘플 통계 리포트 생성
- [ ] class imbalance 확인
- [ ] action_type 분포 확인
- [ ] 길이 분포 확인
- [ ] 이상 샘플 수동 검토

## 3.3 학습 실행
- [ ] 모델 버전 결정
- [ ] 실험명 규칙 정의
- [ ] 파인튜닝 작업 실행
- [ ] 로그 보관
- [ ] 학습 실패 케이스 기록
- [ ] 결과 비교표 작성

## 3.4 파인튜닝 결과 검증
- [ ] 상태 요약 품질 평가
- [ ] 추천 행동 유효성 평가
- [ ] 금지 행동 준수 평가
- [ ] JSON 일관성 평가
- [ ] RAG 문맥이 주어졌을 때 근거 반영률 평가
- [ ] 검색 근거 부족 시 불확실성 표현 평가
- [ ] hallucination 사례 정리
- [ ] confidence calibration 검토
- [ ] 사람 검토 결과 수집
- [ ] 개선 포인트 정리

---

# 4. 시스템 스키마 설계

## 4.1 공통 도메인 모델
- [ ] Zone 모델 정의
- [ ] Sensor 모델 정의
- [ ] Device 모델 정의
- [ ] Constraint 모델 정의
- [ ] Decision 모델 정의
- [ ] Action 모델 정의
- [ ] RobotCandidate 모델 정의
- [ ] RobotTask 모델 정의

## 4.2 상태 스키마 설계
- [ ] current_state 필드 목록 확정
- [ ] derived_features 필드 목록 확정
- [ ] device_status 필드 목록 확정
- [ ] constraints 필드 목록 확정
- [ ] sensor_quality 필드 목록 확정
- [ ] weather_context 필드 목록 확정
- [ ] growth_stage 필드 목록 확정
- [ ] enum 값 정리
- [ ] JSON schema 작성
- [ ] 예제 payload 작성

## 4.3 액션 스키마 설계
- [ ] action_type 목록 확정
- [ ] 장치별 parameter schema 설계
- [ ] irrigation schema 설계
- [ ] shade schema 설계
- [ ] vent schema 설계
- [ ] fan schema 설계
- [ ] heating schema 설계
- [ ] co2 schema 설계
- [ ] robot task schema 설계
- [ ] follow_up schema 설계
- [ ] decision schema 작성

## 4.4 이벤트 스키마 설계
- [ ] sensor.snapshot.updated schema
- [ ] zone.state.updated schema
- [ ] action.requested schema
- [ ] action.blocked schema
- [ ] action.executed schema
- [ ] robot.task.created schema
- [ ] robot.task.failed schema
- [ ] alert.created schema
- [ ] approval.requested schema

---

# 5. 데이터베이스 설계 및 구축

## 5.1 PostgreSQL 스키마
- [ ] zones 테이블 작성
- [ ] sensors 테이블 작성
- [ ] devices 테이블 작성
- [ ] policies 테이블 작성
- [ ] llm_decisions 테이블 작성
- [ ] device_commands 테이블 작성
- [ ] alerts 테이블 작성
- [ ] approvals 테이블 작성
- [ ] robot_candidates 테이블 작성
- [ ] robot_tasks 테이블 작성

## 5.2 인덱스 및 성능
- [ ] zone_id 인덱스 설정
- [ ] timestamp 인덱스 설정
- [ ] device command 조회 인덱스 설정
- [ ] robot task 조회 인덱스 설정
- [ ] partition 필요성 검토
- [ ] 보관 주기 정책 검토

## 5.3 시계열 저장소
- [ ] TimescaleDB vs InfluxDB 결정
- [ ] sensor_readings 스키마 작성
- [ ] zone_state_snapshots 스키마 작성
- [ ] retention policy 작성
- [ ] downsampling 정책 작성
- [ ] 압축 정책 작성

## 5.4 마이그레이션/시드
- [ ] migration 초기화
- [ ] seed 데이터 작성
- [ ] 기본 zone 등록
- [ ] 기본 sensor 등록
- [ ] 기본 device 등록
- [ ] 기본 policy 등록
- [ ] 기본 enum/reference 데이터 등록

---

# 6. 센서 수집 파이프라인

## 6.1 수집 아키텍처 정의
- [ ] polling vs event 방식 결정
- [x] 샘플링 주기 결정 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [ ] timestamp 기준 정의
- [ ] 데이터 손실 처리 방식 정의
- [ ] 재전송 정책 정의
- [ ] 장애 시 buffer 정책 정의
- [x] AI 학습용 raw data와 feature data 분리 저장 방식 정의 (`AI_MLOPS_PLAN.md`, `docs/sensor_collection_plan.md`)
- [x] 센서 이벤트와 장치 명령 시간축 정렬 방식 정의 (`AI_MLOPS_PLAN.md`)
- [x] calibration_version 저장 방식 정의 (`docs/sensor_collection_plan.md`)

## 6.1.1 센서 수집 계획 보강
- [x] 환경 센서 목록 확정: 온도, 습도, CO2, 광량/PAR, 일사량 (`docs/sensor_collection_plan.md`)
- [x] 배지/양액 센서 목록 확정: 함수율, EC, pH, 배액량, 배액 EC/pH, 양액 온도 (`docs/sensor_collection_plan.md`)
- [x] 외기 센서 목록 확정: 외기 온도, 외기 습도, 풍속, 강우, 외부 일사 (`docs/sensor_collection_plan.md`)
- [x] 장치 상태 수집 목록 확정: 팬, 차광, 환기창, 관수 밸브, 난방기, CO2 공급기, 제습기 (`docs/sensor_collection_plan.md`)
- [x] 비전 데이터 수집 계획 작성: 작물 이미지, 숙도, 병징, 잎 상태, 수확 후보 (`docs/sensor_collection_plan.md`)
- [x] 운영 이벤트 수집 계획 작성: 관수 실행, 차광 변경, 작업자 개입, 알람, 수동 override (`docs/sensor_collection_plan.md`)
- [x] sensor_id/device_id/zone_id naming 규칙 확정 (`docs/sensor_collection_plan.md`)
- [x] sensor quality flag 기준 확정 (`docs/sensor_collection_plan.md`)
- [x] 센서별 수집 주기와 단위 확정 (`docs/sensor_collection_plan.md`, `data/examples/sensor_catalog_seed.json`)
- [x] AI 학습 반영 가능 여부별 데이터 우선순위 지정 (`docs/sensor_collection_plan.md`)

## 6.2 센서 어댑터 구현
- [ ] 온도/습도 센서 어댑터 작성
- [ ] CO2 센서 어댑터 작성
- [ ] 광량 센서 어댑터 작성
- [ ] 함수율 센서 어댑터 작성
- [ ] EC 센서 어댑터 작성
- [ ] pH 센서 어댑터 작성
- [ ] 외기 센서 어댑터 작성
- [ ] 각 어댑터 timeout 처리
- [ ] 각 어댑터 retry 처리
- [ ] 품질 플래그 생성 로직 작성

## 6.3 sensor-ingestor 서비스
- [ ] 프로젝트 초기화
- [ ] 설정 파일 구조 작성
- [ ] sensor poller 구현
- [ ] parser 구현
- [ ] validator 구현
- [ ] normalizer 구현
- [ ] MQTT publisher 구현
- [ ] timeseries writer 구현
- [ ] health check endpoint 작성
- [ ] metrics endpoint 작성

## 6.4 센서 품질 관리
- [ ] outlier rule 정의
- [ ] stale sensor rule 정의
- [ ] jump detection rule 정의
- [ ] missing data rule 정의
- [ ] quality_flag 계산기 구현
- [ ] sensor anomaly alert 연결

---

# 7. 상태 추정(state-estimator)

## 7.1 특징량 정의
- [ ] VPD 계산식 검증
- [ ] DLI 계산 방식 정의
- [ ] 1분 평균 정의
- [ ] 5분 평균 정의
- [ ] 10분 변화율 정의
- [ ] 30분 변화율 정의
- [ ] 관수 후 회복률 정의
- [ ] 배액률 정의
- [ ] 스트레스 점수 정의
- [ ] 생육 단계 반영 방식 정의

## 7.2 feature builder 구현
- [ ] raw sensor loader 작성
- [ ] aggregation 함수 작성
- [ ] VPD calculator 작성
- [ ] trend calculator 작성
- [ ] stress score calculator 작성
- [ ] substrate recovery calculator 작성
- [ ] derived feature validator 작성
- [ ] snapshot serializer 작성

## 7.3 zone state 생성
- [ ] current_state 조합
- [ ] derived_features 조합
- [ ] device_status 조합
- [ ] constraints placeholder 조합
- [ ] weather context 조합
- [ ] final state schema validation
- [ ] snapshot DB 저장
- [ ] state updated event 발행

---

# 8. 정책 엔진(policy-engine)

## 8.1 정책 카테고리 정리
- [ ] hard block 정책 정의
- [ ] approval 정책 정의
- [ ] range limit 정책 정의
- [ ] scheduling 정책 정의
- [ ] sensor quality 정책 정의
- [ ] robot safety 정책 정의

## 8.2 정책 DSL/JSON 포맷 정의
- [ ] field/operator/value 포맷 정의
- [ ] AND/OR 표현 방식 정의
- [ ] action_type 대상 지정 방식 정의
- [ ] 조건 템플릿 정의
- [ ] rule version 필드 정의
- [ ] enabled/disabled 정책 정의
- [ ] scope(zone/global) 정의

## 8.3 정책 엔진 구현
- [ ] policy loader 작성
- [ ] evaluator 작성
- [ ] action constraint evaluator 작성
- [ ] state constraint evaluator 작성
- [ ] robot constraint evaluator 작성
- [ ] explanation builder 작성
- [ ] blocked action event 발행
- [ ] requires approval event 발행

## 8.4 기본 정책 등록
- [ ] 야간 관수 제한 정책 등록
- [ ] 센서 품질 불량 제한 정책 등록
- [ ] 과습 시 관수 금지 정책 등록
- [ ] 강풍 시 환기 제한 정책 등록
- [ ] 작업자 존재 시 로봇 금지 정책 등록
- [ ] 장치 응답 불량 시 재명령 금지 정책 등록
- [ ] setpoint 급변 제한 정책 등록

---

# 9. LLM 오케스트레이터

## 9.1 역할 정의
- [ ] evaluate_zone 호출 흐름 정의
- [ ] event-driven 호출 흐름 정의
- [ ] on-demand 호출 흐름 정의
- [ ] robot prioritization 호출 흐름 정의
- [ ] alert summary 호출 흐름 정의
- [ ] RAG retrieval 호출 흐름 정의

## 9.2 프롬프트 설계
- [ ] 시스템 프롬프트 초안 작성
- [ ] 역할 제한 문구 작성
- [ ] 안전 원칙 문구 작성
- [ ] RAG 검색 근거 우선 사용 문구 작성
- [ ] 검색 근거 부족 시 보수적 판단 문구 작성
- [ ] JSON only 출력 규칙 작성
- [ ] confidence 규칙 작성
- [ ] 불확실성 처리 규칙 작성
- [ ] follow_up 규칙 작성
- [ ] citations 출력 규칙 작성
- [ ] 장치 enum 삽입 방식 설계
- [ ] constraints 삽입 방식 설계

## 9.3 툴/함수 설계
- [x] get_zone_state 정의 (`docs/agent_tool_design.md`)
- [x] get_recent_trend 정의 (`docs/agent_tool_design.md`)
- [x] get_active_constraints 정의 (`docs/agent_tool_design.md`)
- [ ] get_device_status 정의
- [ ] get_weather_context 정의
- [x] search_cultivation_knowledge 정의 (`docs/agent_tool_design.md`)
- [ ] search_site_sop 정의
- [ ] get_retrieval_citations 정의
- [ ] get_vision_candidates 정의
- [ ] request_device_action 정의
- [ ] request_robot_task 정의
- [x] request_human_approval 정의 (`docs/agent_tool_design.md`)
- [x] log_decision 정의 (`docs/agent_tool_design.md`)

## 9.4 llm-orchestrator 구현
- [ ] API client 구성
- [ ] model config 구조 작성
- [ ] prompt renderer 구현
- [ ] rag-retriever client 구현
- [ ] retrieved_context 조합 로직 작성
- [ ] tool registry 구현
- [ ] structured output parser 구현
- [ ] retry 전략 구현
- [ ] timeout 전략 구현
- [ ] malformed JSON 복구 전략 구현
- [ ] citations 저장 로직 구현
- [ ] decision logger 구현
- [ ] evaluation endpoint 작성

## 9.5 응답 검증
- [ ] action_type enum 검증
- [ ] parameter schema 검증
- [ ] confidence 범위 검증
- [ ] follow_up 필드 검증
- [ ] citations 필드 검증
- [ ] retrieval_coverage 필드 검증
- [ ] robot task schema 검증
- [ ] natural language leakage 검토
- [ ] policy precheck 연결

---

# 10. 실행 게이트(execution-gateway)

## 10.1 검증 흐름 정의
- [ ] schema validation 단계 정의
- [ ] range validation 단계 정의
- [ ] device availability check 단계 정의
- [ ] duplicate action check 단계 정의
- [ ] cooldown check 단계 정의
- [ ] policy re-evaluation 단계 정의
- [ ] approval routing 단계 정의
- [ ] audit logging 단계 정의

## 10.2 게이트 구현
- [ ] validator 모듈 작성
- [ ] command normalizer 작성
- [ ] range clamp 전략 정의
- [ ] duplicate detector 작성
- [ ] cooldown manager 작성
- [ ] approval handler 작성
- [ ] rejection reason builder 작성
- [ ] execution dispatcher 작성

## 10.3 승인 체계
- [ ] 저위험 액션 목록 확정
- [ ] 중위험 액션 목록 확정
- [ ] 고위험 액션 목록 확정
- [ ] 승인자 역할 정의
- [ ] 승인 UI 요구사항 작성
- [ ] 승인 timeout 정책 정의
- [ ] 거절 시 fallback 정책 정의

---

# 11. PLC/장치 연동

## 11.1 프로토콜 설계
- [ ] PLC 통신 방식 확인
- [ ] Modbus address map 확보
- [ ] OPC UA node map 확보
- [ ] register/write 안전 규칙 정의
- [ ] readback 검증 방식 정의
- [ ] 장애 코드 정의

## 11.2 plc-adapter 구현
- [ ] 연결 초기화 구현
- [ ] reconnect 로직 구현
- [ ] write command 구현
- [ ] readback 구현
- [ ] timeout 처리 구현
- [ ] retry 처리 구현
- [ ] ack 처리 구현
- [ ] result mapping 구현
- [ ] adapter health check 작성

## 11.3 장치별 명령 구현
- [ ] 순환팬 명령 매핑
- [ ] 차광커튼 명령 매핑
- [ ] 관수 밸브 명령 매핑
- [ ] 환기창 명령 매핑
- [ ] 난방기 명령 매핑
- [ ] CO2 명령 매핑
- [ ] 긴급 정지 명령 분리
- [ ] 수동 override 명령 분리

## 11.4 실행 검증
- [ ] write 후 readback 비교
- [ ] 상태 반영 시간 측정
- [ ] 무응답 장치 감지
- [ ] 부분 성공 처리 방식 정의
- [ ] rollback 가능 액션 정의
- [ ] safe mode 전환 조건 연결

---

# 12. API 서버 / 백엔드

## 12.1 공통 백엔드
- [ ] FastAPI 프로젝트 초기화
- [ ] settings 모듈 작성
- [ ] logger 설정
- [ ] exception handler 작성
- [ ] response model 작성
- [ ] auth 방식 정의
- [ ] role 기반 권한 정의
- [ ] OpenAPI 문서 정리

## 12.2 주요 API
- [ ] GET /zones
- [ ] GET /zones/{zone_id}/state
- [ ] GET /zones/{zone_id}/history
- [ ] POST /decisions/evaluate-zone
- [ ] POST /actions/execute
- [ ] POST /actions/approve
- [ ] GET /actions/history
- [ ] GET /alerts
- [ ] GET /policies
- [ ] POST /robot/tasks

## 12.3 테스트
- [ ] API unit test 작성
- [ ] schema validation test 작성
- [ ] auth test 작성
- [ ] error response test 작성
- [ ] load test 최소 시나리오 작성

---

# 13. 모니터링/알람/감사

## 13.1 로깅 설계
- [ ] request log 포맷 정의
- [ ] decision log 포맷 정의
- [ ] command log 포맷 정의
- [ ] robot log 포맷 정의
- [ ] policy block log 포맷 정의
- [ ] sensor anomaly log 포맷 정의

## 13.2 메트릭 설계
- [ ] sensor ingest rate
- [ ] stale sensor count
- [ ] decision latency
- [ ] malformed response count
- [ ] blocked action count
- [ ] approval pending count
- [ ] command success rate
- [ ] robot task success rate
- [ ] safe mode count

## 13.3 알람 설계
- [ ] 고온 알람
- [ ] 고습 알람
- [ ] 센서 이상 알람
- [ ] 장치 무응답 알람
- [ ] 정책 차단 과다 알람
- [ ] decision 실패 알람
- [ ] robot safety 알람
- [ ] safe mode 진입 알람

## 13.4 감사 체계
- [ ] decision trace 저장
- [ ] source state 저장
- [ ] policy evaluation 결과 저장
- [ ] final execution 결과 저장
- [ ] operator override 저장
- [ ] approval action 저장
- [ ] 모델/프롬프트 버전 저장

---

# 14. 프론트엔드/운영 대시보드

## 14.1 기본 화면 정의
- [ ] zone overview 화면 설계
- [ ] real-time sensor 화면 설계
- [ ] decision 로그 화면 설계
- [ ] action 승인 화면 설계
- [ ] alert 화면 설계
- [ ] robot task 화면 설계
- [ ] policy 관리 화면 설계

## 14.2 시각화
- [ ] 온도/습도 시계열 차트
- [ ] CO2 시계열 차트
- [ ] 함수율/EC/pH 시계열 차트
- [ ] 장치 상태 카드
- [ ] 현재 제약 조건 카드
- [ ] 최근 결정 카드
- [ ] blocked/rejected 명령 리스트
- [ ] robot candidate 리스트

## 14.3 운영 기능
- [ ] 수동 명령 입력 UI
- [ ] 자동/수동 모드 전환 UI
- [ ] 승인/거절 UI
- [ ] 주석/운영 메모 UI
- [ ] 문제 사례 태깅 UI

---

# 15. 시뮬레이터/디지털 트윈

## 15.1 시뮬레이션 목표 정의
- [ ] 환경 반응 시뮬레이션 범위 정의
- [ ] 관수 반응 시뮬레이션 범위 정의
- [ ] 차광 영향 시뮬레이션 범위 정의
- [ ] 환기 영향 시뮬레이션 범위 정의
- [ ] 센서 이상 주입 방식 정의
- [ ] 장치 stuck 주입 방식 정의

## 15.2 시나리오 구축
- [ ] 맑은 낮 시나리오
- [ ] 흐린 날 시나리오
- [ ] 급격한 일사 증가 시나리오
- [ ] 고온 외기 시나리오
- [ ] 센서 드리프트 시나리오
- [ ] 함수율 센서 고장 시나리오
- [ ] 관수 밸브 불응답 시나리오
- [ ] 네트워크 지연 시나리오
- [ ] 사람 접근 시 로봇 중지 시나리오

## 15.3 시뮬레이터 구현
- [ ] 환경 상태 모델 작성
- [ ] 장치 반응 모델 작성
- [ ] 관수 반응 모델 작성
- [ ] 잡음 주입 기능 작성
- [ ] 이벤트 주입 기능 작성
- [ ] replay runner 작성
- [ ] score calculator 작성

## 15.4 시뮬레이터 평가
- [ ] 목표 유지율 측정
- [ ] 불필요 명령 수 측정
- [ ] 차단되지 않은 위험 명령 수 측정
- [ ] 승인이 필요한 명령 비율 측정
- [ ] safe mode 진입 빈도 측정

---

# 16. 비전 파이프라인

## 16.1 데이터 준비
- [ ] 수확 대상 이미지 수집
- [ ] 숙도 레이블 정의
- [ ] 병징 레이블 정의
- [ ] occlusion 레이블 정의
- [ ] reachable 레이블 정의
- [ ] annotation 가이드 작성
- [ ] 데이터셋 분할
- [ ] 증강 전략 정의

## 16.2 모델 개발
- [ ] detection baseline 선정
- [ ] segmentation 필요성 검토
- [ ] ripeness score 모델 설계
- [ ] disease suspicion score 모델 설계
- [ ] reachable classifier 설계
- [ ] occlusion 판정 로직 설계

## 16.3 추론 서비스
- [ ] vision-inference 프로젝트 초기화
- [ ] 모델 로딩 구현
- [ ] inference endpoint 작성
- [ ] candidate schema serializer 작성
- [ ] 결과 저장 로직 작성
- [ ] 이미지 링크 저장 로직 작성

## 16.4 결과 검증
- [ ] precision/recall 계산
- [ ] 숙도 score calibration
- [ ] false positive 사례 정리
- [ ] false negative 사례 정리
- [ ] 실패 이미지 태깅 체계 정의

---

# 17. 로봇 태스크 매니저

## 17.1 작업 모델 정의
- [ ] harvest task schema 정의
- [ ] inspect task schema 정의
- [ ] skip reason schema 정의
- [ ] robot capability schema 정의
- [ ] work area schema 정의

## 17.2 후보 생성/정렬
- [ ] ripeness threshold 정의
- [ ] reachable filter 정의
- [ ] occlusion filter 정의
- [ ] disease exclusion rule 정의
- [ ] time budget rule 정의
- [ ] max target count rule 정의
- [ ] priority score 공식 정의

## 17.3 LLM 연동
- [ ] robot prioritization prompt 작성
- [ ] candidate summary 생성기 작성
- [ ] robot task JSON parser 작성
- [ ] fallback deterministic sorter 작성
- [ ] approval 필요 조건 정의

## 17.4 로봇 제어기 인터페이스
- [ ] task enqueue API 정의
- [ ] task status callback 정의
- [ ] task failure callback 정의
- [ ] emergency stop callback 정의
- [ ] human detected callback 정의

---

# 18. 테스트 전략

## 18.1 단위 테스트
- [ ] schema validator 테스트
- [ ] VPD calculator 테스트
- [ ] trend calculator 테스트
- [ ] policy evaluator 테스트
- [ ] action validator 테스트
- [ ] duplicate detector 테스트
- [ ] cooldown manager 테스트

## 18.2 통합 테스트
- [ ] sensor → state-estimator 통합 테스트
- [ ] state-estimator → policy-engine 통합 테스트
- [ ] RAG retrieval → llm-orchestrator 통합 테스트
- [ ] policy-engine → llm-orchestrator 통합 테스트
- [ ] llm-orchestrator → execution-gateway 통합 테스트
- [ ] execution-gateway → plc-adapter 통합 테스트
- [ ] vision → robot-task-manager 통합 테스트

## 18.3 E2E 테스트
- [ ] 5분 주기 zone 평가 E2E
- [ ] RAG 근거 검색 포함 zone 평가 E2E
- [ ] 고온 이벤트 E2E
- [ ] 센서 고장 E2E
- [ ] 장치 무응답 E2E
- [ ] 로봇 후보 생성 E2E
- [ ] 승인 흐름 E2E
- [ ] safe mode 전환 E2E

## 18.4 현장 검증 테스트
- [ ] shadow mode 운영
- [ ] 사람 승인 모드 운영
- [ ] 저위험 자동 실행 운영
- [ ] 운영 로그 리뷰
- [ ] 오경보/미경보 분석
- [ ] 현장 피드백 반영

---

# 19. 배포/인프라

## 19.1 배포 전략
- [ ] Docker 이미지 작성
- [ ] docker-compose 개발환경 구성
- [ ] staging 배포 구조 설계
- [ ] production 배포 구조 설계
- [ ] 비밀정보 관리 방식 정의
- [ ] 롤백 전략 정의

## 19.2 운영 인프라
- [ ] DB 백업 정책 정의
- [ ] object storage 백업 정책 정의
- [ ] 로그 보관 정책 정의
- [ ] 메트릭 수집 인프라 구성
- [ ] 대시보드 구성
- [ ] 장애 알람 채널 연동

## 19.3 안정성
- [ ] service restart 정책 정의
- [ ] circuit breaker 검토
- [ ] queue backlog 대응 전략 정의
- [ ] network partition 대응 전략 정의
- [ ] degraded mode 정책 정의

---

# 20. 단계적 운영 전환

## 20.1 Shadow Mode
- [ ] LLM은 추천만 생성
- [ ] 실제 장치 제어 없음
- [ ] 운영자 수동 비교 검토
- [ ] 추천 적합도 기록
- [ ] 오판 사례 수집

## 20.2 Approval Mode
- [ ] 모든 액션 승인 후 실행
- [ ] 승인/거절 이유 기록
- [ ] 과도한 승인 요청 분석
- [ ] 승인 기준 튜닝

## 20.3 Limited Auto Mode
- [ ] 저위험 장치만 자동
- [ ] 차광 자동 적용
- [ ] 순환팬 자동 적용
- [ ] 짧은 관수 자동 적용
- [ ] rollback 가능 여부 검증

## 20.4 Expanded Auto Mode
- [ ] 더 많은 zone 적용
- [ ] 더 많은 액션 적용
- [ ] 계절별 정책 반영
- [ ] 장치 조합 전략 적용
- [ ] 운영 KPI 비교

---

# 21. 재학습/고도화

## 21.1 운영 로그 데이터화
- [ ] 좋은 결정 사례 태깅
- [ ] 나쁜 결정 사례 태깅
- [ ] blocked 사례 분류
- [ ] 승인 거절 사례 분류
- [ ] 사람 수정 사례 분류
- [ ] 센서 이상 사례 분류
- [ ] 로봇 실패 사례 분류
- [ ] 센서 변화와 작물 반응 지연시간 매핑
- [ ] 운영자 승인/거절 이유 구조화
- [ ] AI 추천과 실제 조치 차이 분석

## 21.2 데이터셋 재생성
- [ ] 운영 로그 → 학습 샘플 변환기 작성
- [ ] preference pair 생성기 검토
- [ ] 실패사례 보강 데이터 생성
- [ ] 계절/품종별 샘플 균형화
- [ ] prompt version별 성능 비교
- [ ] RAG 문서 업데이트 후보 생성
- [ ] eval regression set 자동 갱신

## 21.3 모델/정책 개선
- [ ] 파인튜닝 재실행
- [ ] 시스템 프롬프트 개선
- [ ] 정책 엔진 규칙 추가
- [ ] approval threshold 튜닝
- [ ] confidence threshold 튜닝
- [ ] fallback 전략 개선
- [ ] champion/challenger 비교 평가
- [ ] 모델 승격/롤백 기록 저장

---

# 22. 권장 마일스톤

## M1. 도메인/스키마 확정
- [ ] 요구사항 문서 완료
- [ ] 센서/장치 인벤토리 완료
- [ ] state/action schema 완료
- [ ] 학습 데이터 포맷 완료

## M2. 데이터/파인튜닝 완료
- [ ] 학습셋 구축 완료
- [ ] 파인튜닝 완료
- [ ] 평가셋 통과
- [ ] JSON 출력 안정화

## M3. 센서/정책/LLM 연결 완료
- [ ] 센서 수집 완료
- [ ] state-estimator 완료
- [ ] policy-engine 완료
- [ ] llm-orchestrator 완료

## M4. 안전 실행 완료
- [ ] execution-gateway 완료
- [ ] plc-adapter 완료
- [ ] 승인 체계 완료
- [ ] shadow mode 완료

## M5. 현장 자동화 1차 완료
- [ ] approval mode 완료
- [ ] limited auto mode 완료
- [ ] KPI 측정 시작

## M6. 비전/로봇 연동 완료
- [ ] vision pipeline 완료
- [ ] robot-task-manager 완료
- [ ] 반자동 작업 성공

## M7. 운영 고도화 완료
- [ ] retraining loop 완료
- [ ] simulator/replay 검증 완료
- [ ] 확대 적용 준비 완료

---

# 23. 즉시 착수 우선순위

## 이번 주 바로 시작할 일
- [x] state schema 초안 작성 (`schemas/state_schema.json`)
- [x] action schema 초안 작성 (`schemas/action_schema.json`)
- [x] RAG 문서 범위와 메타데이터 초안 작성 (`docs/rag_source_inventory.md`, `docs/rag_indexing_plan.md`)
- [x] 적고추/건고추 재배 문서 수집 목록 작성 (`docs/rag_source_inventory.md`)
- [x] 기존 파인튜닝 데이터 재분류 (`docs/dataset_taxonomy.md`, `data/examples/`)
- [ ] 행동추천 JSON 샘플 100개 작성
- [ ] 금지행동 샘플 100개 작성
- [x] sensor/device inventory 문서 작성 (`docs/sensor_collection_plan.md`, `docs/sensor_installation_inventory.md`, `data/examples/sensor_catalog_seed.json`)
- [ ] policy 초안 20개 작성
- [ ] llm-orchestrator 인터페이스 초안 작성

## 그 다음 주
- [x] RAG vector store PoC 작성 (`scripts/build_chroma_index.py`, `scripts/rag_chroma_store.py`)
- [x] 검색 품질 평가셋 작성 (`evals/rag_retrieval_eval_set.jsonl`, `scripts/evaluate_rag_retrieval.py`)
- [ ] sensor-ingestor MVP 작성
- [ ] state-estimator MVP 작성
- [ ] policy-engine MVP 작성
- [ ] 파인튜닝 재실행
- [ ] evaluate-zone API 작성
- [ ] decision log 저장 구조 구현

## 그 다음 단계
- [ ] execution-gateway MVP 구현
- [ ] plc-adapter 테스트 연결
- [ ] approval UI 초안 작성
- [ ] shadow mode 운영 개시

---

# 24. 최종 체크리스트

출시 전 아래 항목을 모두 만족해야 한다.

- [ ] LLM이 허용되지 않은 action_type을 출력하지 않는다
- [ ] RAG 검색 결과가 decision log에 citation으로 남는다
- [ ] 검색 근거가 부족할 때 LLM이 보수적으로 응답한다
- [ ] malformed JSON이 운영을 중단시키지 않는다
- [ ] 센서 이상 시 자동화가 안전하게 축소된다
- [ ] 장치 무응답 시 safe mode가 동작한다
- [ ] 승인 필수 액션이 우회되지 않는다
- [ ] 모든 결정과 실행이 audit log로 남는다
- [ ] 사람이 언제든 수동 override 할 수 있다
- [ ] 로봇 작업 시 사람 감지 규칙이 동작한다
- [ ] 시뮬레이터 핵심 시나리오를 통과한다
- [ ] shadow mode에서 충분한 적합도를 보였다

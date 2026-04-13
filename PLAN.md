# PLAN.md
 
# 온실 스마트팜 고추 재배 자동화를 위한 농업용 LLM/제어 시스템 개발 계획

## 관련 문서
- [저장소 README](README.md)
- [프로젝트 현황 요약](PROJECT_STATUS.md)
- [AI 모델 준비 및 MLOps 계획](AI_MLOPS_PLAN.md)
- [적고추 전문가 AI Agent 구축 계획](EXPERT_AI_AGENT_PLAN.md)
- [현장 baseline](docs/site_scope_baseline.md)
- [계절별 운영 범위](docs/seasonal_operation_ranges.md)
- [센서 모델 shortlist](docs/sensor_model_shortlist.md)
- [장치 setpoint 범위](docs/device_setpoint_ranges.md)
- [장치 운전 경험 규칙](docs/device_operation_rules.md)
- [평가셋 확장 계획](docs/eval_scaleup_plan.md)
- [세부 개발 Todo](todo.md)
- [8주 일정 계획](schedule.md)
- [작업 로그](WORK_LOG.md)

## 1. 프로젝트 목표

본 프로젝트의 목표는 **적고추(건고추) 온실 운영 지식을 RAG로 검색하고, 고추 재배 운영 태스크에 맞게 파인튜닝된 LLM**을 기반으로, 온실의 실시간 환경 데이터를 센서로부터 수집하고, 이를 해석하여 **안전한 자동 의사결정**을 수행하며, 필요시 **온실 장치 제어**와 **로봇암 작업 지시**까지 연결되는 운영 시스템을 구축하는 것이다.

현재 계획 기준 현장은 다음처럼 고정한다.

- 대상 site: `gh-01`
- 시설 형태: `300평 연동형 비닐온실 1동`
- 운영 구조: 물리적으로는 대형 온실 1개, 논리적으로는 `zone-a`, `zone-b`, `outside`, `nutrient-room`, `dry-room` 5개 zone
- 품종 운영 범위: `건고추/고춧가루용 적고추`
- 1차 품종 shortlist: `왕조`, `칼탄열풍`, `조생강탄`
- 기본 기준 품종: `왕조`
- 재배 환경 기준: 육묘용 `Grodan Delta 6.5` block, 본재배용 `Grodan GT Master` slab
- 핵심 센서 1차 shortlist:
  - 온습도: `Vaisala HMP110`
  - CO2: `Vaisala GMP252`
  - PAR: `Apogee SQ-522-SS`
  - 배지 함수율: `METER TEROS 12`
  - 양액 pH/EC: `Bluelab Guardian Inline Wi-Fi`
  - 외기 통합: `Vaisala WXT536`
- 공식 재배 자료 기준 환경 기본값:
  - 낮 `25~28℃`
  - 밤 `18℃ 전후`
  - 허용 운전 밴드: 낮 `25~30℃`, 밤 `18~20℃`
  - 정식기 보수 기준: 밤 `16℃ 이상`

근권·양액·배액 판단은 위 Grodan block/slab 기반의 soilless 재배 환경을 기본 전제로 설계한다.

이 시스템은 다음 원칙을 따른다.

- LLM은 **상위 판단 및 계획 엔진**으로 사용한다.
- RAG는 최신 재배 매뉴얼, 현장 SOP, 품종/지역별 기준, 정책 문서를 검색하는 **외부 지식 계층**으로 사용한다.
- 파인튜닝은 JSON 출력, 행동 추천 형식, 안전 거절 패턴, follow_up 생성 등 **운영 행동 양식**을 학습시키는 데 사용한다.
- 실시간 연속 제어는 **PLC / 규칙 엔진 / PID / 상태기계**가 담당한다.
- 모든 실행은 **정책 엔진과 안전 게이트**를 통과해야 한다.
- 로봇암은 LLM이 직접 제어하지 않고, **비전 + 작업계획 + 로봇 제어기**가 실제 동작을 담당한다.
- 전체 시스템은 **기록 가능, 검증 가능, 재현 가능**해야 한다.

---

## 2. 최종 시스템 범위

## 2.1 주요 기능

### A. 도메인 판단
- RAG로 검색한 적고추/건고추 재배 지식에 기반한 환경 상태 해석
- 생육 단계별 환경 적정성 판단
- 이상 상황 탐지 및 원인 추정
- 관수/환기/차광/CO2/양액 관련 상위 전략 수립

### B. 장치 자동화
- 센서 실시간 수집
- 특징량 생성(VPD, 추세, 스트레스 점수, 회복률 등)
- 정책 기반 허용/금지 판단
- 저위험 액션 자동 실행
- 중·고위험 액션 승인 요청

### C. 로봇 작업 연동
- 비전 기반 수확 대상 인식
- LLM 기반 작업 우선순위 결정
- 로봇 작업 큐 생성
- 작업 결과 로깅 및 피드백

### D. 운영/감사/재학습
- 의사결정 로그 저장
- 장치 명령 이력 저장
- 실행 결과와 센서 반응 저장
- 파인튜닝/평가용 데이터셋 자동 축적

### E. 운영자 통합 제어 웹 UI
- 운영자가 온실 운영을 한 화면에서 모니터링하고 승인/수동 조작할 수 있는 **한국어 기본 웹 UI**를 제공한다. 기본 언어는 한글로 표현하고, 기술 필드명(예: `validator_reason_codes`)은 원문 유지한다.
- ops-api의 `GET /dashboard`가 단일 페이지로 사이드바 네비게이션과 다음 메뉴를 노출한다. 루트 `/`는 `/dashboard`로 307 리다이렉트한다.
  - `대시보드`: 운영 지표 카드, 존 상태 요약, shadow window, 최근 알림/실행 요약
  - `존 모니터링`: Zone History Chart (air/rh/vpd/substrate_moisture/substrate_temp/co2/par/feed_ec/drain_ec/feed_ph/drain_ph 11개 지표 SVG 스파크라인), zone 전체 목록
  - `결정 / 승인`: 신규 Decision 요청 폼, Real-time Decisions 리스트 (승인/거절/수동 Execute/문제 사례 태깅 버튼)
  - `알림`: Alerts 리스트 (severity 필터 + validator reason)
  - `로봇`: Robot Tasks, Robot Candidates
  - `장치 / 제약`: Zone별 최신 device_status, Active Constraints
  - `정책 / 이벤트`: Policy Management (live toggle), Policy Events
  - `Shadow Mode`: Shadow Window Summary 상세, 리뷰 가이드
  - `시스템`: Execution History, Runtime Info (actor/role/auth_mode)
- UI는 backend 없이 SPA 하나로 동작하되 5초 주기로 `/dashboard/data`를 폴링해 모든 카드를 재렌더한다. 각 뷰 전환은 클라이언트 사이드 토글로 처리하며, 새 데이터는 `fetch('/dashboard/data')` 한 번으로 공유한다.
- 운영 조작 경로는 API가 이미 제공하는 엔드포인트로만 구성한다: `/decisions/evaluate-zone`, `/actions/approve`, `/actions/reject`, `/actions/execute`, `/shadow/reviews`, `/runtime/mode`, `/policies/{id}` (enable/disable 토글), `/shadow/cases/capture`.
- 권한은 백엔드 `auth.py`의 `viewer/operator/service/admin` 역할을 그대로 사용하며, `auth_mode=disabled` 로컬 개발에서는 헤더 기반 role override로 뷰를 시연한다.

---

## 3. 권장 시스템 아키텍처

## 3.1 계층 구조

### 1) 현장 계층
- 환경 센서
- 양액/배지 센서
- 외기 센서
- 카메라
- 액추에이터
- 로봇암/이동 플랫폼

### 2) 제어 계층
- PLC 또는 산업용 PC
- Modbus TCP/RTU
- OPC UA
- MQTT 게이트웨이
- 인터록
- 비상정지
- 수동/자동 모드

### 3) 플랫폼 계층
- MQTT broker
- TimescaleDB 또는 InfluxDB
- PostgreSQL
- Redis
- Object Storage
- Vector Store 또는 Vector DB

### 4) AI/오케스트레이션 계층
- state-estimator
- policy-engine
- rag-retriever
- llm-orchestrator
- execution-gateway
- vision-inference
- robot-task-manager
- audit-monitor

### 5) 운영자 통합 제어 웹 UI 계층
- ops-api `/dashboard` (단일 SPA, 한국어 기본, 사이드바 네비게이션 + 9개 뷰)
- 루트 `/` 307 리다이렉트 → `/dashboard`
- 백엔드와의 연결은 `ApiResponse` 엔벨로프(`data/meta/actor`) JSON 한 종류만 사용
- 주기 폴링(5s) 기반 refresh, 각 카드에 action 버튼(승인/거절/수동 Execute/문제 사례 태깅/정책 토글/모드 전환) 포함
- 본 시스템의 실제 "운영자 얼굴"이고, Phase 8 단계적 현장 적용 시 UI 확장의 base가 된다

---

## 4. 핵심 설계 원칙

## 4.1 LLM 역할 분리
LLM은 다음만 수행한다.

- 상태 해석
- 위험도 판단
- 추천 행동 생성
- 예외 상황 설명
- 로봇 태스크 우선순위 결정
- 보고서/알람 문구 생성

LLM은 다음을 직접 수행하지 않는다.

- 초단위 연속 제어
- 비상 제어
- 인터록 해제
- 장치 직접 on/off
- 로봇 관절 좌표 제어
- 충돌 회피 최종 결정

## 4.2 실행 안전성 확보
모든 명령은 다음 절차를 거친다.

1. 입력 데이터 품질 검사
2. 정책 엔진 검사
3. JSON schema 검사
4. 장치 상태 검사
5. 중복/충돌 검사
6. 위험도 분류
7. 자동 실행 또는 승인 요청
8. 결과 확인 및 로깅

## 4.3 운영 가능성 확보
- 모든 모델/프롬프트/정책은 버전 관리한다.
- 모든 의사결정은 입력/출력/실행 결과를 함께 저장한다.
- 장애 시 safe mode로 전환한다.
- 수동 개입이 항상 가능해야 한다.

## 4.4 평가셋 운영 원칙

- 현재 fine-tuning benchmark `24건`은 빠른 회귀 확인용 `core regression set`으로 유지한다.
- 승격 판단은 `core24`만으로 하지 않고 `extended120` 이상에서 다시 수행한다.
- 제품화 판단은 `extended160` 이상에서 수행한다.
- `forbidden_action`, `failure_response`, `edge_case`, `seasonal`은 최소치 미달 상태에서 새 fine-tuning submit을 진행하지 않는다.
- 현재 in-flight run(`ds_v10`) 이후에는 `extended120` 게이트를 넘기기 전까지 새 fine-tuning 실험을 기본적으로 중지한다.
- 자세한 분포 목표와 tranche 계획은 `docs/eval_scaleup_plan.md`를 기준으로 관리한다.

---

## 5. 개발 단계 개요

현재 온실은 공사 중이므로 실제 센서 수집과 장치 제어 구현보다 **AI 모델 준비, 데이터 스키마, RAG 지식베이스, 평가셋, MLOps 루프 구축**을 먼저 진행한다.

## 5.0 개정 개발 순서

1. AI 준비 구축
2. 센서 수집 계획 보강
3. 센서 수집 구현
4. 통합 제어 시스템 개발 계획
5. 통합 제어 시스템 구현
6. 사용자 UI 대시보드 개발
7. AI 모델과 통합 제어 시스템 연결

## Phase -1. AI 준비 구축 및 MLOps 기반 설계
목표:
- 실측 데이터가 없는 상태에서 AI 판단 체계를 먼저 준비
- 적고추 재배 전주기 전문가 지식과 센서 판단 체계를 구조화
- RAG 지식베이스, 파인튜닝 데이터셋, 평가셋, 모델 버전 관리 체계 구축
- 센서 데이터가 들어오면 학습과 평가에 반영되는 MLOps 루프 설계

성과물:
- AI_MLOPS_PLAN.md
- EXPERT_AI_AGENT_PLAN.md
- docs/site_scope_baseline.md
- docs/expert_knowledge_map.md
- docs/sensor_judgement_matrix.md
- schemas/rag_chunk_schema.json
- data/rag/pepper_expert_seed_chunks.jsonl
- docs/offline_agent_runner_spec.md
- evals/expert_judgement_eval_set.jsonl
- evals/rag_retrieval_eval_set.jsonl
- docs/mlops_registry_design.md
- docs/shadow_mode_report_format.md

## Phase 0. 요구사항 정리 및 범위 확정
목표:
- 자동화 목표를 명확히 정의
- 대상 온실/구역/장치/센서 목록 확정
- 안전 요구사항과 운영 정책 정리
- 센서 수집 계획과 AI 학습 반영 계획 확정

성과물:
- 요구사항 문서
- 대상 온실/품종/낮밤 운영 baseline
- 장치 목록
- 센서 목록
- 센서 수집 항목/주기/품질 플래그 정의
- 운영 시나리오 목록
- 위험 분석 초안

## Phase 1. 데이터 및 도메인 기반 구축
목표:
- 고추 재배 지식 데이터 정비
- 파인튜닝용 데이터셋 구조 개선
- state/action schema 정의

성과물:
- 도메인 지식셋
- 파인튜닝 학습셋
- JSON schema
- 평가셋
- `core24 + extended120/160` benchmark 운영 기준

## Phase 2. 센서/장치 데이터 파이프라인 구축
목표:
- 현장 데이터 수집 기반 확보
- 센서 시계열 저장
- 장치 상태 수집
- AI 학습/평가용 데이터로 변환 가능한 수집 구조 구현

성과물:
- sensor-ingestor
- MQTT topic 설계
- 시계열 DB 적재
- 상태 캐시
- data quality validator
- feature pipeline

## Phase 3. 상태 추정 및 정책 엔진 구축
목표:
- 원시 센서를 의미 있는 상태로 변환
- 절대 금지/허용 정책을 엔진화

성과물:
- state-estimator
- policy-engine
- 제약 조건 계산 로직

## Phase 4. LLM 의사결정 엔진 구축
목표:
- LLM 입력/출력 구조화
- function calling 연동
- 행동 추천 생성

성과물:
- llm-orchestrator
- structured output
- tool registry
- decision logging

## Phase 5. 실행 게이트와 PLC 연동
목표:
- LLM 추천을 검증 후 실행
- PLC/장치 제어 연결
- 자동/승인 모드 구분

성과물:
- execution-gateway
- plc-adapter
- command audit

## Phase 6. 비전 및 로봇 태스크 연동
목표:
- 수확 대상 탐지
- 작업 후보 생성
- 고수준 로봇 작업 지시

성과물:
- vision-inference
- robot candidate schema
- robot-task-manager

## Phase 7. 시뮬레이터/디지털 트윈 검증
목표:
- 실환경 투입 전 안전 검증
- 장애/예외/스트레스 시나리오 점검

성과물:
- simulator
- replay evaluator
- scenario test set

## Phase 8. 단계적 현장 적용
목표:
- 저위험 자동화부터 운영 시작
- 점진적 확장

성과물:
- 자동 실행 범위 정의
- 운영자 통합 제어 웹 UI (`ops-api/_dashboard_html`): 한국어 기본, 사이드바 네비게이션, 대시보드/존 모니터링/결정-승인/알림/로봇/장치-제약/정책-이벤트/Shadow Mode/시스템 9개 뷰. 5초 주기 폴링으로 `/dashboard/data` 재렌더링. 운영자가 승인/거절/수동 Execute/문제 사례 태깅/정책 토글/모드 전환을 한 화면에서 수행.
- 알람 체계
- KPI 체계

## Phase 9. 재학습 및 운영 고도화
목표:
- 실제 운영 로그 기반 고도화
- 모델/정책 지속 개선

성과물:
- retraining pipeline
- evaluation dashboard
- 정책 버전 관리 체계

---

## 6. 상세 기술 구성

## 6.1 데이터 계층
- PostgreSQL: 정책/명령/결정/작업 이력
- TimescaleDB/InfluxDB: 센서 시계열
- Redis: 최신 zone state 캐시
- Object Storage: 이미지, 캡처, 추론 결과
- Vector Store/Vector DB: 재배 매뉴얼, 현장 SOP, 품종별 기준, 정책 문서 임베딩 인덱스

## 6.2 서비스 계층
- sensor-ingestor
- state-estimator
- policy-engine
- rag-retriever
- llm-orchestrator
- execution-gateway
- plc-adapter
- vision-inference
- robot-task-manager
- audit-monitor

## 6.3 AI 계층
- RAG + 파인튜닝 하이브리드 농업용 LLM
- 임베딩 기반 검색 모델
- 시계열 예측/이상 탐지 모델
- 비전 모델
- 로봇 작업 우선순위 판단 모델(LLM 포함)

---

## 7. 데이터 설계 원칙

## 7.1 센서 데이터
저장해야 할 최소 항목:
- zone_id
- sensor_id
- sensor_type
- timestamp
- value
- quality_flag

## 7.2 상태 스냅샷
저장해야 할 최소 항목:
- 공기온도
- 습도
- CO2
- 광량
- 배지 함수율
- EC
- pH
- VPD
- 최근 추세
- stress_score
- device_status
- constraints

## 7.3 LLM 결정 로그
저장해야 할 최소 항목:
- decision_id
- 입력 상태 JSON
- 모델명
- 프롬프트 버전
- 출력 JSON
- confidence
- approval_required
- final_status

## 7.4 장치 명령 로그
저장해야 할 최소 항목:
- command_id
- source_decision_id
- device_id
- command_type
- requested_value
- validated_value
- execution_result

## 7.5 RAG 지식 문서
저장해야 할 최소 메타데이터:
- document_id
- source_type
- crop_type
- growth_stage
- region
- greenhouse_type
- version
- effective_date
- source_url 또는 file_path
- chunk_id
- embedding_model
- retrieval_score

---

## 8. LLM 개발 원칙

## 8.1 RAG + 파인튜닝 하이브리드 타당성
하이브리드 구조는 본 프로젝트에 적합하다. 적고추/건고추 온실 운영은 재배 매뉴얼, 현장 SOP, 품종별 기준, 계절별 환경 목표처럼 자주 바뀌거나 출처 추적이 필요한 지식과, JSON 행동 추천·금지행동 준수·승인 요청 같은 반복 운영 패턴이 함께 필요하기 때문이다.

- RAG 적용 대상: 재배 매뉴얼, 병해 조건, 생육 단계별 목표, 건조/수확 기준, 현장 SOP, 정책 문서, 장치 운전 기준
- 파인튜닝 적용 대상: 상태 해석 형식, action_type 선택, structured output, 안전한 거절, follow_up, confidence 표현
- 결론: 지식 자체를 파라미터에 모두 넣지 않고, 업데이트 가능한 지식은 RAG에 두며, 모델은 운영 방식과 출력 안정성을 학습한다.
- 제한: RAG 검색 실패, 오래된 문서 검색, 출처 충돌, 파인튜닝 데이터 편향은 별도 평가셋과 감사 로그로 관리한다.
- 적용 방식: `state + constraints + retrieved_context + device_status`를 LLM 입력으로 결합하고, 출력은 policy-engine과 execution-gateway에서 재검증한다.

## 8.2 파인튜닝 방향
기존 Q&A 데이터만으로는 부족하므로 아래 유형을 반드시 포함한다.

- 상태 해석
- 행동 추천
- 금지 행동
- 실패 대응
- 로봇 작업 우선순위
- 후속 점검 계획

운영형 모델의 역할 분리, 허용 `action_type`, `confidence`, `follow_up`, `retrieval_coverage` 요구는 `docs/fine_tuning_objectives.md`를 기준으로 고정한다.
base model과 실험명 규칙은 `docs/fine_tuning_runbook.md`를 기준으로 고정한다.

## 8.3 프롬프트 설계
시스템 프롬프트는 반드시 아래를 포함한다.

- 역할 제한
- 안전 우선 원칙
- RAG 검색 문맥 우선 사용 규칙
- 검색 근거가 부족할 때 불확실성 표시 규칙
- 허용 action_type 목록
- 불확실성 처리 규칙
- JSON 출력 강제
- follow_up 필수

## 8.4 구조화 출력
출력은 자연어가 아니라 다음 구조를 따른다.

- situation_summary
- risk_level
- recommended_actions[]
- robot_tasks[]
- follow_up[]
- confidence
- requires_human_approval
- citations[]
- retrieval_coverage

## 8.5 RAG 검색 설계
RAG는 단순 Q&A 검색이 아니라 운영 판단 근거를 제공하는 계층으로 설계한다.

- 검색 엔진 진화: 초기 Keyword 검색 → Embedding 기반 Semantic Search + Metadata Hard Filter 하이브리드 구조
- 지식 밀도 목표: 도메인별(육묘, 환경, 근권, 병해, 수확/건조) 최소 50~100개 이상의 정밀 청크 확보 (총 200+ 목표)
- 문서 단위: 재배 매뉴얼, 농가 SOP, 정책 문서, 장치 매뉴얼, 병해 자료
- chunk 메타데이터: crop_type, growth_stage, region, season, greenhouse_type, source_version, agent_use
- 검색 전략: 
    1. 상황 필터링 (Metadata Hard Filter: growth_stage, sensor_tags 등)
    2. 의미적 유사도 검색 (Semantic Search via Embedding)
    3. 키워드 보정 (Keyword Fallback for specific terms)
- 검색 결과 검증: 최소 score threshold, 최신 문서 우선, 충돌 문서 탐지
- 출력 요구: 중요한 추천에는 근거 문서 id와 chunk id를 함께 남긴다.

---

## 9. 제어/안전 설계 원칙

## 9.1 위험도 기반 실행
### 자동 실행
- 저위험, 짧은 관수
- 순환팬 단계 조정
- 차광 소폭 조정
- 알람 생성

### 승인 후 실행
- 난방 setpoint 큰 변경
- 양액 농도 큰 변경
- 새 로봇 구역 작업 시작

### 차단
- 안전 정책 위반
- 센서 품질 불량 상태에서 위험 명령
- 작업자 존재 중 로봇 작업
- 인터록 해제 요구

## 9.2 Fail-safe
- 장치 무응답 시 safe mode
- 센서 이상 다발 시 자동제어 축소
- 네트워크 단절 시 현장 제어 독립 지속
- 로봇 이상 시 즉시 정지 및 큐 중단

---

## 10. 로봇 연동 원칙

## 10.1 비전 역할
- 열매 인식
- 숙도 판정
- 병징 의심 탐지
- 가려짐 판정
- 접근 가능성 산정

## 10.2 LLM 역할
- 작업 우선순위 결정
- 제외 대상 지정
- 작업 시간/목표량 기준 정책 반영

## 10.3 로봇 제어기 역할
- grasp pose 생성
- 경로 계획
- 충돌 회피
- 힘/토크 제어
- 재시도 및 실패 복구

---

## 11. 운영 단계별 적용 전략

## 11.1 1단계
- 센서 데이터 수집
- 대시보드
- 수동 운영 + LLM 조언

## 11.2 2단계
- 행동 추천 JSON
- 사람 승인 후 실행

## 11.3 3단계
- 저위험 장치 자동 실행

## 11.4 4단계
- 비전 기반 수확 후보 탐지
- 로봇 작업 제안

## 11.5 5단계
- 반자동 로봇 수확

## 11.6 6단계
- 제한된 구역 완전자동 운영

---

## 12. KPI 및 평가 항목

### 재배 성능
- 생육 안정성
- 수확량
- 상품과율
- 병해 발생률
- 과실 균일성

### 제어 성능
- 목표 환경 유지율
- 과도응답 빈도
- 장치 명령 성공률
- safe mode 전환 빈도

### AI 성능
- 상태 판단 정확도
- 행동 추천 적합도
- 불필요 명령률
- 승인 요청 적정성
- 오경보/미경보율

### 로봇 성능
- 탐지 정확도
- 수확 성공률
- 손상률
- 작업 시간
- 재시도율

---

## 13. 권장 초기 MVP 범위

초기 MVP는 다음으로 제한한다.

- 단일 온실 또는 단일 구역
- 센서: 온도/습도/CO2/광량/배지 함수율/EC/pH
- 장치: 순환팬/차광/관수
- 기능: RAG 기반 근거 검색, 상태 요약, 행동 추천, 저위험 자동 실행
- LLM: structured output 안정화를 위한 소규모 파인튜닝 + 재배/SOP 문서 RAG
- 로봇: 실제 제어 전 단계인 작업 후보 제안까지만

---

## 14. 예상 리스크

- 센서 품질 불안정
- 현장 장치 프로토콜 호환 문제
- 파인튜닝 데이터의 운영 적합성 부족
- LLM 출력의 일관성 부족
- 규칙 엔진 미정의 영역에서 예외 발생
- 로봇 비전 오검출
- 네트워크 장애
- 사람 개입 시 충돌 시나리오

대응:
- 품질 플래그 도입
- 시뮬레이터 우선 검증
- 승인 모드 기본값 유지
- 로그 기반 재학습

---

## 15. 최종 결론

이 프로젝트는 단순한 “고추 재배 챗봇”이 아니라, **현장 데이터·정책·제어·로봇 작업을 통합하는 운영형 AI 시스템**이다.

성공하려면 다음 순서를 지켜야 한다.

1. AI 준비 구축
2. RAG 지식베이스 설계 및 문서 인덱싱
3. 파인튜닝 데이터셋과 평가셋 구축
4. 센서 수집 계획 보강
5. state/action schema 확정
6. 센서 수집 구현
7. 센서 데이터 품질 검증 및 특징량 생성
8. 통합 제어 시스템 개발 계획
9. 정책 엔진과 실행 게이트 설계
10. 통합 제어 시스템 구현
11. 사용자 UI 대시보드 개발
12. AI 모델과 통합 제어 시스템 연결
13. Shadow Mode 검증
14. Limited Auto Mode 전환
15. 운영 로그 기반 모델/정책 고도화

# Reference
- [세부 개발목록](todo.md)
- [AI 모델 준비 및 MLOps 계획](AI_MLOPS_PLAN.md)
- OpenAI Retrieval guide: https://platform.openai.com/docs/guides/retrieval
- OpenAI File search guide: https://platform.openai.com/docs/guides/tools-file-search/
- OpenAI Fine-tuning guide: https://platform.openai.com/docs/guides/fine-tuning
- OpenAI Evals API: https://platform.openai.com/docs/api-reference/evals
- MLflow Model Registry: https://mlflow.org/docs/latest/ml/model-registry/
- Kubeflow Pipelines: https://www.kubeflow.org/docs/components/pipelines/overview/
- Lewis et al., Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks: https://arxiv.org/abs/2005.11401

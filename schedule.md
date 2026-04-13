# schedule.md

# 8주 일정 계획 (주차별 실행 로드맵)

이 문서는 `todo.md`의 세부 작업을 실제 일정 단위로 실행하기 위한 주차별 계획서이다.

## 관련 문서
- [저장소 README](README.md)
- [프로젝트 현황 요약](PROJECT_STATUS.md)
- [AI 모델 준비 및 MLOps 계획](AI_MLOPS_PLAN.md)
- [적고추 전문가 AI Agent 구축 계획](EXPERT_AI_AGENT_PLAN.md)
- [현장 baseline](docs/site_scope_baseline.md)
- [계절별 운영 범위](docs/seasonal_operation_ranges.md)
- [센서 모델 shortlist](docs/sensor_model_shortlist.md)
- [장치 setpoint 범위](docs/device_setpoint_ranges.md)
- [전체 개발 계획 보기](PLAN.md)
- [세부 Todo 보기](todo.md)
- [작업 로그 보기](WORK_LOG.md)
- [평가셋 확장 계획 보기](docs/eval_scaleup_plan.md)

---

## 개정 실행 순서

온실이 아직 공사 중이므로 실제 제어 구현보다 AI와 데이터 기반을 먼저 준비한다.

1. AI 준비 구축
2. 센서 수집 계획 보강
3. 센서 수집 구현
4. 통합 제어 시스템 개발 계획
5. 통합 제어 시스템 구현
6. 사용자 UI 대시보드 개발
7. AI 모델과 통합 제어 시스템 연결

---

## 즉시 조정 사항 (2026-04-13)

- 현재 fine-tuning `core24`는 challenger 비교용 append-only 회귀셋으로 유지한다.
- `extended200`과 blind holdout `50` frozen coverage는 이미 확보했다. 현재 분포는 `expert 60 / action 28 / forbidden 20 / failure 24 / robot 16 / edge 28 / seasonal 24`, blind holdout은 `50건`이다.
- 현재 frozen baseline은 `ds_v11`이고 최신 corrective candidate `ds_v14`는 `ds_v11`보다 낮아 승격 실패로 닫았다.
- 현재 in-flight fine-tuning run은 없다. `docs/model_product_readiness_reassessment.md` 기준 submit freeze를 유지한다.
- 즉시 우선순위는 `real shadow window` 누적, blind50 validator 잔여 `5건` 축소, extended200 validator 잔여 `42건` 우선순위 batch 설계, synthetic shadow `day0` residual `4건` 해소다.
- 운영/API 쪽 즉시 우선순위는 real PostgreSQL smoke, `TimescaleDB + Grafana` 기반 real sensor chart/zone history의 통합관제 웹 반영, policy source versioning/UI 반영이다.

---

## Week 1 — AI 준비 구축 + 데이터 구조 확정

### 목표
- 온실 실측 데이터 없이도 AI 판단 체계 준비
- state/action schema 완성
- RAG 지식베이스 범위 확정
- 파인튜닝 방향 재정의
- eval/MLOps 기본 구조 정의
- 대상 온실, 품종, 낮/밤 운영 기준 baseline 확정

### 주요 작업
- 전문가 지식 지도 작성
- 센서 판단 매트릭스 작성
- state schema v1 작성
- feature schema v1 작성
- action schema v1 작성
- action_type enum 확정
- RAG 문서 범위와 메타데이터 정의
- 적고추/건고추 재배 매뉴얼, 현장 SOP, 장치 운전 기준 수집 목록 작성
- offline decision runner 설계
- eval set 기준 정의
- `core24 + extended120 + extended160 + extended200 + blind_holdout50 + raw/validator gate` 운영 기준 정의
- model/prompt/dataset version 규칙 정의
- 기존 Q&A → 상태/행동 구조로 재분류
- 행동추천 JSON 샘플 100개 생성
- 금지행동 샘플 100개 생성
- hard block 정책 10개 작성
- approval 정책 10개 작성
- 서비스 구조, API 구조, 이벤트 이름 초안 작성
- `gh-01` site baseline, 품종 shortlist, 낮/밤 기준 문서화

### 완료 기준
- expert knowledge map 초안 완료
- 대상 현장 baseline 완료 (`300평 연동형 비닐온실 1동`, `gh-01`)
- 품종 shortlist 완료 (`왕조`, `칼탄열풍`, `조생강탄`)
- 낮/밤 운영 기준 완료 (낮 `25~28℃`, 밤 `18℃ 전후`)
- sensor judgement matrix 초안 완료
- state schema JSON 문서 완료
- feature schema JSON 문서 완료
- action schema JSON 문서 완료
- action_type 목록 확정
- RAG 문서 메타데이터 초안 완료
- 학습 샘플 200개 이상 확보
- 정책 JSON 20개 이상 작성
- AI_MLOPS_PLAN.md 기준 반영
- eval scale-up 기준 문서 완료

---

## Week 2 — RAG/파인튜닝 PoC + 센서 수집 계획 보강

### 목표
- LLM이 JSON으로 안정적으로 행동 추천 가능하도록 만들기
- RAG vector store PoC로 재배 지식 검색 가능성 확인
- 수집 센서 종류, 수집 주기, 품질 기준 확정
- 핵심 센서 1차 상용 모델 shortlist 확정
- 계절별 운영 범위와 계절 slice 기준 정리

### 주요 작업
- train/val JSONL 생성
- expert judgement eval set 초안 작성
- eval `core24 + extended120 + extended160 + extended200 + blind_holdout50 + raw/validator gate` 운영 기준 반영
- state judgement 샘플 작성
- forbidden action 샘플 작성
- RAG chunking 전략 정의
- vector store 또는 vector DB PoC 구축
- 검색 품질 평가셋 작성
- retrieval score와 citation 저장 형식 정의
- 환경/배지/외기/장치/비전/운영 이벤트 센서 목록 확정
- 확정된 `Grodan Delta 6.5` / `Grodan GT Master` 배지 조건을 수집·판단 기준에 반영
- sensor_id, device_id, zone_id naming 규칙 확정
- 수집 주기와 quality_flag 규칙 정의
- 포맷 검증 스크립트 작성
- SFT 1차 실행
- 결과 로그 분석
- JSON 파싱 실패 케이스 수집
- malformed output 보정 로직 작성
- 상태판단 정확도 테스트
- 행동추천 적합도 테스트
- 금지행동 위반 테스트
- 계절별 운영 범위 정의

### 완료 기준
- JSON 출력 성공률 95% 이상
- action_type 오류율 5% 이하
- 주요 재배 질의에 대한 검색 hit rate 기준 통과
- 센서 수집 계획 문서 완료
- 핵심 센서 shortlist 문서 완료
- 계절별 운영 범위 문서 완료
- 기본 케이스 행동추천 가능
- eval 총량 `120` 달성

---

## Week 3 — 센서 수집 구현

### 목표
- 공사 완료 후 바로 연결 가능한 센서 수집 소프트웨어 기반 구축
- `TimescaleDB`를 canonical 시계열 저장소로 연결할 준비 완료

### 주요 작업
- 센서 adapter 구현
- MQTT publish 구현
- `TimescaleDB` raw/snapshot 저장 구현
- PostgreSQL 기본 테이블 생성
- 센서 → `TimescaleDB` 저장 확인
- 센서 → MQTT → 소비 확인
- 이상값 필터 구현
- stale sensor 감지 구현
- AI 학습용 raw/feature 데이터 분리 저장

### 완료 기준
- 센서 데이터 실시간 저장
- 1분 단위 데이터 안정 수집
- quality_flag 정상 동작
- MLOps feature pipeline 입력 형식 확정

---

## Week 4 — 통합 제어 시스템 개발 계획

### 목표
- 제어 시스템 구현 전 안전 아키텍처와 인터페이스 확정

### 주요 작업
- VPD 계산
- trend 계산
- stress score 계산
- zone state 생성
- 통합 제어 시스템 컴포넌트 경계 정의
- PLC/장치 adapter 인터페이스 정의
- policy evaluator 구현
- hard block 동작 구현
- approval 판단 동작 구현
- state updated 이벤트 생성
- constraint 생성 로직 구현

### 완료 기준
- zone state JSON 완성
- 정책 위반 시 action block 동작
- constraints 정상 생성
- 통합 제어 시스템 설계 문서 완료

---

## Week 5 — 통합 제어 시스템 구현

### 목표
- 센서 상태, 정책, 실행 게이트, 장치 adapter의 기본 흐름 구현

### 주요 작업
- state + constraints + device 상태 결합
- decision logging 구현
- execution-gateway 기본 구현
- schema/range validation 구현
- duplicate/cooldown 구현
- plc-adapter mock 구현
- readback 검증 흐름 구현

### 완료 기준
- decision log 저장
- 잘못된 명령 차단
- mock PLC 기준 제어 흐름 성공

---

## Week 6 — 사용자 UI 대시보드 개발

### 목표
- 운영자가 상태, 추천, 승인, 알람, 로그를 확인할 수 있게 만들기
- 시계열 장기 조회는 `Grafana`를 통합관제 웹에 붙여 제공하기

### 주요 작업
- zone overview 화면
- `Grafana` 기반 실시간/장기 센서 차트
- decision log 화면
- action 승인/거절 화면
- alert 화면
- policy 조회 화면
- 수동 override 기록 화면
- 통합관제 웹과 `Grafana` embed 연동

### 완료 기준
- 운영 대시보드 MVP 동작
- `Grafana` 시계열 패널이 통합관제 웹에서 열림
- 승인/거절 기록 저장
- 주요 로그 조회 가능

---

## Week 7 — AI 모델과 통합 제어 시스템 연결

### 목표
- AI 판단을 통합 제어 시스템에 연결하되 실제 자동제어는 shadow mode부터 시작

### 주요 작업
- OpenAI API 연결
- prompt renderer 구현
- rag-retriever client 구현
- retrieved_context + citations 입력 조합
- structured output parser 구현
- fallback 처리 구현
- Shadow Mode 운영
- 사람 판단과 비교
- Approval Mode 운영
- 오판 사례 수집
- 승인 패턴 분석

### 완료 기준
- 실제 또는 mock 센서 기반 판단 가능
- RAG 근거가 decision log에 citation으로 저장
- JSON 안정 출력 유지
- 위험 행동 없음
- 승인/자동 흐름 정상 동작

---

## Week 8 — Limited Auto Mode 준비 + 비전/로봇 계획

### 목표
- 저위험 자동화 전환 기준과 비전/로봇 후속 계획 정리

### 주요 작업
- 팬 자동 후보 검증
- 차광 자동 후보 검증
- 짧은 관수 자동 후보 검증
- 수확 대상 탐지 데이터 수집 계획
- 숙도 score 기준 정의
- robot-task-manager 인터페이스 초안
- 후보 정렬 기준 정의
- 작업 큐 schema 초안
- LLM 우선순위 판단 프롬프트 초안
- 반자동 수확 흐름 설계

### 완료 기준
- limited auto 전환 조건 정의
- 비전/로봇 데이터 수집 계획 완료
- 로봇 태스크 schema 초안 완료
- 반자동 수확 후속 구현 범위 정의

---

## 최종 체크포인트

- Week 2: JSON 출력 안정화 전에는 다음 단계 진행 금지
- Week 2: RAG 검색 품질 기준 없이 하이브리드 판단 운영 금지
- Week 2: frozen gate 재확인과 real shadow mode 전에는 새 fine-tuning submit 기본 중지
- Week 3: 센서 품질 플래그 없이 학습 데이터 반영 금지
- Week 4: 정책 엔진 없이 자동화 금지
- Week 5: execution-gateway 없이 PLC 연결 금지
- Week 7: AI 연결은 shadow mode부터 시작
- Week 8: shadow → approval → auto 순서 준수

---

## 일정 운영 원칙

- 처음부터 완전자동 목표로 가지 않기
- 반드시 승인 단계를 거치기
- RAG 문서는 출처, 버전, 적용 기간을 기록하기
- 파인튜닝에는 자주 바뀌는 재배 기준을 직접 암기시키지 않기
- 최소 1~2주 shadow mode 운영
- 로그 기반으로 파인튜닝 지속 반복

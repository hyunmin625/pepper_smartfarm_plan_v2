# schedule.md

# 8주 일정 계획 (주차별 실행 로드맵)

이 문서는 `todo.md`의 세부 작업을 실제 일정 단위로 실행하기 위한 주차별 계획서이다.

---

## Week 1 — 기초 설계 + 데이터 구조 확정

### 목표
- 시스템 뼈대 확정
- state/action schema 완성
- RAG 지식베이스 범위 확정
- 파인튜닝 방향 재정의

### 주요 작업
- state schema v1 작성
- action schema v1 작성
- action_type enum 확정
- zone/device/sensor naming 규칙 확정
- RAG 문서 범위와 메타데이터 정의
- 적고추/건고추 재배 매뉴얼, 현장 SOP, 장치 운전 기준 수집 목록 작성
- 기존 Q&A → 상태/행동 구조로 재분류
- 행동추천 JSON 샘플 100개 생성
- 금지행동 샘플 100개 생성
- hard block 정책 10개 작성
- approval 정책 10개 작성
- 서비스 구조, API 구조, 이벤트 이름 초안 작성

### 완료 기준
- state schema JSON 문서 완료
- action schema JSON 문서 완료
- action_type 목록 확정
- RAG 문서 메타데이터 초안 완료
- 학습 샘플 200개 이상 확보
- 정책 JSON 20개 이상 작성

---

## Week 2 — 파인튜닝 + LLM 구조화 출력 완성

### 목표
- LLM이 JSON으로 안정적으로 행동 추천 가능하도록 만들기
- RAG vector store PoC로 재배 지식 검색 가능성 확인

### 주요 작업
- train/val JSONL 생성
- RAG chunking 전략 정의
- vector store 또는 vector DB PoC 구축
- 검색 품질 평가셋 작성
- retrieval score와 citation 저장 형식 정의
- 포맷 검증 스크립트 작성
- SFT 1차 실행
- 결과 로그 분석
- JSON 파싱 실패 케이스 수집
- malformed output 보정 로직 작성
- 상태판단 정확도 테스트
- 행동추천 적합도 테스트
- 금지행동 위반 테스트

### 완료 기준
- JSON 출력 성공률 95% 이상
- action_type 오류율 5% 이하
- 주요 재배 질의에 대한 검색 hit rate 기준 통과
- 기본 케이스 행동추천 가능

---

## Week 3 — 센서 파이프라인 구축

### 목표
- 실제 데이터 흐름 시작

### 주요 작업
- 센서 adapter 구현
- MQTT publish 구현
- 시계열 DB 저장 구현
- PostgreSQL 기본 테이블 생성
- 센서 → DB 저장 확인
- 센서 → MQTT → 소비 확인
- 이상값 필터 구현
- stale sensor 감지 구현

### 완료 기준
- 센서 데이터 실시간 저장
- 1분 단위 데이터 안정 수집
- quality_flag 정상 동작

---

## Week 4 — 상태 추정 + 정책 엔진

### 목표
- LLM 입력용 상태 생성
- 안전 규칙 시스템 구축

### 주요 작업
- VPD 계산
- trend 계산
- stress score 계산
- zone state 생성
- policy evaluator 구현
- hard block 동작 구현
- approval 판단 동작 구현
- state updated 이벤트 생성
- constraint 생성 로직 구현

### 완료 기준
- zone state JSON 완성
- 정책 위반 시 action block 동작
- constraints 정상 생성

---

## Week 5 — LLM + 실시간 데이터 연결

### 목표
- LLM이 실제 센서 상태를 보고 판단하도록 만들기
- RAG 검색 근거를 LLM 판단 입력에 결합하기

### 주요 작업
- OpenAI API 연결
- prompt renderer 구현
- tool 구조 정의
- rag-retriever client 구현
- retrieved_context + citations 입력 조합
- state + constraints + device 상태 결합
- structured output parser 구현
- fallback 처리 구현
- decision logging 구현

### 완료 기준
- 실제 센서 기반 판단 가능
- RAG 근거가 decision log에 citation으로 저장
- decision log 저장
- JSON 안정 출력 유지

---

## Week 6 — 실행 게이트 + PLC 연결

### 목표
- 안전하게 장치 제어 시작

### 주요 작업
- schema validation
- range validation
- duplicate 방지
- cooldown 적용
- plc-adapter 구현
- 장치 write 구현
- readback 검증
- auto / approval 분리
- 승인 요청 흐름 구현

### 완료 기준
- 저위험 액션 자동 실행 가능
- 잘못된 명령 차단
- PLC 제어 성공

---

## Week 7 — Shadow Mode → Limited Auto Mode

### 목표
- 실제 운영 시작

### 주요 작업
- Shadow Mode 운영
- 사람 판단과 비교
- Approval Mode 운영
- 팬 자동
- 차광 자동
- 짧은 관수 자동
- 오판 사례 수집
- 승인 패턴 분석

### 완료 기준
- 운영 안정성 확보
- 위험 행동 없음
- 승인/자동 흐름 정상 동작

---

## Week 8 — 비전 + 로봇 연동

### 목표
- 로봇 작업 판단 연결

### 주요 작업
- 수확 대상 탐지
- 숙도 score 생성
- robot-task-manager 구현
- 후보 정렬
- 작업 큐 생성
- LLM 우선순위 판단 연결
- 반자동 수확 흐름 테스트

### 완료 기준
- 수확 후보 생성
- LLM이 작업 우선순위 결정
- 로봇 태스크 생성 성공

---

## 최종 체크포인트

- Week 2: JSON 출력 안정화 전에는 다음 단계 진행 금지
- Week 2: RAG 검색 품질 기준 없이 하이브리드 판단 운영 금지
- Week 4: 정책 엔진 없이 자동화 금지
- Week 6: execution-gateway 없이 PLC 연결 금지
- Week 7: shadow → approval → auto 순서 준수

---

## 일정 운영 원칙

- 처음부터 완전자동 목표로 가지 않기
- 반드시 승인 단계를 거치기
- RAG 문서는 출처, 버전, 적용 기간을 기록하기
- 파인튜닝에는 자주 바뀌는 재배 기준을 직접 암기시키지 않기
- 최소 1~2주 shadow mode 운영
- 로그 기반으로 파인튜닝 지속 반복

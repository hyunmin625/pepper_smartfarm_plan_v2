# 적고추 스마트팜 운영 전문가 AI Agent 구축 계획

이 문서는 적고추(건고추) 온실 재배 전주기에 대해 전문가 수준 지식을 갖고, 센서 데이터로 정확한 판단을 내리는 LLM 기반 AI Agent 구축 단계를 정리한다.

## 목표

- 적고추 재배 전주기 지식과 온실 운영 데이터를 결합한다.
- 센서 데이터로 생육 상태, 환경 위험, 관수/양액 문제, 병해 위험, 수확/건조 적기를 판단한다.
- AI 판단은 추천과 설명을 담당하고, 실제 제어는 policy-engine과 execution-gateway가 검증한다.
- 운영 로그를 학습 데이터와 RAG 문서로 환류해 시간이 지날수록 더 정확해지는 구조를 만든다.

## 전주기 지식 범위

AI Agent는 최소한 아래 생육/운영 단계를 구분해야 한다.

1. 공사/입식 전 준비: 온실 구조, 센서 배치, 관수/양액/환기/차광 장치 점검
2. 육묘: 발아, 묘 생육, 온도 순화, 병해충 예방
3. 정식: 정식 간격, 초기 활착, 뿌리 상태, 배지/토양 수분 안정화
4. 영양생장: 온습도, 광, CO2, VPD, 관수 리듬, 초세 판단
5. 개화/착과: 고온·저온 스트레스, 습도, 꽃가루 활력, 착과 불량 위험
6. 과실 비대/착색: 수분 스트레스, EC/pH, 칼슘/마그네슘 흡수, 일사/차광 관리
7. 수확 적기: 착색, 과실 크기, 병징, 수확 우선순위
8. 건조/저장: 건조 함수율, 곰팡이 위험, 저장 온습도, 재흡습 방지
9. 작기 종료/다음 작기: 병해 잔재 제거, 배지/토양 소독, 데이터 리뷰

## 센서 기반 판단 체계

AI Agent 입력은 원시 센서가 아니라 품질 검증과 특징량 생성을 거친 상태 JSON이어야 한다.

- 환경: 온도, 상대습도, CO2, PAR/광량, 일사량, VPD, DLI
- 근권/양액: 배지 함수율, 배지 온도, 급액 EC/pH, 배액 EC/pH, 배액률, 급액량
- 외기: 외기 온도, 습도, 풍속, 강우, 외부 일사
- 장치: 환기창, 팬, 차광, 관수 밸브, 양액기, 난방기, CO2 공급기, 제습기 상태
- 비전: 잎색, 생장점, 과실 크기, 착색, 병징, 기형과, 수확 후보
- 운영 이벤트: 관수, 차광, 환기, 수동 override, 방제, 작업자 출입, 알람

판단에는 단일 값보다 추세와 맥락을 우선한다. 예: 1분 평균, 5분 평균, 30분 변화율, 일출 후 누적광, 관수 후 함수율 회복률, 급액/배액 EC 차이.

## Agent 아키텍처

```text
sensor-ingestor
→ data-quality-validator
→ feature-builder
→ zone-state-builder
→ rag-retriever
→ expert-ai-agent
→ policy-engine
→ execution-gateway
→ dashboard / approval / audit log
```

### 주요 하위 Agent

- `growth-stage-agent`: 생육 단계와 초세 판단
- `climate-agent`: 온도, 습도, VPD, CO2, 광 관리 판단
- `irrigation-agent`: 관수량, 관수 주기, 배액률, 함수율 회복 판단
- `nutrient-agent`: EC/pH, 급액/배액 차이, 영양 흡수 이상 판단
- `pest-disease-agent`: 병해충 위험 조건과 비전 의심 증상 판단
- `harvest-drying-agent`: 수확 적기, 건조/저장 위험 판단
- `safety-agent`: 금지 행동, 승인 필요 행동, 센서 불량 시 보수적 판단
- `report-agent`: 운영자 보고서와 follow_up 생성

최종 응답은 하나의 `expert-ai-agent`가 통합하되, 각 하위 Agent 판단 근거와 confidence를 함께 남긴다.

## 지식 구축 단계

1. 공식 재배 자료 수집: 농촌진흥청/농사로 고추 재배, 시설재배, 양액재배, 병해충, 수확/건조 자료
2. 현장 사례 수집: 고온, 과습, EC/pH 이상, 생리장해, 착과불량, 곡과, 뿌리 갈변 사례
3. 지식 온톨로지 정의: 생육 단계, 센서 지표, 위험 조건, 원인 후보, 추천 조치, 금지 조치
4. RAG 문서화: 출처, 버전, 적용 작형, 재배방식, 생육단계, 지역, 계절 메타데이터 부여
5. 판단 룰 초안 작성: hard block, approval, warning, recommendation으로 구분
6. 전문가 검토: 농업 전문가 또는 현장 운영자가 기준값과 판단 근거를 검토

## 데이터셋 구축 단계

- `state_judgement`: 상태 요약과 위험도 판단
- `action_recommendation`: 추천 행동과 근거
- `forbidden_action`: 하면 안 되는 행동과 차단 이유
- `sensor_fault`: 센서 불량, stale, outlier 상황
- `rootzone_diagnosis`: 함수율, EC, pH, 배액률 기반 근권 판단
- `climate_risk`: 고온, 저온, 결로, 과습, 저습, CO2 부족
- `flower_fruit_risk`: 착과불량, 기형과, 낙화, 일소, 칼슘장해
- `harvest_drying`: 수확 우선순위, 건조/저장 함수율 위험
- `operator_feedback`: 승인, 거절, 수정 조치, 현장 메모

각 샘플은 `input_state`, `retrieved_context`, `expected_json`, `risk_level`, `citations`, `expert_label`을 포함한다.

## 평가 기준

- JSON schema 통과율
- `action_type` 오류율
- 금지 행동 차단율
- 센서 이상 시 보수적 응답률
- RAG 근거 반영률
- citation 정확도
- 전문가 판정 일치율
- 위험도 분류 정확도
- 불필요 명령률
- 승인 요청 적정성
- 운영자 수정률

운영 투입 전에는 offline eval, replay eval, shadow mode eval을 모두 통과해야 한다.

## 단계별 구축 순서

### Step 1. 전문가 지식 지도 작성
- 생육 전주기 단계 정의
- 단계별 목표 환경과 위험 조건 정리
- 센서 지표와 판단 질문 매핑
- 산출물: `docs/expert_knowledge_map.md`

### Step 2. 센서 판단 스키마 작성
- `state_schema.json`
- `feature_schema.json`
- `sensor_quality_schema.json`
- `decision_schema.json`

### Step 3. RAG 지식베이스 구축
- 공식 문서와 현장 SOP 인덱싱
- 생육 단계/센서/작형별 metadata filtering
- 근거 chunk citation 저장

### Step 4. 전문가 판단 평가셋 구축
- 정상/이상/센서불량/장치불량/수확/건조 케이스 작성
- 공식 자료와 현장 사례를 기준으로 expected output 작성

### Step 5. Agent 프롬프트와 도구 설계
- `get_zone_state`
- `search_cultivation_knowledge`
- `get_recent_trend`
- `get_active_constraints`
- `estimate_growth_stage`
- `request_human_approval`
- `log_decision`

### Step 6. 파인튜닝 데이터 구축
- 출력 형식, 판단 절차, 금지 행동, follow_up을 학습
- 자주 바뀌는 기준값은 파인튜닝하지 않고 RAG에 둔다.

### Step 7. Offline Agent Runner 구현
- 실제 온실 없이 JSON 상태를 넣고 판단 결과를 검증
- eval 결과를 model/prompt/dataset registry에 기록

### Step 8. Shadow Mode 연결
- 실제 또는 mock 센서 데이터로 추천만 생성
- 운영자 판단과 비교해 오판 사례를 축적

### Step 9. Approval Mode 연결
- 모든 조치를 승인 후 실행
- 승인/거절 사유를 학습 후보로 저장

### Step 10. Limited Auto Mode 전환
- 팬, 차광 소폭 조정, 짧은 관수 등 저위험 액션만 자동화
- 정책 엔진과 execution-gateway 통과가 필수다.

## 우선 착수 작업

1. `docs/expert_knowledge_map.md` 작성
2. `schemas/state_schema.json` 작성
3. `schemas/feature_schema.json` 작성
4. `docs/sensor_judgement_matrix.md` 작성
5. `docs/rag_source_inventory.md` 작성
6. `evals/expert_judgement_eval_set.jsonl` 초안 작성
7. `data/examples/state_judgement_samples.jsonl` 작성
8. `data/examples/forbidden_action_samples.jsonl` 작성
9. `docs/agent_tool_design.md` 작성
10. `docs/offline_agent_runner_spec.md` 작성

## 조사 근거

- 농사로 고추 육묘/재배 환경 자료: 발아·생육 온도, 광, 육묘 관리 기준을 제공한다. https://www.nongsaro.go.kr/portal/ps/psx/psxa/mlrdCurationDtl.mo?curationNo=188
- 농사로 고추 시설 이상증상 현장 기술지원: 하우스 고온, 배지 함수율, EC/pH, 환기 상태 등 실제 진단 항목을 제공한다. https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=262042&menuId=PS00077
- 농사로 고추 양액재배 현장 기술지원: 코이어 배지, 정식, 양액재배, 여름철 관리 등 현장 운영 항목을 제공한다. https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=259682&menuId=PS00077
- 농사로 고추 생육불량 현장 기술지원: 과습, EC, 저온, 뿌리 갈변 등 원인 진단과 대책 사례를 제공한다. https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=249249&menuId=PS00077
- OpenAI Retrieval guide: RAG 검색 기반 응답 구성을 위한 근거. https://platform.openai.com/docs/guides/retrieval
- OpenAI Evals API: 모델 출력 평가 체계 구축 근거. https://platform.openai.com/docs/api-reference/evals

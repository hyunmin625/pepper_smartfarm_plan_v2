# Sensor Judgement Matrix

이 문서는 적고추 전문가 AI Agent가 센서 데이터를 어떤 판단에 사용할지 정의하는 초안이다.

## 판단 원칙

- 단일 센서값만으로 제어 결정을 내리지 않는다.
- `quality_flag`가 불량이면 자동 실행이 아니라 보수적 판단과 확인 요청을 우선한다.
- `quality_flag`가 핵심 센서 `stale/missing/flatline/communication_loss`이면 state-estimator는 기본 `risk_level=unknown`으로 올린다.
- 생육 단계, 최근 추세, 장치 상태, 운영 이벤트, RAG 근거를 함께 본다.
- 최종 제어 명령은 policy-engine과 execution-gateway에서 재검증한다.

## 센서-판단 매트릭스

| 데이터 그룹 | 주요 센서/데이터 | 생성 특징량 | 판단 질문 | 담당 Agent | 주요 위험 |
|---|---|---|---|---|---|
| 온실 환경 | 온도, 습도 | VPD, 5분/30분 trend, 결로 위험 | 현재 온습도가 생육 단계에 적합한가? | climate-agent | 고온, 저온, 과습, 결로 |
| 광/일사 | PAR/광량, 일사량 | DLI, 일출 후 누적광, 급격한 일사 증가 | 차광 또는 광 관리가 필요한가? | climate-agent | 일소, 광부족, 고온 상승 |
| CO2 | CO2 농도, 환기 상태 | 주야간 평균, 환기 중 CO2 저하 | CO2 공급 또는 환기 전략이 적절한가? | climate-agent | CO2 부족, 과잉 공급 |
| 배지 수분 | 함수율, 배지 온도 | 관수 후 회복률, 건조 속도 | 관수가 부족하거나 과한가? | irrigation-agent | 과습, 과건조, 뿌리 스트레스 |
| 양액/배액 | 급액 EC/pH, 배액 EC/pH, 배액률 | 급배액 EC 차이, pH drift, 배액률 trend | 양분 흡수와 염류 집적이 정상인가? | nutrient-agent | 고EC, pH 이상, 흡수장해 |
| 외기 | 외기 온도, 습도, 풍속, 강우 | 환기 가능성, 냉방 효과 예상 | 환기/차광/냉방 전략을 바꿔야 하는가? | climate-agent | 환기 역효과, 강풍 위험 |
| 장치 상태 | 팬, 차광, 환기창, 관수 밸브, 난방기 | 명령 후 readback, 응답 지연 | 장치가 명령대로 동작했는가? | safety-agent | stuck, 무응답, 중복 명령 |
| 비전 | 잎색, 생장점, 착색, 병징, 과실 크기 | 숙도 score, 병징 score, 생육 이상 score | 병해/수확/생육 이상 후보가 있는가? | pest-disease-agent, harvest-drying-agent | 병해, 기형과, 수확 지연 |
| 운영 이벤트 | 수동 override, 알람, 방제, 작업자 출입 | 이벤트-센서 반응 지연, 조치 결과 | AI 추천과 실제 운영 결과가 일치했는가? | report-agent | 반복 오판, 안전 우회 |

## LLM 입력 상태 최소 필드

- `zone_id`
- `growth_stage`
- `timestamp`
- `current_state`
- `derived_features`
- `sensor_quality`
- `device_status`
- `recent_events`
- `active_constraints`
- `retrieved_context`

## 다음 작업

1. `schemas/state_schema.json` 작성
2. `schemas/feature_schema.json` 작성
3. 센서별 정상/주의/위험 기준값 조사
4. 생육 단계별 판단 질문 세분화
5. expert eval set에 정상/이상 사례 추가

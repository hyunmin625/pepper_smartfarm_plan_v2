# RAG Source Inventory

이 문서는 적고추 온실 스마트팜 전문가 AI Agent의 RAG 지식베이스에 넣을 출처를 관리한다.

## 조사 회차 요약

| 회차 | 조사 주제 | 핵심 목적 | RAG 반영 위치 |
|---|---|---|---|
| 1 | 육묘/정식/초기 생육 | 전주기 시작 단계와 생육 단계 분류 | `growth_stage`, `nursery`, `transplanting` |
| 2 | 온실 환경/고온/환기/차광 | 온도, 습도, 광, 냉방 판단 기준 | `climate_risk`, `heat_stress`, `ventilation` |
| 3 | 근권/양액/배지/EC/pH | 함수율, EC, pH, 뿌리 갈변, 과습 판단 | `rootzone_diagnosis`, `nutrient_risk` |
| 4 | 병해충/생리장해 | 역병, 탄저병, 총채벌레, 진딧물, 바이러스 위험 | `pest_disease_risk` |
| 5 | 수확/건조/저장 | 건고추 수확 후 건조·저장 위험 판단 | `harvest_drying_storage` |

## 초기 Source 목록

### RAG-SRC-001. 농사로 고추 육묘/재배 환경 자료

- URL: https://www.nongsaro.go.kr/portal/ps/psx/psxa/mlrdCurationDtl.mo?curationNo=188
- source_type: official_guideline
- crop_type: red_pepper
- lifecycle_scope: nursery, transplanting, vegetative_growth
- expected_use: 발아, 육묘, 초기 생육 환경 기준 검색
- metadata_tags: `growth_stage:nursery`, `sensor:temperature`, `sensor:light`, `operation:transplanting`
- ingestion_status: planned

### RAG-SRC-002. 농사로 고추 시설 이상증상 현장 기술지원

- URL: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=262042&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: greenhouse_operation, vegetative_growth, fruiting
- expected_use: 하우스 고온, 환기, 배지 함수율, EC/pH, 생육 이상 진단 사례 검색
- metadata_tags: `sensor:temperature`, `sensor:substrate_moisture`, `sensor:ec`, `sensor:ph`, `risk:heat_stress`
- ingestion_status: planned

### RAG-SRC-003. 농사로 고추 양액재배 현장 기술지원

- URL: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=259682&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: hydroponics, rootzone, summer_management
- expected_use: 코이어 배지, 정식, 양액재배, 여름철 관리, 급액/배액 판단 사례 검색
- metadata_tags: `cultivation:hydroponic`, `substrate:coir`, `sensor:ec`, `sensor:ph`, `operation:irrigation`
- ingestion_status: planned

### RAG-SRC-004. 농사로 고추 생육불량/뿌리 갈변 현장 기술지원

- URL: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=249249&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: rootzone, vegetative_growth
- expected_use: 과습, 배수 불량, 고EC, 저온, 뿌리 갈변 원인 판단 검색
- metadata_tags: `risk:overwet`, `risk:root_damage`, `sensor:soil_moisture`, `sensor:ec`, `sensor:temperature`
- ingestion_status: planned

### RAG-SRC-005. 시설원예 고온기 온실 냉방 기술 기사

- URL: https://www.newsam.co.kr/mobile/article.html?no=37957
- source_type: secondary_agriculture_news
- crop_type: greenhouse_crops
- lifecycle_scope: summer_greenhouse_operation
- expected_use: 차광, 환기, 포그, 양액 냉각 등 고온기 대응 옵션 검색
- metadata_tags: `risk:heat_stress`, `operation:shading`, `operation:ventilation`, `operation:cooling`
- ingestion_status: review_required

### RAG-SRC-006. 고추 병해충 발생 주의 자료

- URL: https://news.nate.com/view/20230608n33113
- source_type: local_extension_news
- crop_type: red_pepper
- lifecycle_scope: pest_disease_management
- expected_use: 진딧물, 총채벌레, 역병, 탄저병 위험 조건 검색
- metadata_tags: `risk:pest`, `risk:anthracnose`, `risk:phytophthora`, `risk:virus_vector`
- ingestion_status: review_required

## RAG 메타데이터 규칙

각 chunk는 최소한 다음 필드를 가진다.

- `document_id`
- `source_url`
- `source_type`
- `crop_type`
- `growth_stage`
- `cultivation_type`
- `sensor_tags`
- `risk_tags`
- `operation_tags`
- `region`
- `season`
- `version`
- `effective_date`
- `chunk_id`
- `chunk_summary`
- `citation_required`

## 다음 작업

1. source별 원문 저장 가능 여부 확인
2. 공식 자료와 보조 자료 구분
3. chunk 단위 분할
4. `data/rag/pepper_expert_seed_chunks.jsonl` 확장
5. vector store 인덱싱 스크립트 설계

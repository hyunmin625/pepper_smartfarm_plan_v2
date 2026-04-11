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

### RAG-SRC-001. 농업기술길잡이 115 - 고추 (농촌진흥청 개정판)

- URL: https://www.nongsaro.go.kr/portal/ps/psx/psxa/mlrdCurationDtl.mo?curationNo=188
- local_pdf: `/mnt/d/DOWNLOAD/GPT_고추재배_훈련세트/original-know-how/고추_재배기술_최종파일-농촌진흥청.pdf`
- source_type: official_master_guideline
- crop_type: red_pepper
- lifecycle_scope: full_lifecycle (nursery to harvest/drying)
- expected_use: 모든 생육 단계별 환경 제어 기준, 시비 처방, 병해충 진단 및 방제, 건조 표준 공정의 마스터 데이터로 사용
- metadata_tags: `growth_stage:all`, `sensor:all`, `operation:all`, `trust_level:high`
- ingestion_status: ingested (initial chunks and PDF-derived precision chunks added)
- ingestion_note: 2026-04-11 local PDF에서 중복 제외 후 화분/착과, 비가림 온습도, 자동관수, 차광, 육묘 소질, 플러그 상토, 가뭄, 저온해, 고온해, 영양장애, 생리장해, 병해충/IPM, 총채벌레·진딧물 생물적 방제, 바이러스 전염 생태, 양액 급액 제어, 풋고추 저장·결로 억제, 홍고추 저장, 건고추 장기 저장·산소흡수제 포장, 하우스·열풍건조 운전 규칙 청크를 추가 추출

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

### RAG-SRC-007. 농촌진흥청 고추 품종별 온도 임계점 및 생육 지표 연구

- URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156631165
- source_type: official_research_report
- crop_type: red_pepper
- lifecycle_scope: vegetative_growth, fruiting, flowering
- expected_use: 품종별 고온/저온 임계점(13~15℃, 30~35℃), 광합성 효율, 증산율, 화분 활력 등 생육 지표 기준 검색
- metadata_tags: `sensor:temperature`, `growth_indicator:photosynthesis`, `growth_indicator:transpiration`, `risk:heat_stress`, `risk:cold_stress`
- ingestion_status: planned

### RAG-SRC-008. 건고추 품질 최적화 열풍 건조 3단계 표준 곡선 (경북농업기술원)

- URL: https://gba.go.kr/main/sub04/sub01_03_02.do
- source_type: official_guideline
- crop_type: red_pepper
- lifecycle_scope: harvest_drying_storage
- expected_use: 건고추 색택 보존을 위한 3단계(65℃ 찌기 -> 60℃ 배습 -> 55℃ 마무리) 건조 프로토콜 검색
- metadata_tags: `operation:drying`, `sensor:temperature`, `sensor:humidity`, `quality:color`, `quality:capsanthin`
- ingestion_status: planned

### RAG-SRC-009. AI 비전 기반 고추 병해충(탄저병, 총채벌레) 조기 진단 특징점 연구

- URL: https://www.mdpi.com/2077-0472/13/2/433
- source_type: research_paper
- crop_type: red_pepper
- lifecycle_scope: pest_disease_management
- expected_use: 탄저병(수침상 반점, 겹무늬), 총채벌레(은백색 반점, 잎 뒤틀림) AI 모델 학습용 특징점 정의 검색
- metadata_tags: `ai:vision`, `risk:anthracnose`, `risk:thrips`, `feature_point:concentric_ring`, `feature_point:silvering`
- ingestion_status: planned

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

권장 확장 필드:

- `source_pages`
- `source_section`
- `causality_tags`
- `visual_tags`
- `trust_level`
- `active`

## 다음 작업

1. `RAG-SRC-001` PDF에서 병해충/IPM 장의 정밀 청크 추가 추출
2. `RAG-SRC-001` PDF에서 양액재배/시설재배 장의 EC·pH·배양액 청크 추가 추출
3. 공식 자료와 보조 자료 간 중복/상충 기준 정리
4. `data/rag/pepper_expert_seed_chunks.jsonl`을 200개 이상으로 확장
5. vector store 기반 citation 검색 품질 평가

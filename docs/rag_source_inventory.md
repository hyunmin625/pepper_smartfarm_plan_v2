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
- ingestion_note: 2026-04-11 local PDF에서 중복 제외 후 화분/착과, 비가림 온습도, 자동관수, 차광, 육묘 소질, 플러그 상토, 가뭄, 저온해, 고온해, 영양장애, 생리장해, 병해충/IPM, 총채벌레·진딧물 생물적 방제, 바이러스 전염 생태, 양액 급액 제어, 풋고추 저장·결로 억제, 홍고추 저장, 건고추 장기 저장·산소흡수제 포장, 하우스·열풍건조 운전 규칙 청크를 추가 추출했고, 이어서 역병 초기 발병률·호밀 혼화·아인산 예방, 탄저병 빗물 전파·비가림 위생, 가루이/진딧물/나방 세부 운용 규칙, 비가림 측지·적심·관비 횟수, 건고추 예건·천일건조 건조대 기준까지 확장했다.

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

### RAG-SRC-010. 농사로 작물기술정보 - 고추

- URL: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=101628&menuId=PS03172&sSeCode=335001
- source_type: official_guideline
- crop_type: red_pepper
- lifecycle_scope: nursery, transplanting, flowering, harvest
- expected_use: 생육 적온, pH, 싹틔우기, 육묘 기간, 아주심기 적기, 수확·품질 기준의 기본 규칙 청크화
- metadata_tags: `growth_stage:nursery/transplanting/harvest`, `sensor:temperature`, `sensor:ph`, `quality:pungency`
- ingestion_status: ingested

### RAG-SRC-011. 농사로 작목정보 포털 - 고추 농작업 일정/품종 정보

- URL: https://www.nongsaro.go.kr/portal/farmTechMain.ps?menuId=PS65291&stdPrdlstCode=VC011205
- source_type: official_guideline
- crop_type: red_pepper
- lifecycle_scope: yearly_cropping_plan, cultivar_selection
- expected_use: 반촉성/보통/촉성 작형 일정, 에너지 절감 기술, 품종별 역병 저항성·착과 안정성 기준 청크화
- metadata_tags: `season:all`, `cultivar:all`, `operation:cropping_plan`, `operation:energy_saving`
- ingestion_status: ingested

### RAG-SRC-012. 농사로 고추 생육이 불량하고 활착되지 않아요

- URL: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=246474&menuId=PS00077&totalSearchYn=Y
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: transplanting, early_vegetative_growth
- expected_use: 활착 불량, 잔류 제초제, 산성 토양, 깊이갈이·토양개량 처방 검색
- metadata_tags: `risk:poor_establishment`, `risk:herbicide_residue`, `sensor:ph`, `sensor:soil_moisture`
- ingestion_status: ingested

### RAG-SRC-013. 농사로 고추 석회결핍 증상이 나타나고 영양제를 주어도 개선이 안돼요

- URL: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentNsSub.ps?cntntsNo=262393&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: vegetative_growth, flowering
- expected_use: 붕소 과잉, 질소 과다, 생리장해 회복 절차 청크화
- metadata_tags: `risk:boron_toxicity`, `risk:nutrient_imbalance`, `operation:fertigation_review`
- ingestion_status: ingested

### RAG-SRC-014. 농사로 미끌애꽃노린재 이용 기술

- URL: https://www.nongsaro.go.kr/portal/ps/pss/pssa/nnmyInsectSearchDtl.ps?menuId=PS00407&nnmyInsectCode=E00000004
- source_type: official_guideline
- crop_type: red_pepper
- lifecycle_scope: flowering, fruiting
- expected_use: 애꽃노린재 방사 시기, 정착 확인, 추가 방사 기준 청크화
- metadata_tags: `risk:thrips`, `operation:biocontrol`, `sensor:sticky_trap_count`, `sensor:flower_sampling`
- ingestion_status: ingested

### RAG-SRC-015. 농촌진흥청 보도자료 - 고추, 아주심기 시기 저온 노출 기간 길수록 생육 뚝

- URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156753597&pWise=main&pWiseMain=L4
- source_type: official_research_report
- crop_type: red_pepper
- lifecycle_scope: transplanting, early_recovery, harvest
- expected_use: 저온 노출 기간과 광합성·증산·착색 저하의 정량 기준 청크화
- metadata_tags: `risk:cold_stress`, `sensor:temperature`, `sensor:cold_duration_days`, `quality:red_fruit_ratio`
- ingestion_status: ingested

### RAG-SRC-016. 농사로 고추가 잘 자라지 않고 열매 끝이 휘어요

- URL: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=262042&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: fruiting, summer_greenhouse_operation
- expected_use: 곡과, 고온·환기 실패, 근권 수분 변동, 남부권 작형 전환 기준 청크화
- metadata_tags: `risk:curved_fruit`, `risk:heat_stress`, `operation:cropping_plan`, `sensor:substrate_moisture`
- ingestion_status: ingested

### RAG-SRC-017. 지역 품종 뉴스 - 건고추용 신품종 홍고은

- URL: https://www.ajunews.com/view/20211220150333398
- source_type: local_extension_news
- crop_type: dried_red_pepper
- lifecycle_scope: fruiting, harvest_drying_storage
- expected_use: 건고추용 고색도 품종 후보의 ASTA color, 매운맛, 외관 품질 기준 참고
- metadata_tags: `cultivar:honggoeun`, `quality:asta`, `quality:wrinkle`, `quality:capsaicinoid`
- ingestion_status: ingested_with_review_flag

### RAG-SRC-018. 농사로 정식 후 생육초기 생육불량 기술지원

- URL: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=253556&menuId=PS00077&totalSearchYn=Y
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: transplanting, early_vegetative_growth
- expected_use: 미숙 유기질퇴비, 암모니아 가스 피해, 활착 지연, TSWV 동반 제거 기준 청크화
- metadata_tags: `risk:ammonia_gas_injury`, `risk:poor_establishment`, `operation:irrigation`, `operation:fertilizer_pause`
- ingestion_status: ingested

### RAG-SRC-019. 농사로 수직배수 불량에 의한 시설 풋고추 과습 피해

- URL: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentNsSub.ps?cntntsNo=208295&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: vegetative_growth, fruiting, next_cycle_recovery
- expected_use: 경반층, 과습 지속시간, 조기 수확, 심토파쇄·볏짚·고이랑 개선 기준 청크화
- metadata_tags: `risk:poor_drainage`, `risk:root_browning`, `sensor:soil_moisture`, `operation:subsoiling`
- ingestion_status: ingested

### RAG-SRC-020. 농사로 고추꽃과 열매 낙화 및 웃자람 기술지원

- URL: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=247587&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: flowering, fruiting, rainy_season_recovery
- expected_use: 과차광, 장마기 낙화, 웃자람, 잎/과실 비율 불균형, EC 조정 규칙 청크화
- metadata_tags: `risk:flower_drop`, `risk:low_light_stress`, `operation:shading_control`, `operation:fruit_thinning`
- ingestion_status: ingested

### RAG-SRC-021. 농사로 고추묘 새순 오그라듦 기술지원

- URL: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=251951&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: nursery, transplanting
- expected_use: 육묘기 과습·약해형 장해, 회복 온도·광·폐기 기준 청크화
- metadata_tags: `risk:nursery_growth_stop`, `risk:overwet`, `sensor:substrate_moisture`, `operation:nursery_recovery`
- ingestion_status: ingested

### RAG-SRC-022. 농사로 시설고추 첫서리 후 낙화 기술지원

- URL: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=242390&menuId=PS00077&totalSearchYn=Y
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: flowering, fruiting, terminal_crop_decision
- expected_use: 첫서리 이후 상부 낙화·기형과·검은 씨, 총채벌레·흰가루병 동반 시 철거 판단 청크화
- metadata_tags: `risk:first_frost_damage`, `risk:flower_drop`, `risk:terminal_crop_decline`, `operation:crop_termination`
- ingestion_status: ingested

### RAG-SRC-023. 농사로 뿌리 발달 지연과 활착 지연 기술지원

- URL: https://nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=208731&menuId=PS00077&totalSearchYn=Y
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: nursery, transplanting, early_vegetative_growth
- expected_use: 노화묘, 깊은 정식, 적과, 진딧물·응애 동반 회복, 정식 깊이 기준 청크화
- metadata_tags: `risk:overaged_seedling`, `risk:deep_transplant`, `sensor:seedling_age`, `operation:fruit_thinning`
- ingestion_status: ingested

### RAG-SRC-024. 농사로 특정품종 활착 불량 원인과 저온 민감성

- URL: https://www.nongsaro.go.kr/portal/ps/psz/psza/contentSub.ps?cntntsNo=207176&menuId=PS00077
- source_type: field_case
- crop_type: red_pepper
- lifecycle_scope: transplanting, early_vegetative_growth
- expected_use: 해비치 품종의 저온 민감성, 순화, 정식 시기 보수화 기준 청크화
- metadata_tags: `cultivar:haevichi`, `risk:cultivar_cold_sensitivity`, `sensor:outside_min_temperature`, `operation:variety_selection`
- ingestion_status: ingested

### RAG-SRC-025. 지방농촌진흥기관 뉴스 - 루비홍 품종 특성

- URL: https://rda.go.kr/board/board.do?boardId=farmlcltinfo&currPage=51&dataNo=100000802147&mode=updateCnt&prgId=day_farmlcltinfoEntry&searchEDate=&searchKey=&searchSDate=&searchVal=
- source_type: local_extension_news
- crop_type: dried_red_pepper
- lifecycle_scope: fruiting, harvest_drying_storage
- expected_use: 루비홍의 ASTA color, 과실 크기, 매운맛 수준, 비가림 적응성 참고용 청크화
- metadata_tags: `cultivar:rubihong`, `quality:asta`, `quality:capsaicinoid`, `cultivation:rain_shelter`
- ingestion_status: ingested_with_review_flag

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
5. 계절·센서 이상·현장 사례 포함 retrieval eval을 100건 이상으로 확장
6. vector store 기반 citation 검색 품질 평가와 multi-turn contextual retrieval 설계 보강

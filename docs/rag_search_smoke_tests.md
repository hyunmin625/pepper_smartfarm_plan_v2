# RAG Search Smoke Tests

이 문서는 로컬 RAG 인덱스가 기본 태그와 키워드로 검색되는지 확인하는 smoke test를 정의한다.

## 전제

먼저 인덱스를 생성한다.

```bash
./.venv/bin/python scripts/validate_rag_chunks.py
./.venv/bin/python scripts/build_rag_index.py --skip-embeddings
```

검색은 keyword + metadata matching을 기본으로 수행한다. `OPENAI_API_KEY`가 있으면 OpenAI embedding 경로를, 없으면 local TF-IDF + SVD 또는 local-backed Chroma 경로를 사용할 수 있다. 검증 시에는 `--no-vector`로 keyword-only 경로를 고정할 수 있다.

```bash
./.venv/bin/python scripts/search_rag_index.py "heat_stress temperature flowering"
./.venv/bin/python scripts/search_rag_index.py "heat_stress temperature flowering" --vector-backend chroma --chroma-embedding-backend local
```

전체 smoke test는 다음 명령으로 실행한다.

```bash
./.venv/bin/python scripts/rag_smoke_test.py
```

검색 hit rate 평가는 다음 명령으로 실행한다.

```bash
./.venv/bin/python scripts/evaluate_rag_retrieval.py --fail-under 1.0
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend local --fail-under 1.0
./.venv/bin/python scripts/run_rag_validation_suite.py --fail-under 1.0 --output-json artifacts/reports/rag_validation_suite_latest.json --output-md artifacts/reports/rag_validation_suite_latest.md
./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend local
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend local
./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend openai
```

`scripts/run_rag_validation_suite.py`는 공통 retrieval eval `110건`과 stage-specific retrieval eval `16건`을 keyword/local 기준으로 한 번에 실행하고 JSON/Markdown 요약을 남긴다.

## Smoke Test Query

| 목적 | Query | 기대 chunk |
|---|---|---|
| 고온/차광/환기 판단 | `heat_stress temperature flowering` | `pepper-climate-001` |
| 과습/뿌리 갈변 판단 | `overwet root_damage soil_moisture` | `pepper-rootzone-001` |
| 양액/배액 EC 판단 | `feed_ec drain_ec drain_rate` | `pepper-hydroponic-001` |
| 병해충 의심 판단 | `thrips anthracnose vision_symptom` | `pepper-pest-001` |
| 육묘/정식 판단 | `nursery transplanting temperature` | `pepper-lifecycle-001` |
| 안전/정책 판단 | `decision_support approval audit` | `pepper-agent-001` |
| 화분/착과 온도 판단 | `화분 착과 야간 13도 18도` | `pepper-flowering-pollen-001` |
| 비가림 자동관수 판단 | `-20kPa 자동관수 석회결핍 일소 열과` | `pepper-irrigation-tensiometer-001` |
| 건고추 저장 위험 판단 | `건고추 저장 함수율 18% 곰팡이 갈변` | `pepper-dry-storage-001` |
| 비가림 재배력 판단 | `비가림 하우스 늦서리 첫서리 작부체계` | `pepper-rain-shelter-calendar-001` |
| 정식기 저온/재정식 판단 | `정식기 저온 13도 18도 재정식 동해` | `pepper-lowtemp-regional-recovery-001` |
| 장마 전후 대응 판단 | `장마 역병 탄저병 선수확 배수` | `pepper-monsoon-prevention-001` |
| 태풍 피해 대응 판단 | `태풍 도복 낙과 지주 보강 배수` | `pepper-typhoon-response-001` |
| 우박 회복 판단 | `우박 측지 유인 재정식 경제성` | `pepper-hail-recovery-001` |
| 풋고추 저온저장 판단 | `풋고추 저장 7도 95 종자갈변` | `pepper-green-storage-temperature-001` |
| 풋고추 결로 억제 판단 | `풋고추 결로 천공필름 팬 30분 꼭지 무름` | `pepper-green-packaging-condensation-001` |
| 홍고추 저장 판단 | `홍고추 저장 5도 10도 에틸렌 사과 토마토` | `pepper-red-storage-ethylene-001` |
| 건고추 장기저장 판단 | `건고추 7월 8월 함수율 18 훈증 UV 포장` | `pepper-dry-storage-maintenance-001` |
| 고춧가루 포장 판단 | `고춧가루 나일론 PE 산소흡수제 색도 매운맛` | `pepper-powder-packaging-oxygen-001` |
| 하우스 건조 판단 | `하우스 건조 35 40도 결로 제습 환기` | `pepper-house-drying-hygiene-001` |
| 열풍건조 효율 판단 | `반절 열풍건조 60도 건조시간 절반 캡산틴` | `pepper-hotair-drying-split-001` |
| 수확 후 세척 위생 판단 | `수확 후 큐어링 세척기 세척솔 곰팡이 오염` | `pepper-postharvest-wash-hygiene-001` |
| 플러그 상토 판단 | `플러그 상토 pH 6.0 6.5 EC 0.5 1.2 분형근` | `pepper-plug-substrate-001` |
| 가뭄 대응 판단 | `가뭄 pF 2.0 2.5 점적관수 멀칭` | `pepper-drought-001` |
| 동해/재정식 판단 | `동해 -0.7 -1.85 10% 50% 재정식` | `pepper-cold-injury-001` |
| 고온해 회복 판단 | `30도 40도 일소 낙화 생장점` | `pepper-heat-injury-001` |
| 영양장애 진단 판단 | `하위엽 황화 EC 높음 질소 과잉 칼리 과다` | `pepper-nutrient-diagnosis-001` |
| 칼슘·붕소 결핍 판단 | `석회결핍과 붕소결핍 함몰 흑갈색 생장점 정지` | `pepper-calcium-boron-001` |
| 생리장해 복합 판단 | `석과 열과 일소과 화분관 신장 토양수분 급변` | `pepper-physiological-disorders-001` |
| 오전 광 확보 판단 | `오전 광합성 70 80 커튼 골재 차광` | `pepper-morning-light-001` |
| 비가림 구조 판단 | `비가림 폭 7.0m 높이 3.5m 고깔형 천창` | `pepper-rainshelter-structure-001` |
| 비가림 표준 시비 판단 | `비가림 990㎡ 질소 19.0kg 토양 EC 0.3` | `pepper-rainshelter-fertilizer-ec-001` |
| 비가림 초기 저일조 판단 | `정식 후 26일 저온 저일조 첫 수확 10일 지연` | `pepper-rainshelter-lowlight-yield-001` |
| 비가림 매운맛 저하 판단 | `저온 저일조 캡사이신 디하이드로캡사이신 매운맛` | `pepper-rainshelter-lowlight-pungency-001` |
| 비가림 관비 염류 판단 | `관비 분할공급 토양 EC 상승 속도 연작 비가림` | `pepper-rainshelter-fertigation-salinity-001` |
| 비가림 멀칭/세척 판단 | `투명 멀칭 2 3도 흑색 멀칭 담수 세척 3회` | `pepper-rainshelter-mulch-leaching-001` |
| 비가림 보온자재 판단 | `부직포 보온 덮개 -4.9도 26 28% 증수` | `pepper-rainshelter-frost-cover-001` |
| 비가림 재식거리 판단 | `재식거리 100 120cm 20 35cm 밀식 약제 도달성` | `pepper-rainshelter-density-001` |
| 생육 적온·pH 판단 | `25 28도 pH 6.0 5.0 역병 기형과` | `pepper-crop-env-thresholds-001` |
| 반촉성 재배 일정 판단 | `반촉성 12월 하순 1월 중순 파종 2월 중순 정식 5월 중순 수확` | `pepper-semiforcing-schedule-001` |
| 촉성 에너지 절감 판단 | `촉성재배 8월 중하순 파종 다겹 보온커튼 46 연료 절감` | `pepper-forcing-energy-saving-001` |
| 코코피트 세척 판단 | `코코피트 EC 0.5 이하 수분 40 50 정식 전 세척` | `pepper-hydroponic-coir-prewash-001` |
| 뿌리 갈변 프로파일 판단 | `수분 37.4 41.7 EC 1.85 1.91 뿌리 갈변` | `pepper-root-browning-overwet-profile-001` |
| 붕소 과잉 판단 | `붕소 포함 NK 칼슘 비료 신엽 황화 위로 굽는 잎 수정 불량` | `pepper-boron-excess-diagnosis-001` |
| 애꽃노린재 방사 판단 | `미끌애꽃노린재 50cm 총채벌레 피해 전 방사` | `pepper-orius-release-timing-001` |
| 정식기 저온 노출 기간 판단 | `15 10도 7일 광합성 효율 44 증산 57` | `pepper-transplant-cold-duration-001` |
| 곡과 고온·근권 판단 | `33.9도 환풍기 불완전 코이어 수분 28.2 36.8 굽은과` | `pepper-curved-fruit-heat-rootzone-001` |
| 남부권 작형 전환 판단 | `6월 파종 8월 하순 정식 10 12월 수확 50 50 코이어` | `pepper-curved-fruit-cropping-shift-001` |
| 미숙퇴비 암모니아 피해 판단 | `미숙 퇴비 암모니아 가스 부정근` | `pepper-establishment-ammonia-compost-001` |
| 과차광 장마기 낙화 판단 | `차광량 90 장마 낙화 웃자람` | `pepper-flowerdrop-heavy-shading-001` |
| 첫서리 후 낙화 판단 | `첫서리 외기 0 1.2 상부 2 3마디 낙화 검은 씨` | `pepper-firstfrost-flowerdrop-001` |
| 노화묘 깊은 정식 판단 | `105일 노화묘 깊게 심기 지제부 새뿌리` | `pepper-overaged-seedling-deep-001` |
| 역병 초기 발병률 판단 | `장마 전 초기 발병률 10% 장마 후 75%` | `pepper-phytophthora-early-incidence-002` |
| 호밀 혼화·고휴재배 판단 | `호밀 혼화 고휴재배 역병 60%` | `pepper-phytophthora-rye-highridge-002` |
| 역병 아인산 예방 판단 | `아인산 pH 5.5 6.5 7 14일 간격` | `pepper-phytophthora-phosphite-002` |
| 탄저병 빗물 전파 판단 | `탄저병 99% 빗물 전파 4일 10일 잠복` | `pepper-anthracnose-rain-spread-002` |
| 탄저병 비가림 위생 판단 | `비가림 탄저병 85 95 병든 과실 즉시 제거` | `pepper-anthracnose-rainshelter-sanitation-002` |
| 담배가루이 임계치 방제 판단 | `담배가루이 10마리 7일 간격 2회 그을음병` | `pepper-whitefly-threshold-control-001` |
| 가루이 지중해이리응애 방사 판단 | `지중해이리응애 80 120마리 1주 후 2 3마리` | `pepper-whitefly-swirskii-release-001` |
| 진딧물 바이러스 방제 시작 판단 | `진딧물 5월 하순 CMV 보독 비래 살포 시작` | `pepper-aphid-virus-spray-window-001` |
| 진딧물 살포 방식 판단 | `진딧물 잎 뒷면 진하게 소량 살포 약해 저항성` | `pepper-aphid-coverage-resistance-001` |
| 나방 성페로몬 배치 판단 | `성페로몬 10a 6개 80 20 온실 안팎` | `pepper-budworm-pheromone-layout-001` |
| 비가림 측지 제거 판단 | `비가림 측지 30 50 70일 3회 제거` | `pepper-rainshelter-side-shoot-001` |
| 비가림 적심 판단 | `초장 2m 1.5m 적심` | `pepper-rainshelter-topping-001` |
| 비가림 관비 횟수 판단 | `비가림 관비 2주 1회 노동력` | `pepper-rainshelter-fertigation-interval-001` |
| 건고추 예건 판단 | `45 50일 홍고추 1 2일 음지 예건` | `pepper-drying-precure-001` |
| 천일건조 건조대 판단 | `천일건조 40 50cm 건조대` | `pepper-sundry-rack-001` |
| 균핵병 감염 창 판단 | `균핵병 2 3일 습기 20도 무가온` | `pepper-sclerotinia-infection-window-001` |
| 균핵병 멀칭/점적 판단 | `균핵병 전면 멀칭 점적관수` | `pepper-sclerotinia-mulch-drip-001` |
| 시들음병 감별 판단 | `시들음병 역병보다 느림 껍질 벗겨짐` | `pepper-fusarium-symptom-diff-001` |
| 시들음병 윤작/석회 판단 | `시들음병 pH 6.5 7.0 석회 5년 윤작` | `pepper-fusarium-rotation-liming-001` |
| 잿빛곰팡이 감염 창 판단 | `잿빛곰팡이병 24도 6시간 포화습도` | `pepper-graymold-infection-window-001` |
| 흰별무늬병 위생 판단 | `흰별무늬병 흰색 중심 스프링클러 자제` | `pepper-white-star-spot-sanitation-001` |
| 흰비단병 진단 판단 | `흰비단병 비단 같은 균사 배추씨 균핵` | `pepper-southern-blight-diagnosis-001` |
| 무름병 상처 전염 판단 | `무름병 물에 데친 것처럼 8월 담배나방` | `pepper-soft-rot-wound-insect-prevention-001` |
| 잎굴파리 고온 세대 판단 | `잎굴파리 30도 11 13일 15회 발생` | `pepper-leafminer-temperature-generation-001` |
| 잎굴파리 분할 살포 판단 | `잎굴파리 5 7일 3회 황색점착리본` | `pepper-leafminer-three-spray-001` |
| 뿌리혹선충 훈증 판단 | `뿌리혹선충 3 4주 전 훈증 5 7일 밀봉` | `pepper-rootknot-fumigation-sealing-001` |
| 잔류농약 농도 판단 | `농약 농도 2배 잔류량 2배 물량 배량` | `pepper-pesticide-residue-concentration-001` |
| 농약 혼용 순서 판단 | `수화제 WG SC 유제 액제 혼용 순서` | `pepper-pesticide-mix-order-001` |

## Metadata Filter Test

| 목적 | Query / Filter | 기대 chunk |
|---|---|---|
| 생육 단계와 신뢰도 필터 | `정식 야간 온도`, `growth_stage=transplanting`, `trust_level=high` | `pepper-transplant-001` |
| 출처 섹션 부분 일치 필터 | `건고추 65℃ 건조`, `source_section=열풍 건조` | `pepper-drying-001` |
| 품종 필터 | `역병 저항성`, `cultivar=wongang_1` | `pepper-cultivar-phytophthora-resistance-001` |
| 품종+계절 필터 | `야간 최저온 18도`, `cultivar=cheongyang`, `season=winter` | `pepper-root-browning-winter-heating-001` |
| 지역+계절 필터 | `표토 10cm 관수 비료 중단 TSWV 제거`, `region=chungnam_boryeong`, `season=spring` | `pepper-establishment-ammonia-remediation-001` |
| 품종+계절+하우스 필터 | `경반층 30 40cm 관수 5일 후 수분 25 30`, `cultivar=cheongyang`, `season=winter`, `greenhouse_type=plastic_house` | `pepper-greenhouse-poor-drainage-overwet-001` |
| 회복조치 필터 | `1회 관수량 줄이고 15 20일 과실 수확 심토파쇄`, `cultivar=cheongyang`, `season=winter`, `greenhouse_type=plastic_house` | `pepper-greenhouse-poor-drainage-remediation-001` |
| 육묘하우스 필터 | `새순 오그라듦 과습 약해형 장해`, `greenhouse_type=nursery_house`, `season=spring` | `pepper-nursery-curling-overwet-001` |
| 품종 저온민감성 필터 | `해비치 5월 5일 이후 정식`, `cultivar=haevichi`, `season=spring` | `pepper-cultivar-haevichi-cold-001` |
| 품종 품질형 필터 | `루비홍 ASTA color 146 생과중 20.4g`, `cultivar=rubihong`, `greenhouse_type=rain_shelter` | `pepper-cultivar-rubihong-001` |
| 가루이 천적 하우스 필터 | `지중해이리응애 80 120마리`, `greenhouse_type=plastic_house` | `pepper-whitefly-swirskii-release-001` |
| 진딧물 방제 시점 계절 필터 | `5월 하순 CMV 보독 진딧물`, `season=spring` | `pepper-aphid-virus-spray-window-001` |
| 비가림 관비 필터 | `2주 1회 관비`, `greenhouse_type=rain_shelter` | `pepper-rainshelter-fertigation-interval-001` |
| 건조 섹션 필터 | `건조대 40 50cm`, `source_section=천일건조` | `pepper-sundry-rack-001` |
| 겨울 시설 잔류 필터 | `겨울 시설 잔류농약`, `season=winter` | `pepper-pesticide-residue-greenhouse-winter-001` |
| 균핵병 섹션 필터 | `균핵 2년 생존 20 22도`, `source_section=균핵병` | `pepper-sclerotinia-pathogen-survival-001` |
| 시들음병 섹션 필터 | `시들음병 26 30도 산성 토양`, `source_section=시들음병` | `pepper-fusarium-acidic-sandy-soil-001` |
| 흰비단병 섹션 필터 | `흰비단병 흰 균사 77.5 89.4`, `source_section=흰비단병` | `pepper-southern-blight-early-fungicide-001` |

## 통과 기준

- 각 query에서 기대 chunk가 상위 3개 안에 포함된다.
- 현재 기준 smoke test는 기본 query 80개와 metadata filter query 18개, 총 98개를 검증한다.
- 결과 metadata에 `document_id`, `source_url`, `risk_tags`, `sensor_tags`가 포함된다.
- `citation_required`가 true인 chunk는 `source_url`, `source_pages`, `source_section`을 가진다.
- 필터 query는 지정한 metadata 조건을 만족하는 chunk만 반환한다.
- 현재 기준 retrieval eval은 110개 case에서 keyword-only MRR 0.9909, local vector MRR 1.0, local-backed Chroma MRR 0.9955, OpenAI-backed Chroma MRR 0.9803이다.

## 다음 개선

- 병해충/IPM, 양액 pH/EC, 염류장해 query 추가
- retrieval query builder에 `docs/rag_contextual_retrieval_strategy.md`의 최근 3~5일 이벤트 태그 반영
- local vector, local-backed Chroma, OpenAI-backed Chroma를 포함한 하이브리드 검색 가중치 비교

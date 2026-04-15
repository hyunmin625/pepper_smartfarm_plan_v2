# RAG Next Steps

이 문서는 현재 RAG 구축 상태에서 실제 적고추 온실 스마트팜 운영 수준으로 가기 위해 보완해야 할 핵심 과제를 정리한다.

## 현재 상태

- `data/rag/pepper_expert_seed_chunks.jsonl` 기준 RAG seed chunk는 250개다.
- `scripts/build_rag_index.py --skip-embeddings`로 로컬 JSON 인덱스를 재생성할 수 있다.
- `scripts/validate_rag_chunks.py`로 JSONL 필수 필드, 중복 `chunk_id`, citation 경고를 확인할 수 있다.
- `scripts/search_rag_index.py`는 keyword 검색, local TF-IDF + SVD vector score, OpenAI embedding 기반 vector score, ChromaDB vector score, metadata hard filter를 지원한다.
- `scripts/rag_smoke_test.py`는 기본 query 80개와 metadata filter query 18개, 총 98개를 검증한다.
- `scripts/evaluate_rag_retrieval.py` 기준 keyword-only는 110개 case hit rate 1.0, MRR 0.9909이고, local vector hybrid는 hit rate 1.0, MRR 1.0, local-backed Chroma hybrid는 hit rate 1.0, MRR 0.9955, OpenAI-backed Chroma hybrid는 hit rate 1.0, MRR 0.9803이다.
- `evals/rag_stage_retrieval_eval_set.jsonl` 기준 stage-specific retrieval eval 16개 case는 keyword-only와 local vector hybrid 모두 hit rate 1.0, MRR 1.0이다.
- `scripts/build_chroma_index.py`로 persistent Chroma collection을 만들 수 있고, 현재는 local-backed와 OpenAI-backed collection 검증까지 완료했다.

## 1. Knowledge Expansion

운영용 RAG의 최소 기준인 200개 청크와 중기 기준 250개 청크는 달성했다. 다음 확장은 `farm_case` 계층 보강과 `Grodan Delta/GT Master` 기반 적고추 수량·병충해 예방 규칙의 단계별 세분화에 초점을 둔다.

우선 확장 대상:

- `RAG-SRC-001` PDF의 병해충/IPM 장: 풋마름병, 저장·건조 잔여 세부, 약제·안전사용 잔여 항목
- `RAG-SRC-001` PDF의 양액재배/시설재배 장: EC, pH, 배양액 조성, 배액률, 염류집적
- `RAG-SRC-002~004` 현장 기술지원 사례: 이상증상, 뿌리 갈변, 배지 함수율, 현장 진단
- 품종별 온도·착과·착색·병저항성 기준
- 지역별 재배력, 월별 작업, 지역 기상 리스크

확장 기준:

- 동일 기준값만 반복하는 청크는 제외한다.
- 판단에 쓰이는 임계값, 원인-결과, 센서 연결, 작업 대응이 있는 내용만 청크화한다.
- 각 청크는 `source_pages`, `source_section`, `trust_level`, `causality_tags`, `visual_tags`를 우선 채운다.

확장 전 정리:

- 초기 시드 청크 중 `source_pages`, `source_section`이 없는 항목을 보강한다.
- 신규 청크는 `scripts/validate_rag_chunks.py` 오류 0건 상태에서만 인덱싱한다.

## 2. Vector Search

현재 검색은 keyword-only baseline, local vector hybrid, local-backed Chroma hybrid, OpenAI-backed Chroma hybrid가 모두 동작한다. 현재 기본 score는 OpenAI-backed Chroma에 local blend 4.0을 적용해 4모드 상위 성능을 맞춰 둔 상태다.

구현 완료:

- local TF-IDF + SVD vector 모델 유지 및 가중치 조정
- ChromaDB persistent vector store 연동
- `artifacts/chroma_db/pepper_expert_manifest_local.json`, `artifacts/chroma_db/pepper_expert_manifest_openai.json`에 embedding backend와 generated_at 기록
- query embedding과 metadata filter를 결합한 hybrid retrieval 구현
- keyword-only, local vector, local-backed Chroma 결과 비교

남은 구현:

- 110개 eval을 140개 이상으로 확대해 현 기본 score가 유지되는지 재검증
- keyword-only, local vector, local-backed Chroma, OpenAI-backed Chroma 4모드 결과를 고정 리포트로 관리
- Semantic + Keyword 가중치 최적화

운영 전 기준:

- embedding 모델 버전 변경 시 전체 재임베딩
- citation 없는 검색 결과는 운영 판단에 사용하지 않음
- 공식 출처와 현장 로그가 충돌하면 공식 출처를 우선하되, farm-specific override는 별도 신뢰 등급으로 관리

## 3. Metadata Filtering

메타데이터 hard filter는 1차 구현되어 있으나 운영 수준의 필터 체계가 더 필요하다.

필수 filter:

- `growth_stage`: nursery, transplanting, flowering, fruiting, harvest_drying_storage
- `cultivation_type`: greenhouse, rain_shelter, soil, hydroponic, rockwool_block, rockwool_slab, grodan_delta_6_5, grodan_gt_master
- `sensor_tags`: temperature, humidity, soil_moisture, ec, ph, vision_symptom
- `risk_tags`: heat_stress, flower_drop, calcium_deficiency, anthracnose, phytophthora
- `source_type`: official_master_guideline, field_case, farm_case, internal_sop
- `active`: false 청크 제외

고도화 과제:

- `source_section` 부분 일치 filter
- `region`, `season`, `cultivar`, `greenhouse_type` 필드 추가
- `trust_level` 기반 reranking
- multi-turn context로 최근 3~5일 상태와 현재 생육 단계를 함께 필터링

## 4. Farm Data Feedback

실제 농장 운영 데이터는 RAG의 별도 지식 계층으로 축적한다.

기준 문서:

- [farm_case RAG 환류 파이프라인](./farm_case_rag_pipeline.md)
- [farm_case event window 규칙](./farm_case_event_window_builder.md)
- [farm_case 후보 스키마](../schemas/farm_case_candidate_schema.json)
- [farm_case 후보 -> RAG chunk 변환 스크립트](../scripts/build_farm_case_rag_chunks.py)

수집 대상:

- 센서 시계열: 온습도, 광, CO2, 토양수분, EC, pH, 배액률
- 작업 로그: 관수, 환기, 차광, 방제, 수확, 건조, 저장 조치
- AI 판단 로그: 입력 상태, 검색 chunk, 추천, 승인 여부, 실행 결과
- 성공/실패 사례: 고온 대응 성공, 과습 실패, 병해 확산, 저장 곰팡이 발생
- 작업자 메모와 사진: 비전 태그와 함께 저장

RAG 변환 흐름:

1. 운영 로그와 센서 구간을 event 단위로 묶는다.
2. 결과가 확인된 사례만 `farm_case` 후보로 만든다.
3. 사람이 원인과 교훈을 검토한다.
4. `farm_id`, `zone_id`, `cultivar`, `season`, `outcome` metadata를 붙인다.
5. 공식 지식과 충돌하지 않는 범위에서 RAG에 반영한다.

이 흐름은 `Phase 9. 재학습 및 운영 고도화`와 연결하며, 파인튜닝 데이터 후보와 RAG 지식 후보를 분리해 관리한다.

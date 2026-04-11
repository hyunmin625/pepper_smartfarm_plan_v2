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
./.venv/bin/python scripts/build_chroma_index.py --embedding-backend local
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend local --fail-under 1.0
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend local
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend local
./.venv/bin/python scripts/build_chroma_index.py --embedding-backend openai
./.venv/bin/python scripts/evaluate_rag_retrieval.py --vector-backend chroma --chroma-embedding-backend openai --fail-under 1.0
./.venv/bin/python scripts/compare_rag_retrieval_modes.py --candidate-backend chroma --chroma-embedding-backend openai
```

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

## Metadata Filter Test

| 목적 | Query / Filter | 기대 chunk |
|---|---|---|
| 생육 단계와 신뢰도 필터 | `정식 야간 온도`, `growth_stage=transplanting`, `trust_level=high` | `pepper-transplant-001` |
| 출처 섹션 부분 일치 필터 | `건고추 65℃ 건조`, `source_section=열풍 건조` | `pepper-drying-001` |

## 통과 기준

- 각 query에서 기대 chunk가 상위 3개 안에 포함된다.
- 현재 기준 smoke test는 기본 query 22개와 metadata filter query 2개, 총 24개를 검증한다.
- 결과 metadata에 `document_id`, `source_url`, `risk_tags`, `sensor_tags`가 포함된다.
- `citation_required`가 true인 chunk는 `source_url`, `source_pages`, `source_section`을 가진다.
- 필터 query는 지정한 metadata 조건을 만족하는 chunk만 반환한다.
- 현재 기준 retrieval eval은 keyword-only MRR 0.9583, local vector MRR 1.0, local-backed Chroma MRR 1.0, OpenAI-backed Chroma MRR 1.0이다.

## 다음 개선

- 병해충/IPM, 양액 pH/EC, 염류장해 query 추가
- 더 긴 평가셋으로 4모드 재검증
- local vector, local-backed Chroma, OpenAI-backed Chroma를 포함한 하이브리드 검색 가중치 비교

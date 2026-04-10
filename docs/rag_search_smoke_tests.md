# RAG Search Smoke Tests

이 문서는 로컬 RAG 인덱스가 기본 태그와 키워드로 검색되는지 확인하는 smoke test를 정의한다.

## 전제

먼저 인덱스를 생성한다.

```bash
python3 scripts/build_rag_index.py
```

검색은 현재 embedding 없이 keyword + metadata matching으로 수행한다.

```bash
python3 scripts/search_rag_index.py "heat_stress temperature flowering"
```

전체 smoke test는 다음 명령으로 실행한다.

```bash
python3 scripts/rag_smoke_test.py
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

## 통과 기준

- 각 query에서 기대 chunk가 상위 3개 안에 포함된다.
- 결과 metadata에 `document_id`, `source_url`, `risk_tags`, `sensor_tags`가 포함된다.
- `citation_required`가 true인 chunk는 `source_url`을 가진다.

## 다음 개선

- 한국어 query alias 추가: `고온`, `과습`, `배액`, `총채벌레`, `정식`
- OpenAI embedding 또는 별도 vector DB 연결
- eval set과 검색 결과를 연결해 RAG hit rate 측정

# Hybrid RRF retriever benchmark — 2026-04-17

## 결론 (TL;DR)

- **HybridRagRetriever (keyword + OpenAI RRF) 벤치마크는 이번 라운드에서 미완료다.** `OpenAIEmbeddingRetriever`가 필요로 하는 `text-embedding-3-small` 호출이 **429 `insufficient_quota`** 로 전량 실패했다. 벤치마크 실행 시점 기준 OpenAI 계정 quota가 고갈 상태였다.
- Local-only 경로(`keyword`, `tfidf`)만 `evals/rag_retrieval_eval_set.jsonl` + `evals/rag_stage_retrieval_eval_set.jsonl` 총 **126 case**로 측정했다.
- **즉시 운영 영향**: `.env`의 `OPS_API_RETRIEVER_TYPE=openai` 설정과 `ops-api` `create_app()`의 OpenAI retriever 주입은 quota 복구 전까지 **live 검색이 실패**한다. quota 복구 전까지는 한시적으로 `OPS_API_RETRIEVER_TYPE=keyword`로 롤백하는 것을 검토해야 한다.
- 결정 eval 벤치마크(Phase F 방식, 250 cases, extended200 + blind50) 기준 `hybrid` 평가는 quota 복구 후 재시도로 이관한다.

## 측정값 (126 case, top-k=5, local-only)

| retriever | case_count | avg recall@5 | any_hit@5 | MRR | elapsed_sec |
|---|---:|---:|---:|---:|---:|
| **keyword** | 126 | **0.9444** | 0.9444 | 0.9114 | 1.2 |
| **tfidf** | 126 | 0.7698 | 0.7698 | 0.6060 | 0.4 |
| openai | 126 | *0.000 (quota_exceeded)* | — | — | 195.7 |
| hybrid | 126 | *0.000 (quota_exceeded)* | — | — | 192.0 |

> 126 case는 `rag_retrieval_eval_set.jsonl` (110) + `rag_stage_retrieval_eval_set.jsonl` (16). 이 eval set은 token-rich 쿼리(`"heat_stress temperature flowering"`)로 의도적으로 구성되어 keyword retriever에 유리하다. Phase F의 `keyword 0.164` 수치는 decision eval 250 case(자연어 scenario) 기준이며 본 평가와는 다른 축이다.

## 해석

1. **이 eval set에서 keyword가 0.944로 최상**이라는 사실 자체는 hybrid 결정에 쓸 수 없다. 이 eval은 keyword-token 과적합 성격이 있고, 운영 중 ops-api 결정 경로 입력은 자연어 scenario다.
2. **tfidf 0.77 vs keyword 0.94**: local TF-IDF+SVD 24d는 여전히 keyword 토큰 overlap + trust boost를 이기지 못한다. 이 결과는 Phase F의 `keyword 0.164 vs tfidf 0.172` 근접 관찰과 결이 같다(두 local 경로 모두 limited).
3. **openai/hybrid 0 수치는 품질 신호가 아니라 인프라 실패**다. 126 case에 대한 `insufficient_quota` 429가 OpenAI API 재호출로 재현된다.

## 의사결정 백로그 (quota 복구 후)

1. `text-embedding-3-small` quota 복구 확인 후 벤치마크 재실행: `scripts/benchmark_hybrid_retriever.py` (기본 3 retriever, --output-json/md 덮어쓰기 됨)
2. Phase F 기준 벤치마크 재실행: `scripts/evaluate_fine_tuned_model.py --rag-retriever-type {keyword,openai,hybrid} --live-rag ...`로 decision eval 250 case 기준 recall@5 측정. 이것이 production 승격 결정용 핵심 수치.
3. `ops-api/ops_api/app.py`가 hybrid retriever 주입까지 받도록 `create_retriever("hybrid", ...)` 경로 확정 (이미 `retriever_vector.create_retriever`는 `"hybrid"` 인자 지원).

## 운영 즉시 조치 권장

`.env`의 production 라인을 quota 복구까지 아래와 같이 한시 전환:

```
# Phase F 기준 기본값. quota 복구 시 openai로 되돌린다.
OPS_API_RETRIEVER_TYPE=keyword
```

복구 이후 hybrid 벤치마크가 keyword 대비 `safety_policy / edge_case` 카테고리에서 유의미한 개선을 보여주면 `OPS_API_RETRIEVER_TYPE=hybrid`로 승격한다.

## 산출물

- `scripts/benchmark_hybrid_retriever.py` — 신규. 3 retriever × 126 eval case recall@5 / MRR / any_hit 집계.
- `artifacts/reports/hybrid_retriever_benchmark.md` — 본 포스트모템.
- `artifacts/reports/hybrid_retriever_benchmark.json` — 최초 실행 raw 결과(openai/hybrid 0, note=`retrieval_error: 429`).
- `artifacts/reports/hybrid_retriever_benchmark_local_only.md` + `.json` — quota 이슈 없는 local-only 재실행 결과(keyword / tfidf).

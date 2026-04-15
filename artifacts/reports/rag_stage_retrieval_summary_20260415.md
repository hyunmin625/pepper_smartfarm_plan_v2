# Stage Retrieval Eval Summary (2026-04-15)

## Scope

- eval set: `evals/rag_stage_retrieval_eval_set.jsonl`
- case count: `16`
- coverage:
  - nursery
  - transplanting
  - flowering
  - fruiting
  - harvest_drying_storage
- filters exercised:
  - `growth_stage`
  - `cultivation_type`

## Results

- keyword-only: `hit_rate 1.0`, `MRR 1.0`
- local vector hybrid: `hit_rate 1.0`, `MRR 1.0`

## Interpretation

- `RAG-SRC-038`~`044`와 stage-specific chunk 추가 이후에도 단계별 metadata hard filter retrieval이 깨지지 않았다.
- `Grodan Delta 6.5`, `Grodan GT Master`, `촉성재배`, `수확/건조/저장` query가 모두 top-1에서 기대 청크를 반환했다.
- 현재 stage-aware retrieval baseline은 keyword/local 두 경로 모두 `16/16` PASS 상태다.

## Artifacts

- `artifacts/reports/rag_stage_retrieval_keyword_20260415.json`
- `artifacts/reports/rag_stage_retrieval_local_20260415.json`

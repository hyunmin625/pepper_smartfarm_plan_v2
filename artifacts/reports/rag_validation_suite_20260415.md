# RAG Validation Suite Summary

## Scope

- index: `artifacts/rag_index/pepper_expert_index.json`
- fail_under: `1.0`
- suites: `common, stage`
- modes: `keyword, local`

## Results

| Suite | Mode | Cases | Hit Rate | MRR | Status |
|---|---:|---:|---:|---:|---|
| common | keyword | 110 | 1.0000 | 0.9909 | PASS |
| common | local | 110 | 1.0000 | 1.0000 | PASS |
| stage | keyword | 16 | 1.0000 | 1.0000 | PASS |
| stage | local | 16 | 1.0000 | 1.0000 | PASS |

## Aggregates

| Mode | Cases | Hit Rate | MRR |
|---|---:|---:|---:|
| keyword | 126 | 1.0000 | 0.9921 |
| local | 126 | 1.0000 | 1.0000 |

## Eval Sets

- common: `evals/rag_retrieval_eval_set.jsonl`
- stage: `evals/rag_stage_retrieval_eval_set.jsonl`

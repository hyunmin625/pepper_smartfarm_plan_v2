#!/usr/bin/env python3
"""Validate llm_orchestrator.retriever_vector backends.

Runs a handful of invariants against the two dense retriever classes
(`TfidfSvdRagRetriever`, `OpenAIEmbeddingRetriever`) plus the keyword
baseline, so we catch regressions before the orchestrator is wired to
them in ops-api.

Checks:

  1. TfidfSvdRagRetriever loads cleanly from the local index and has the
     expected 24-dim SVD model + 226 documents.
  2. TfidfSvdRagRetriever.search() returns RetrievedChunk objects whose
     chunk_ids are all present in the corpus (no hallucinated ids).
  3. TfidfSvdRagRetriever.search() ranks results by descending score.
  4. `create_retriever("keyword")` dispatches to KeywordRagRetriever.
  5. `create_retriever("vector")` dispatches to TfidfSvdRagRetriever.
  6. `create_retriever("unknown")` raises ValueError.
  7. OpenAIEmbeddingRetriever loads the 1536-dim index cleanly (skipped
     when `pepper_openai_embed_index.json` is missing — matches the
     skip-embeddings build mode).
  8. OpenAIEmbeddingRetriever.search() — only if
     OPENAI_LIVE_RETRIEVER_SMOKE=1. One live query against the index;
     asserts recall shape.

Exit code 0 on success, 1 on first failing invariant. Runs in <5 s
without network/API spend by default. The optional live OpenAI call is
opt-in because it consumes quota.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass

from llm_orchestrator.retriever import KeywordRagRetriever, RetrievedChunk  # noqa: E402
from llm_orchestrator.retriever_vector import (  # noqa: E402
    DEFAULT_LOCAL_RAG_INDEX_PATH,
    DEFAULT_OPENAI_RAG_INDEX_PATH,
    OpenAIEmbeddingRetriever,
    TfidfSvdRagRetriever,
    create_retriever,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        print(f"  FAIL: {message}", flush=True)
        raise SystemExit(1)
    print(f"  ok  : {message}", flush=True)


def _env_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    print(f"REPO_ROOT={REPO_ROOT}")
    print(f"local_index={DEFAULT_LOCAL_RAG_INDEX_PATH}")
    print(f"openai_index={DEFAULT_OPENAI_RAG_INDEX_PATH}")
    print()

    # 1) TfidfSvdRagRetriever boot
    print("[1] TfidfSvdRagRetriever boot")
    tfidf = TfidfSvdRagRetriever()
    _assert(tfidf.svd_dim == 24, f"svd_dim=24 (got {tfidf.svd_dim})")
    _assert(len(tfidf.rows) >= 200, f"docs loaded ≥200 (got {len(tfidf.rows)})")

    # Build a chunk_id corpus to reject hallucinated ids later
    corpus_chunk_ids = {d["chunk_id"] for d in tfidf.rows}

    # 2) TfidfSvdRagRetriever.search() returns corpus chunk_ids only
    print("\n[2] TfidfSvdRagRetriever.search — results stay in corpus")
    hits = tfidf.search(
        query="온도가 매우 높고 강한 일사에 노출된 개화기 고추",
        task_type="climate_risk",
        zone_id="gh-01-zone-a",
        growth_stage="flowering",
        limit=5,
    )
    _assert(all(isinstance(h, RetrievedChunk) for h in hits), "all hits are RetrievedChunk")
    _assert(
        all(h.chunk_id in corpus_chunk_ids for h in hits),
        "all chunk_ids present in corpus (no hallucination)",
    )
    _assert(len(hits) <= 5, f"limit honored (got {len(hits)})")

    # 3) ranked by descending score
    print("\n[3] TfidfSvdRagRetriever — descending score order")
    scores = [h.score for h in hits]
    _assert(
        all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1)),
        f"scores monotone descending: {scores}",
    )

    # 4) factory → keyword
    print("\n[4] create_retriever('keyword') dispatches to KeywordRagRetriever")
    kw = create_retriever("keyword")
    _assert(isinstance(kw, KeywordRagRetriever), "keyword factory returns KeywordRagRetriever")

    # 5) factory → vector
    print("\n[5] create_retriever('vector') dispatches to TfidfSvdRagRetriever")
    vec = create_retriever("vector")
    _assert(isinstance(vec, TfidfSvdRagRetriever), "vector factory returns TfidfSvdRagRetriever")

    # 6) unknown type raises
    print("\n[6] create_retriever('unknown') raises")
    raised = False
    try:
        create_retriever("flux_capacitor")
    except ValueError:
        raised = True
    _assert(raised, "unknown type raises ValueError")

    # 7) OpenAI index static checks (skip if file missing). This validates
    # the precomputed local artifact without creating a query embedding.
    print("\n[7] OpenAI embedding index static checks")
    if not DEFAULT_OPENAI_RAG_INDEX_PATH.exists():
        print("  skip: openai index not built (run build_rag_index.py without --skip-embeddings)")
    else:
        with DEFAULT_OPENAI_RAG_INDEX_PATH.open("r", encoding="utf-8") as handle:
            openai_index = json.load(handle)
        openai_docs = [
            row
            for row in openai_index.get("documents", [])
            if row.get("embedding")
        ]
        _assert(len(openai_docs) >= 200, f"docs loaded ≥200 (got {len(openai_docs)})")
        emb_len = len(openai_docs[0]["embedding"]) if openai_docs else 0
        _assert(emb_len == 1536, f"embedding dim=1536 (got {emb_len})")

    # 8) OpenAI live search. This is intentionally opt-in even when
    # OPENAI_API_KEY is present in .env, because the call consumes quota.
    print("\n[8] OpenAIEmbeddingRetriever.search — live query")
    if not _env_truthy("OPENAI_LIVE_RETRIEVER_SMOKE"):
        print("  skip: set OPENAI_LIVE_RETRIEVER_SMOKE=1 to run the quota-consuming live query")
    elif not DEFAULT_OPENAI_RAG_INDEX_PATH.exists():
        _assert(False, "OPENAI_LIVE_RETRIEVER_SMOKE=1 requires the OpenAI embedding index")
    elif not os.getenv("OPENAI_API_KEY"):
        _assert(False, "OPENAI_LIVE_RETRIEVER_SMOKE=1 requires OPENAI_API_KEY")
    else:
        oai = OpenAIEmbeddingRetriever()
        oai_hits = oai.search(
            query="작업자가 있는 곳에서 관수 readback 신호가 사라졌다",
            task_type="failure_response",
            zone_id="gh-01-zone-a",
            growth_stage="fruit_expansion",
            limit=5,
        )
        _assert(len(oai_hits) <= 5, f"limit honored (got {len(oai_hits)})")
        _assert(
            all(h.chunk_id in corpus_chunk_ids for h in oai_hits),
            "all openai hits present in corpus",
        )
        oai_scores = [h.score for h in oai_hits]
        _assert(
            all(oai_scores[i] >= oai_scores[i + 1] for i in range(len(oai_scores) - 1)),
            f"openai scores monotone: {oai_scores}",
        )

    print("\nall invariants passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

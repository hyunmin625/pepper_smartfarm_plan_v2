#!/usr/bin/env python3
"""Build a persistent Chroma vector store for pepper RAG documents."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from build_rag_index import EMBEDDING_MODEL, get_embeddings
from rag_chroma_store import (
    DEFAULT_CHROMA_PATH,
    get_default_collection_name,
    reset_collection,
    scalarize_metadata,
)
from search_rag_index import load_index

load_dotenv()


def resolve_embedding_backend(requested: str, api_key: str | None) -> str:
    if requested == "auto":
        return "openai" if api_key else "local"
    if requested == "openai" and not api_key:
        raise SystemExit("OPENAI_API_KEY not found. OpenAI-backed Chroma build requires embeddings API access.")
    return requested


def default_manifest_path(embedding_backend: str, text_field: str) -> str:
    suffix = embedding_backend
    if text_field != "text":
        suffix = f"{suffix}_{text_field}"
    return f"artifacts/chroma_db/pepper_expert_manifest_{suffix}.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", default="artifacts/rag_index/pepper_expert_index.json")
    parser.add_argument("--chroma-path", default=str(DEFAULT_CHROMA_PATH))
    parser.add_argument("--collection-name")
    parser.add_argument(
        "--embedding-backend",
        choices=("auto", "openai", "local"),
        default="auto",
        help="Embedding backend for vectors stored in Chroma",
    )
    parser.add_argument("--text-field", choices=("text", "chunk_summary"), default="text")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--manifest")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    embedding_backend = resolve_embedding_backend(args.embedding_backend, api_key)
    collection_name = args.collection_name or get_default_collection_name(embedding_backend, args.text_field)
    manifest_path = Path(args.manifest or default_manifest_path(embedding_backend, args.text_field))

    index = load_index(Path(args.index))
    documents = index.get("documents", [])
    if not documents:
        raise SystemExit(f"No documents found in {args.index}")

    texts = [str(document.get(args.text_field) or document["text"]) for document in documents]
    embeddings: list[list[float]] = []
    embedding_model_name = "local_tfidf_svd"

    if embedding_backend == "openai":
        client = OpenAI(api_key=api_key)
        print(f"Generating OpenAI embeddings for {len(texts)} documents using {EMBEDDING_MODEL}...")
        for start in range(0, len(texts), args.batch_size):
            batch = texts[start : start + args.batch_size]
            print(f"  batch {start // args.batch_size + 1}: {len(batch)} docs")
            embeddings.extend(get_embeddings(batch, client))
        embedding_model_name = EMBEDDING_MODEL
    else:
        if args.text_field != "text":
            raise SystemExit("Local Chroma backend currently supports --text-field text only.")
        missing_local = [document["id"] for document in documents if "local_embedding" not in document]
        if missing_local:
            raise SystemExit(f"local_embedding missing for {len(missing_local)} documents. Rebuild the JSON index first.")
        embeddings = [document["local_embedding"] for document in documents]
        print(f"Using existing local embeddings for {len(embeddings)} documents.")

    chroma_path = Path(args.chroma_path)
    collection = reset_collection(
        chroma_path,
        collection_name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": embedding_model_name,
            "embedding_backend": embedding_backend,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    metadatas = []
    ids = []
    for document in documents:
        metadata = dict(document.get("metadata", {}))
        metadata["chunk_id"] = document["id"]
        metadatas.append(scalarize_metadata(metadata))
        ids.append(document["id"])

    collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "index_path": args.index,
        "chroma_path": str(chroma_path),
        "collection_name": collection_name,
        "embedding_model": embedding_model_name,
        "embedding_backend": embedding_backend,
        "document_count": len(documents),
        "text_field": args.text_field,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        f"wrote {len(documents)} vectors to {chroma_path} collection {collection_name}"
        f" using {embedding_backend} embeddings"
    )
    print(f"wrote manifest to {manifest_path}")


if __name__ == "__main__":
    main()

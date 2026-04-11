#!/usr/bin/env python3
"""Helpers for persisting and querying a Chroma vector store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CHROMA_PATH = Path("artifacts/chroma_db/pepper_expert")
DEFAULT_COLLECTION_NAME = "pepper_expert_chunks"


def get_default_collection_name(embedding_backend: str, text_field: str = "text") -> str:
    normalized_backend = (embedding_backend or "local").lower()
    normalized_field = (text_field or "text").lower()
    suffix = normalized_backend
    if normalized_field != "text":
        suffix = f"{suffix}_{normalized_field}"
    return f"{DEFAULT_COLLECTION_NAME}_{suffix}"


def ensure_chromadb():
    try:
        import chromadb  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "chromadb is not installed. Install it before using the Chroma vector backend."
        ) from exc
    return chromadb


def get_persistent_client(path: Path):
    chromadb = ensure_chromadb()
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def get_collection(path: Path, name: str):
    client = get_persistent_client(path)
    return client.get_collection(name=name)


def reset_collection(path: Path, name: str, metadata: dict[str, Any] | None = None):
    client = get_persistent_client(path)
    existing = {collection.name for collection in client.list_collections()}
    if name in existing:
        client.delete_collection(name=name)
    return client.create_collection(name=name, metadata=metadata or {"hnsw:space": "cosine"})


def scalarize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    scalarized: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            scalarized[key] = value
            continue
        scalarized[key] = json.dumps(value, ensure_ascii=False)
    return scalarized


def distance_to_similarity(distance: float | None) -> float:
    if distance is None:
        return 0.0
    return max(0.0, 1.0 - float(distance))

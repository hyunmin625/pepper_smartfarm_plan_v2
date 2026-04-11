#!/usr/bin/env python3
"""Local TF-IDF + SVD vector utilities for lightweight RAG retrieval."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

import numpy as np

TOKEN_PATTERN = re.compile(r"[0-9a-z가-힣]+")
MAX_FEATURES = 1024
MAX_DIM = 24


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    a = np.array(v1, dtype=float)
    b = np.array(v2, dtype=float)
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)
    if a_norm == 0.0 or b_norm == 0.0:
        return 0.0
    return float(np.dot(a, b) / (a_norm * b_norm))


def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return matrix / norms


def build_local_vector_model(
    texts: list[str],
    max_features: int = MAX_FEATURES,
    max_dim: int = MAX_DIM,
) -> tuple[dict[str, Any], list[list[float]]]:
    tokenized_docs = [tokenize(text) for text in texts]
    if not tokenized_docs:
        return {}, []

    document_frequency: Counter[str] = Counter()
    total_frequency: Counter[str] = Counter()
    for tokens in tokenized_docs:
        if not tokens:
            continue
        counts = Counter(tokens)
        document_frequency.update(counts.keys())
        total_frequency.update(counts)

    ranked_terms = sorted(
        document_frequency,
        key=lambda term: (-document_frequency[term], -total_frequency[term], term),
    )[:max_features]
    if not ranked_terms:
        return {}, [[] for _ in texts]

    vocabulary = {term: index for index, term in enumerate(ranked_terms)}
    doc_count = len(texts)
    idf = [
        round(math.log((doc_count + 1) / (document_frequency[term] + 1)) + 1.0, 6)
        for term in ranked_terms
    ]

    matrix = np.zeros((doc_count, len(ranked_terms)), dtype=float)
    for row_index, tokens in enumerate(tokenized_docs):
        counts = Counter(token for token in tokens if token in vocabulary)
        for term, count in counts.items():
            column_index = vocabulary[term]
            matrix[row_index, column_index] = (1.0 + math.log(count)) * idf[column_index]

    matrix = _normalize_rows(matrix)

    component_count = min(max_dim, doc_count, len(ranked_terms))
    if component_count <= 0:
        return {}, [[] for _ in texts]

    u, singular_values, vt = np.linalg.svd(matrix, full_matrices=False)
    component_count = min(component_count, len(singular_values))
    components = vt[:component_count]
    document_embeddings = (u[:, :component_count] * singular_values[:component_count]).tolist()

    model = {
        "type": "tfidf_svd",
        "token_pattern": TOKEN_PATTERN.pattern,
        "max_features": max_features,
        "svd_dim": component_count,
        "terms": ranked_terms,
        "idf": idf,
        "components": components.tolist(),
    }
    return model, document_embeddings


def get_local_query_embedding(query: str, model: dict[str, Any]) -> list[float]:
    terms = model.get("terms") or []
    idf_values = model.get("idf") or []
    components = np.array(model.get("components") or [], dtype=float)
    if not terms or not idf_values or components.size == 0:
        return []

    vocabulary = {term: index for index, term in enumerate(terms)}
    vector = np.zeros(len(terms), dtype=float)
    counts = Counter(token for token in tokenize(query) if token in vocabulary)
    for term, count in counts.items():
        column_index = vocabulary[term]
        vector[column_index] = (1.0 + math.log(count)) * float(idf_values[column_index])

    norm = np.linalg.norm(vector)
    if norm == 0.0:
        return [0.0] * components.shape[0]

    normalized = vector / norm
    return (normalized @ components.T).tolist()

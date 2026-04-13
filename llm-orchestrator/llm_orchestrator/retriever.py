from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAG_PATHS = [
    REPO_ROOT / "data" / "rag" / "pepper_expert_seed_chunks.jsonl",
    REPO_ROOT / "data" / "rag" / "farm_case_seed_chunks.jsonl",
]
TOKEN_RE = re.compile(r"[a-zA-Z0-9가-힣_]+")


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    chunk_summary: str
    source_type: str
    trust_level: str
    score: float
    source_url: str | None = None
    source_section: str | None = None
    citation_required: bool = False

    def as_prompt_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "summary": self.chunk_summary,
            "source_type": self.source_type,
            "trust_level": self.trust_level,
            "source_url": self.source_url,
            "source_section": self.source_section,
            "citation_required": self.citation_required,
            "score": round(self.score, 3),
        }

    def as_citation_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_section": self.source_section,
        }


class KeywordRagRetriever:
    def __init__(self, *, corpus_paths: list[Path] | None = None) -> None:
        self.corpus_paths = corpus_paths or DEFAULT_RAG_PATHS
        self.rows = self._load_rows(self.corpus_paths)

    def search(
        self,
        *,
        query: str,
        task_type: str,
        zone_id: str | None = None,
        growth_stage: str | None = None,
        limit: int = 5,
    ) -> list[RetrievedChunk]:
        query_tokens = _tokenize(" ".join(part for part in [query, task_type, zone_id or "", growth_stage or ""] if part))
        scored: list[RetrievedChunk] = []
        for row in self.rows:
            score = _score_row(row, query_tokens, zone_id=zone_id, growth_stage=growth_stage)
            if score <= 0:
                continue
            scored.append(
                RetrievedChunk(
                    chunk_id=str(row.get("chunk_id") or "unknown-chunk"),
                    document_id=str(row.get("document_id") or "unknown-doc"),
                    chunk_summary=str(row.get("chunk_summary") or ""),
                    source_type=str(row.get("source_type") or "unknown"),
                    trust_level=str(row.get("trust_level") or "unknown"),
                    score=score,
                    source_url=str(row.get("source_url") or "") or None,
                    source_section=str(row.get("source_section") or "") or None,
                    citation_required=bool(row.get("citation_required")),
                )
            )
        scored.sort(key=lambda item: (-item.score, item.chunk_id))
        return scored[:limit]

    @staticmethod
    def _load_rows(paths: list[Path]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in paths:
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    payload = json.loads(line)
                    if isinstance(payload, dict):
                        rows.append(payload)
        return rows


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text) if len(token) >= 2}


def _score_row(
    row: dict[str, Any],
    query_tokens: set[str],
    *,
    zone_id: str | None,
    growth_stage: str | None,
) -> float:
    haystacks: list[str] = [
        str(row.get("chunk_summary") or ""),
        str(row.get("source_section") or ""),
        str(row.get("source_type") or ""),
    ]
    for key in ("risk_tags", "operation_tags", "sensor_tags", "causality_tags", "growth_stage"):
        value = row.get(key)
        if isinstance(value, list):
            haystacks.extend(str(item) for item in value)
        elif isinstance(value, str):
            haystacks.append(value)
    row_tokens = _tokenize(" ".join(haystacks))
    overlap = len(query_tokens & row_tokens)
    if overlap == 0:
        return 0.0

    score = float(overlap)
    trust_level = str(row.get("trust_level") or "unknown").lower()
    if trust_level == "high":
        score += 1.2
    elif trust_level == "medium":
        score += 0.5
    elif trust_level == "review_required":
        score -= 0.1

    if growth_stage:
        stages = row.get("growth_stage")
        if isinstance(stages, list) and growth_stage in {str(item) for item in stages}:
            score += 0.8
    if zone_id and row.get("zone_id") == zone_id:
        score += 1.0
    if row.get("source_type") == "farm_case":
        score += 0.4
    return round(score, 3)

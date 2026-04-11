#!/usr/bin/env python3
"""Validate RAG chunk JSONL files without external dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA_PATH = Path("schemas/rag_chunk_schema.json")
DEFAULT_INPUT = Path("data/rag/pepper_expert_seed_chunks.jsonl")
CHUNK_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{3}$")


def load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append((line_number, row))
    return rows


def is_string_array(value: Any, *, allow_empty: bool = False) -> bool:
    if not isinstance(value, list):
        return False
    if not allow_empty and not value:
        return False
    return all(isinstance(item, str) and item for item in value)


def validate_row(
    row: dict[str, Any],
    line_number: int,
    schema: dict[str, Any],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    required = set(schema["required"])
    allowed = set(schema["properties"])

    missing = sorted(required - set(row))
    if missing:
        errors.append(f"line {line_number}: missing required fields: {', '.join(missing)}")

    unknown = sorted(set(row) - allowed)
    if unknown:
        errors.append(f"line {line_number}: unknown fields: {', '.join(unknown)}")

    chunk_id = row.get("chunk_id")
    if isinstance(chunk_id, str):
        if not CHUNK_ID_PATTERN.match(chunk_id):
            errors.append(f"line {line_number}: chunk_id has invalid pattern: {chunk_id}")
    elif "chunk_id" in row:
        errors.append(f"line {line_number}: chunk_id must be a string")

    for field in (
        "growth_stage",
        "cultivation_type",
        "sensor_tags",
        "risk_tags",
        "operation_tags",
        "causality_tags",
        "agent_use",
    ):
        if field in row and not is_string_array(row[field]):
            errors.append(f"line {line_number}: {field} must be a non-empty string array")

    if "visual_tags" in row and not is_string_array(row["visual_tags"], allow_empty=True):
        errors.append(f"line {line_number}: visual_tags must be a string array")

    for field in ("document_id", "source_url", "source_type", "crop_type", "chunk_summary"):
        if field in row and not (isinstance(row[field], str) and row[field]):
            errors.append(f"line {line_number}: {field} must be a non-empty string")

    if "chunk_summary" in row and isinstance(row["chunk_summary"], str) and len(row["chunk_summary"]) < 20:
        errors.append(f"line {line_number}: chunk_summary must be at least 20 characters")

    if "citation_required" in row and not isinstance(row["citation_required"], bool):
        errors.append(f"line {line_number}: citation_required must be boolean")

    if row.get("citation_required") is True:
        if not row.get("source_url"):
            errors.append(f"line {line_number}: citation_required chunk must have source_url")
        if not row.get("source_pages") and not row.get("source_page") and row.get("source_type") != "internal_design":
            warnings.append(f"line {line_number}: citation_required chunk has no source page")
        if not row.get("source_section") and row.get("source_type") != "internal_design":
            warnings.append(f"line {line_number}: citation_required chunk has no source_section")

    if "source_pages" in row:
        pages = row["source_pages"]
        valid_pages = isinstance(pages, str) and bool(pages)
        valid_pages = valid_pages or (
            isinstance(pages, list) and bool(pages) and all(isinstance(page, int) and page > 0 for page in pages)
        )
        if not valid_pages:
            errors.append(f"line {line_number}: source_pages must be a non-empty string or positive integer array")

    if "source_page" in row and not (isinstance(row["source_page"], int) and row["source_page"] > 0):
        errors.append(f"line {line_number}: source_page must be a positive integer")

    if row.get("source_type") == "farm_case":
        for field in ("farm_id", "zone_id", "outcome"):
            if not row.get(field):
                warnings.append(f"line {line_number}: farm_case should include {field}")

    return errors, warnings


def validate_file(input_path: Path, schema_path: Path) -> int:
    schema = load_schema(schema_path)
    rows = load_jsonl(input_path)
    all_errors: list[str] = []
    all_warnings: list[str] = []

    chunk_ids = [row["chunk_id"] for _, row in rows if isinstance(row.get("chunk_id"), str)]
    counts = Counter(chunk_ids)
    duplicates = sorted(chunk_id for chunk_id, count in counts.items() if count > 1)
    if duplicates:
        all_errors.append(f"duplicate chunk_id values: {', '.join(duplicates)}")

    for line_number, row in rows:
        errors, warnings = validate_row(row, line_number, schema)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    for warning in all_warnings:
        print(f"WARN {warning}")
    for error in all_errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"validated rows: {len(rows)}")
    print(f"duplicate chunk_id count: {len(duplicates)}")
    print(f"warnings: {len(all_warnings)}")
    print(f"errors: {len(all_errors)}")
    return 1 if all_errors else 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--schema", default=str(SCHEMA_PATH))
    args = parser.parse_args()
    raise SystemExit(validate_file(Path(args.input), Path(args.schema)))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate citation coverage for example outputs and eval responses."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_KNOWLEDGE_BASE = Path("artifacts/rag_index/pepper_expert_index.json")
DEFAULT_EXAMPLE_FILES = (
    Path("data/examples/state_judgement_samples.jsonl"),
    Path("data/examples/forbidden_action_samples.jsonl"),
)


def load_json(path: Path) -> Any:
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


def load_chunk_map(path: Path) -> dict[str, dict[str, Any]]:
    if path.suffix == ".jsonl":
        rows = load_jsonl(path)
        return {row["chunk_id"]: row for _, row in rows if isinstance(row.get("chunk_id"), str)}

    payload = load_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("documents"), list):
        raise ValueError(f"{path}: expected index JSON with a documents array")
    chunk_map: dict[str, dict[str, Any]] = {}
    for document in payload["documents"]:
        if not isinstance(document, dict) or not isinstance(document.get("id"), str):
            continue
        metadata = document.get("metadata")
        normalized = dict(metadata) if isinstance(metadata, dict) else {}
        normalized["chunk_id"] = document["id"]
        normalized.setdefault("chunk_summary", document.get("chunk_summary"))
        chunk_map[document["id"]] = normalized
    return chunk_map


def normalize_retrieved_context(value: Any, record_id: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{record_id}: retrieved_context must be an array")

    chunk_ids: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            chunk_ids.append(item)
            continue
        if isinstance(item, dict) and isinstance(item.get("chunk_id"), str) and item["chunk_id"]:
            chunk_ids.append(item["chunk_id"])
            continue
        raise ValueError(f"{record_id}: retrieved_context items must be chunk_id strings or objects with chunk_id")
    return chunk_ids


def normalize_citations(value: Any, record_id: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{record_id}: citations must be an array")

    citations: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{record_id}: citation #{index} must be an object")
        chunk_id = item.get("chunk_id")
        document_id = item.get("document_id")
        source_url = item.get("source_url")
        if not isinstance(chunk_id, str) or not chunk_id:
            raise ValueError(f"{record_id}: citation #{index} must include non-empty chunk_id")
        if document_id is not None and not isinstance(document_id, str):
            raise ValueError(f"{record_id}: citation #{index} document_id must be a string or null")
        if source_url is not None and not isinstance(source_url, str):
            raise ValueError(f"{record_id}: citation #{index} source_url must be a string or null")
        citations.append(
            {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "source_url": source_url,
            }
        )
    return citations


def unwrap_output(row: dict[str, Any]) -> dict[str, Any]:
    for field in ("output", "response", "preferred_output"):
        if isinstance(row.get(field), dict):
            return row[field]
    return row


def classify_coverage(required_ids: set[str], cited_ids: set[str]) -> str:
    if not required_ids:
        return "not_used" if not cited_ids else "sufficient"
    if not cited_ids:
        return "insufficient"
    if required_ids.issubset(cited_ids):
        return "sufficient"
    return "partial"


def validate_record(
    record_id: str,
    retrieved_ids: list[str],
    citations: list[dict[str, Any]],
    chunk_map: dict[str, dict[str, Any]],
    *,
    must_include_citations: bool,
    retrieval_coverage: str | None,
) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []

    retrieved_set = set(retrieved_ids)
    citation_ids = [citation["chunk_id"] for citation in citations]
    citation_set = set(citation_ids)

    duplicate_citations = sorted(chunk_id for chunk_id, count in Counter(citation_ids).items() if count > 1)
    if duplicate_citations:
        errors.append(f"{record_id}: duplicate cited chunk_id values: {', '.join(duplicate_citations)}")

    unknown_retrieved = sorted(chunk_id for chunk_id in retrieved_set if chunk_id not in chunk_map)
    if unknown_retrieved:
        warnings.append(f"{record_id}: unknown retrieved_context chunk_id: {', '.join(unknown_retrieved)}")

    unknown_citations = sorted(chunk_id for chunk_id in citation_set if chunk_id not in chunk_map)
    if unknown_citations:
        errors.append(f"{record_id}: cited unknown chunk_id: {', '.join(unknown_citations)}")

    out_of_context = sorted(chunk_id for chunk_id in citation_set if chunk_id not in retrieved_set)
    if out_of_context:
        errors.append(f"{record_id}: cited chunk_id not present in retrieved_context: {', '.join(out_of_context)}")

    required_ids = {
        chunk_id
        for chunk_id in retrieved_set
        if chunk_map.get(chunk_id, {}).get("citation_required") is True
    }
    missing_required = sorted(chunk_id for chunk_id in required_ids if chunk_id not in citation_set)
    if missing_required:
        errors.append(f"{record_id}: missing citations for required chunks: {', '.join(missing_required)}")

    if must_include_citations and not citations:
        errors.append(f"{record_id}: expected citations but citations array is empty")

    for citation in citations:
        chunk_id = citation["chunk_id"]
        metadata = chunk_map.get(chunk_id)
        if not metadata:
            continue
        expected_document_id = metadata.get("document_id")
        expected_source_url = metadata.get("source_url")

        if citation.get("document_id") and expected_document_id and citation["document_id"] != expected_document_id:
            errors.append(
                f"{record_id}: citation {chunk_id} document_id mismatch "
                f"(got {citation['document_id']}, expected {expected_document_id})"
            )
        if citation.get("source_url") and expected_source_url and citation["source_url"] != expected_source_url:
            errors.append(
                f"{record_id}: citation {chunk_id} source_url mismatch "
                f"(got {citation['source_url']}, expected {expected_source_url})"
            )

    coverage_status = classify_coverage(required_ids, citation_set & required_ids)
    if retrieval_coverage is not None and retrieval_coverage != coverage_status:
        errors.append(
            f"{record_id}: retrieval_coverage mismatch "
            f"(got {retrieval_coverage}, expected {coverage_status})"
        )

    return errors, warnings, {
        "record_id": record_id,
        "retrieved_count": len(retrieved_set),
        "required_citation_count": len(required_ids),
        "citation_count": len(citation_set),
        "coverage_status": coverage_status,
    }


def validate_example_files(example_files: list[Path], chunk_map: dict[str, dict[str, Any]]) -> tuple[int, int, list[dict[str, Any]]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []

    for example_file in example_files:
        for line_number, row in load_jsonl(example_file):
            sample_id = row.get("sample_id") or f"{example_file}:{line_number}"
            input_payload = row.get("input")
            if not isinstance(input_payload, dict):
                errors.append(f"{sample_id}: input must be an object")
                continue
            output_payload = unwrap_output(row)
            try:
                retrieved_ids = normalize_retrieved_context(input_payload.get("retrieved_context"), sample_id)
                citations = normalize_citations(output_payload.get("citations"), sample_id)
            except ValueError as exc:
                errors.append(str(exc))
                continue

            row_errors, row_warnings, stats = validate_record(
                sample_id,
                retrieved_ids,
                citations,
                chunk_map,
                must_include_citations=any(chunk_map.get(chunk_id, {}).get("citation_required") is True for chunk_id in retrieved_ids),
                retrieval_coverage=output_payload.get("retrieval_coverage"),
            )
            errors.extend(row_errors)
            warnings.extend(row_warnings)
            rows.append(stats)

    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    return len(errors), len(warnings), rows


def validate_eval_responses(
    cases_path: Path,
    responses_path: Path,
    chunk_map: dict[str, dict[str, Any]],
    *,
    allow_missing_responses: bool,
) -> tuple[int, int, list[dict[str, Any]]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []

    cases = {row.get("eval_id"): row for _, row in load_jsonl(cases_path) if isinstance(row.get("eval_id"), str)}
    responses = {row.get("eval_id"): row for _, row in load_jsonl(responses_path) if isinstance(row.get("eval_id"), str)}

    missing_case_ids = sorted(response_id for response_id in responses if response_id not in cases)
    for missing_case_id in missing_case_ids:
        errors.append(f"{missing_case_id}: response has no matching eval case")

    for eval_id, case in cases.items():
        response_row = responses.get(eval_id)
        if response_row is None:
            message = f"{eval_id}: response missing"
            if allow_missing_responses:
                warnings.append(message)
                continue
            errors.append(message)
            continue

        output_payload = unwrap_output(response_row)
        try:
            retrieved_ids = normalize_retrieved_context(case.get("retrieved_context"), eval_id)
            citations = normalize_citations(output_payload.get("citations"), eval_id)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        row_errors, row_warnings, stats = validate_record(
            eval_id,
            retrieved_ids,
            citations,
            chunk_map,
            must_include_citations=bool(case.get("expected", {}).get("must_include_citations")),
            retrieval_coverage=output_payload.get("retrieval_coverage"),
        )
        errors.extend(row_errors)
        warnings.extend(row_warnings)
        rows.append(stats)

    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    return len(errors), len(warnings), rows


def print_summary(rows: list[dict[str, Any]], *, mode: str, error_count: int, warning_count: int) -> None:
    total_required = sum(row["required_citation_count"] for row in rows)
    total_citations = sum(row["citation_count"] for row in rows)
    sufficient = sum(1 for row in rows if row["coverage_status"] == "sufficient")
    not_used = sum(1 for row in rows if row["coverage_status"] == "not_used")

    print(f"mode: {mode}")
    print(f"validated rows: {len(rows)}")
    print(f"rows with sufficient coverage: {sufficient}")
    print(f"rows with citation not_used: {not_used}")
    print(f"required citation count: {total_required}")
    print(f"actual citation count: {total_citations}")
    print(f"warnings: {warning_count}")
    print(f"errors: {error_count}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--knowledge-base",
        default=str(DEFAULT_KNOWLEDGE_BASE),
        help="RAG index JSON or chunk JSONL used as citation ground truth",
    )
    parser.add_argument(
        "--examples",
        nargs="*",
        default=[str(path) for path in DEFAULT_EXAMPLE_FILES],
        help="Example JSONL files with input.retrieved_context and preferred_output.citations",
    )
    parser.add_argument("--eval-cases", help="Eval case JSONL with retrieved_context and must_include_citations")
    parser.add_argument("--responses", help="Response JSONL keyed by eval_id")
    parser.add_argument("--allow-missing-responses", action="store_true")
    args = parser.parse_args()

    chunk_map = load_chunk_map(Path(args.knowledge_base))

    if args.responses and not args.eval_cases:
        raise SystemExit("--responses requires --eval-cases")
    if args.eval_cases and not args.responses:
        raise SystemExit("--eval-cases requires --responses")

    if args.eval_cases:
        error_count, warning_count, rows = validate_eval_responses(
            Path(args.eval_cases),
            Path(args.responses),
            chunk_map,
            allow_missing_responses=args.allow_missing_responses,
        )
        print_summary(rows, mode="eval_responses", error_count=error_count, warning_count=warning_count)
        raise SystemExit(1 if error_count else 0)

    example_files = [Path(path) for path in args.examples]
    error_count, warning_count, rows = validate_example_files(example_files, chunk_map)
    print_summary(rows, mode="example_outputs", error_count=error_count, warning_count=warning_count)
    raise SystemExit(1 if error_count else 0)


if __name__ == "__main__":
    main()

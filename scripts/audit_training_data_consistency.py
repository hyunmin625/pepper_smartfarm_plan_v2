#!/usr/bin/env python3
"""Audit training sample JSONL files for duplicates and potential contradictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from build_openai_sft_datasets import DEFAULT_EVAL_FILES, load_eval_signatures, signature_for_task_input
from training_data_config import training_sample_files

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILES = training_sample_files(REPO_ROOT)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            item["_source_path"] = str(path)
            item["_source_line"] = line_number
            rows.append(item)
    return rows


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_training_input(input_payload: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(canonical_json(input_payload))
    if "summary" in normalized and "state_summary" not in normalized:
        normalized["state_summary"] = normalized.pop("summary")
    return normalized


def output_signature(task_type: str, preferred_output: dict[str, Any]) -> dict[str, Any]:
    signature: dict[str, Any] = {"task_type": task_type}
    if task_type == "forbidden_action":
        signature["decision"] = preferred_output.get("decision")
        signature["blocked_action_type"] = preferred_output.get("blocked_action_type")
        signature["risk_level"] = preferred_output.get("risk_level")
    else:
        actions = []
        for action in preferred_output.get("recommended_actions", []):
            if isinstance(action, dict):
                actions.append(action.get("action_type"))
        signature["risk_level"] = preferred_output.get("risk_level")
        signature["recommended_actions"] = actions
        signature["requires_human_approval"] = preferred_output.get("requires_human_approval")
        signature["fallback_mode"] = preferred_output.get("fallback_mode")
    return signature


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", default=[str(path) for path in DEFAULT_FILES])
    parser.add_argument(
        "--eval-files",
        nargs="*",
        default=[str(path) for path in DEFAULT_EVAL_FILES],
        help="Eval JSONL files used to detect exact task/input overlap with training samples.",
    )
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for file_name in args.files:
        rows.extend(load_jsonl(Path(file_name)))
    eval_signatures = load_eval_signatures([Path(file_name) for file_name in args.eval_files])

    errors: list[str] = []
    seen_sample_ids: set[str] = set()
    duplicate_rows: list[str] = []
    exact_rows: dict[str, tuple[str, int, str]] = {}
    by_input_signature: dict[str, list[tuple[str, int, str, str]]] = {}
    overlap_rows: list[str] = []

    for row in rows:
        sample_id = row.get("sample_id")
        source_path = row["_source_path"]
        source_line = row["_source_line"]
        if not isinstance(sample_id, str) or not sample_id:
            errors.append(f"{source_path}:{source_line}: sample_id must be a non-empty string")
            continue
        if sample_id in seen_sample_ids:
            errors.append(f"{source_path}:{source_line}: duplicate sample_id {sample_id}")
        seen_sample_ids.add(sample_id)

        task_type = row.get("task_type")
        input_value = row.get("input")
        preferred_output = row.get("preferred_output")
        if not isinstance(task_type, str) or not isinstance(input_value, dict) or not isinstance(preferred_output, dict):
            errors.append(f"{source_path}:{source_line}: task_type/input/preferred_output must be present")
            continue

        exact_signature = stable_hash(
            {"task_type": task_type, "input": input_value, "preferred_output": preferred_output}
        )
        previous = exact_rows.get(exact_signature)
        if previous is not None:
            duplicate_rows.append(
                f"{source_path}:{source_line}: duplicates {previous[0]}:{previous[1]} ({sample_id} vs {previous[2]})"
            )
        else:
            exact_rows[exact_signature] = (source_path, source_line, sample_id)

        input_signature = stable_hash({"task_type": task_type, "input": input_value})
        signature_text = canonical_json(output_signature(task_type, preferred_output))
        by_input_signature.setdefault(input_signature, []).append((source_path, source_line, sample_id, signature_text))
        eval_signature = signature_for_task_input(task_type, canonical_training_input(input_value))
        if eval_signature in eval_signatures:
            overlap_rows.append(f"{source_path}:{source_line}({sample_id}) overlaps an eval task/input pair")

    contradiction_rows: list[str] = []
    for matches in by_input_signature.values():
        distinct_signatures = {signature for _, _, _, signature in matches}
        if len(matches) > 1 and len(distinct_signatures) > 1:
            locations = ", ".join(f"{path}:{line}({sample_id})" for path, line, sample_id, _ in matches)
            contradiction_rows.append(f"potential contradiction across {locations}")

    for message in errors + duplicate_rows + contradiction_rows + overlap_rows:
        print(f"ERROR {message}", file=sys.stderr)

    print(f"files: {len(args.files)}")
    print(f"rows: {len(rows)}")
    print(f"duplicate_rows: {len(duplicate_rows)}")
    print(f"potential_contradictions: {len(contradiction_rows)}")
    print(f"eval_overlap_rows: {len(overlap_rows)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors or duplicate_rows or contradiction_rows or overlap_rows else 0)


if __name__ == "__main__":
    main()

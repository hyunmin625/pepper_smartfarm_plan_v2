#!/usr/bin/env python3
"""Build a combined eval JSONL from task-family eval files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUTS = [
    Path("evals/expert_judgement_eval_set.jsonl"),
    Path("evals/action_recommendation_eval_set.jsonl"),
    Path("evals/forbidden_action_eval_set.jsonl"),
    Path("evals/failure_response_eval_set.jsonl"),
    Path("evals/robot_task_eval_set.jsonl"),
    Path("evals/edge_case_eval_set.jsonl"),
    Path("evals/seasonal_eval_set.jsonl"),
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="*", default=[str(path) for path in DEFAULT_INPUTS])
    parser.add_argument(
        "--output",
        default="artifacts/training/combined_eval_cases.jsonl",
        help="Combined eval JSONL output path.",
    )
    parser.add_argument(
        "--include-source-file",
        action="store_true",
        help="Attach source_file to each row for manual review and traceability.",
    )
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for file_name in args.inputs:
        path = Path(file_name)
        for row in load_jsonl(path):
            if args.include_source_file:
                row = dict(row)
                row["source_file"] = path.as_posix()
            rows.append(row)

    rows.sort(key=lambda item: str(item.get("eval_id", "")))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"input_files: {len(args.inputs)}")
    print(f"rows: {len(rows)}")
    print(f"output: {output_path.as_posix()}")


if __name__ == "__main__":
    main()

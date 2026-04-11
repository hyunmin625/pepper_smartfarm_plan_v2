#!/usr/bin/env python3
"""Generate summary statistics for training sample JSONL files."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from training_data_config import training_sample_files


DEFAULT_INPUTS = training_sample_files()


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
            row["_source_file"] = path.as_posix()
            rows.append(row)
    return rows


def percentile(values: list[int], ratio: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * ratio))))
    return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="*", default=[str(path) for path in DEFAULT_INPUTS])
    parser.add_argument(
        "--output",
        default="artifacts/reports/training_sample_stats.json",
        help="JSON report output path.",
    )
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for file_name in args.inputs:
        rows.extend(load_jsonl(Path(file_name)))

    task_counts: Counter[str] = Counter()
    action_type_counts: Counter[str] = Counter()
    input_lengths: list[int] = []
    output_lengths: list[int] = []
    combined_lengths: list[tuple[int, str, str]] = []

    for row in rows:
        sample_id = str(row.get("sample_id", ""))
        task_type = str(row.get("task_type", "unknown"))
        task_counts[task_type] += 1

        input_text = json.dumps(row.get("input", {}), ensure_ascii=False, sort_keys=True)
        output_text = json.dumps(row.get("preferred_output", {}), ensure_ascii=False, sort_keys=True)
        input_len = len(input_text)
        output_len = len(output_text)
        input_lengths.append(input_len)
        output_lengths.append(output_len)
        combined_lengths.append((input_len + output_len, sample_id, row["_source_file"]))

        preferred_output = row.get("preferred_output", {})
        if isinstance(preferred_output, dict):
            for action in preferred_output.get("recommended_actions", []):
                if isinstance(action, dict):
                    action_type = action.get("action_type")
                    if isinstance(action_type, str) and action_type:
                        action_type_counts[action_type] += 1

    imbalance_ratio = 0.0
    if task_counts:
        imbalance_ratio = max(task_counts.values()) / min(task_counts.values())

    longest_samples = [
        {"sample_id": sample_id, "source_file": source_file, "combined_chars": combined_chars}
        for combined_chars, sample_id, source_file in sorted(combined_lengths, reverse=True)[:5]
    ]

    report = {
        "input_files": len(args.inputs),
        "sample_rows": len(rows),
        "task_counts": dict(sorted(task_counts.items())),
        "class_imbalance_ratio": imbalance_ratio,
        "action_type_counts": dict(sorted(action_type_counts.items())),
        "input_length_chars": {
            "min": min(input_lengths) if input_lengths else 0,
            "median": int(statistics.median(input_lengths)) if input_lengths else 0,
            "p90": percentile(input_lengths, 0.90),
            "max": max(input_lengths) if input_lengths else 0,
        },
        "output_length_chars": {
            "min": min(output_lengths) if output_lengths else 0,
            "median": int(statistics.median(output_lengths)) if output_lengths else 0,
            "p90": percentile(output_lengths, 0.90),
            "max": max(output_lengths) if output_lengths else 0,
        },
        "longest_samples": longest_samples,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"input_files: {len(args.inputs)}")
    print(f"sample_rows: {len(rows)}")
    print(f"class_imbalance_ratio: {imbalance_ratio:.2f}")
    print(f"output: {output_path.as_posix()}")


if __name__ == "__main__":
    main()

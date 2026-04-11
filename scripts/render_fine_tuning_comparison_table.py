#!/usr/bin/env python3
"""Render a Markdown comparison table from fine-tuning run manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_RUNS_DIR = Path("artifacts/fine_tuning/runs")
DEFAULT_OUTPUT = Path("artifacts/fine_tuning/fine_tuning_comparison_table.md")


def load_manifests(runs_dir: Path) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    if not runs_dir.exists():
        return manifests
    for path in sorted(runs_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_manifest_path"] = path.as_posix()
        manifests.append(payload)
    manifests.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
    return manifests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default=str(DEFAULT_RUNS_DIR))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    manifests = load_manifests(Path(args.runs_dir))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Fine-tuning Comparison Table",
        "",
        "| experiment_name | status | base_model | model_version | dataset_version | prompt_version | eval_version | training_rows | validation_rows | job_id | fine_tuned_model |",
        "|---|---|---|---|---|---|---|---:|---:|---|---|",
    ]

    for item in manifests:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item.get("experiment_name", "")),
                    str(item.get("status", "")),
                    str(item.get("base_model", "")),
                    str(item.get("model_version", "")),
                    str(item.get("dataset_version", "")),
                    str(item.get("prompt_version", "")),
                    str(item.get("eval_version", "")),
                    str(item.get("training_rows", "")),
                    str(item.get("validation_rows", "")),
                    str(item.get("job_id", "")),
                    str(item.get("fine_tuned_model", "")),
                ]
            )
            + " |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"runs: {len(manifests)}")
    print(f"output: {output_path.as_posix()}")


if __name__ == "__main__":
    main()

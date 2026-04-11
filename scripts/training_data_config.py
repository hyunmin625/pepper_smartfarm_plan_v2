#!/usr/bin/env python3
"""Shared training sample file discovery for dataset build scripts."""

from __future__ import annotations

from pathlib import Path


TRAINING_SAMPLE_PATTERNS = (
    "qa_reference_samples*.jsonl",
    "state_judgement_samples*.jsonl",
    "action_recommendation_samples*.jsonl",
    "forbidden_action_samples*.jsonl",
    "failure_response_samples*.jsonl",
    "robot_task_samples*.jsonl",
    "reporting_samples*.jsonl",
)


def training_sample_files(repo_root: Path | None = None) -> list[Path]:
    base_dir = (repo_root or Path(__file__).resolve().parents[1]) / "data" / "examples"
    files: list[Path] = []
    seen: set[Path] = set()
    for pattern in TRAINING_SAMPLE_PATTERNS:
        for path in sorted(base_dir.glob(pattern)):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(path)
    return files

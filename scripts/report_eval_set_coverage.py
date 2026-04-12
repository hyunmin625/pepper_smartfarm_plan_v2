#!/usr/bin/env python3
"""Report eval set coverage against minimum and recommended targets."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_FILES = [
    Path("evals/expert_judgement_eval_set.jsonl"),
    Path("evals/action_recommendation_eval_set.jsonl"),
    Path("evals/forbidden_action_eval_set.jsonl"),
    Path("evals/failure_response_eval_set.jsonl"),
    Path("evals/robot_task_eval_set.jsonl"),
    Path("evals/edge_case_eval_set.jsonl"),
    Path("evals/seasonal_eval_set.jsonl"),
]

MINIMUM_TARGETS = {
    "expert_judgement_eval_set.jsonl": 40,
    "action_recommendation_eval_set.jsonl": 16,
    "forbidden_action_eval_set.jsonl": 12,
    "failure_response_eval_set.jsonl": 12,
    "robot_task_eval_set.jsonl": 8,
    "edge_case_eval_set.jsonl": 16,
    "seasonal_eval_set.jsonl": 16,
}

RECOMMENDED_TARGETS = {
    "expert_judgement_eval_set.jsonl": 56,
    "action_recommendation_eval_set.jsonl": 24,
    "forbidden_action_eval_set.jsonl": 16,
    "failure_response_eval_set.jsonl": 16,
    "robot_task_eval_set.jsonl": 12,
    "edge_case_eval_set.jsonl": 24,
    "seasonal_eval_set.jsonl": 24,
}

DEFAULT_MINIMUM_TOTAL = 120
DEFAULT_RECOMMENDED_TOTAL = 160


def count_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--files",
        nargs="*",
        default=[path.as_posix() for path in DEFAULT_FILES],
        help="Eval JSONL files to inspect.",
    )
    parser.add_argument(
        "--minimum-total",
        type=int,
        default=DEFAULT_MINIMUM_TOTAL,
        help="Minimum total eval rows required before more fine-tuning.",
    )
    parser.add_argument(
        "--recommended-total",
        type=int,
        default=DEFAULT_RECOMMENDED_TOTAL,
        help="Recommended total eval rows for productization review.",
    )
    parser.add_argument(
        "--enforce-minimums",
        action="store_true",
        help="Exit non-zero when total or per-file minimum targets are not met.",
    )
    args = parser.parse_args()

    total = 0
    below_minimum: list[str] = []

    print("eval_file,current_rows,minimum_target,recommended_target,status")
    for file_name in args.files:
        path = Path(file_name)
        current = count_rows(path)
        total += current
        minimum = MINIMUM_TARGETS.get(path.name)
        recommended = RECOMMENDED_TARGETS.get(path.name)
        status = "ok"
        if minimum is not None and current < minimum:
            status = "below_minimum"
            below_minimum.append(path.name)
        elif recommended is not None and current < recommended:
            status = "below_recommended"
        print(f"{path.name},{current},{minimum},{recommended},{status}")

    print(f"total_rows,{total}")
    print(f"minimum_total_target,{args.minimum_total}")
    print(f"recommended_total_target,{args.recommended_total}")

    total_ok = total >= args.minimum_total
    recommended_ok = total >= args.recommended_total
    print(f"minimum_total_pass,{str(total_ok).lower()}")
    print(f"recommended_total_pass,{str(recommended_ok).lower()}")

    if args.enforce_minimums and (not total_ok or below_minimum):
        if not total_ok:
            print("error: total eval rows are below the minimum target.")
        if below_minimum:
            print(f"error: per-file minimums not met for {', '.join(sorted(below_minimum))}.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

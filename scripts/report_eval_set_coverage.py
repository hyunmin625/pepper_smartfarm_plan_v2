#!/usr/bin/env python3
"""Report eval set coverage against minimum, recommended, and product targets."""

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
DEFAULT_BLIND_HOLDOUT_FILE = Path("evals/blind_holdout_eval_set.jsonl")

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

PRODUCT_TARGETS = {
    "expert_judgement_eval_set.jsonl": 60,
    "action_recommendation_eval_set.jsonl": 28,
    "forbidden_action_eval_set.jsonl": 20,
    "failure_response_eval_set.jsonl": 24,
    "robot_task_eval_set.jsonl": 16,
    "edge_case_eval_set.jsonl": 28,
    "seasonal_eval_set.jsonl": 24,
}

DEFAULT_MINIMUM_TOTAL = 120
DEFAULT_RECOMMENDED_TOTAL = 160
DEFAULT_PRODUCT_TOTAL = 200
DEFAULT_BLIND_HOLDOUT_MINIMUM = 24
DEFAULT_BLIND_HOLDOUT_PRODUCT = 50
PROMOTION_BASELINE_TARGETS = {
    "extended120": DEFAULT_MINIMUM_TOTAL,
    "extended160": DEFAULT_RECOMMENDED_TOTAL,
    "extended200": DEFAULT_PRODUCT_TOTAL,
}


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
        "--product-total",
        type=int,
        default=DEFAULT_PRODUCT_TOTAL,
        help="Product-readiness total eval rows target.",
    )
    parser.add_argument(
        "--blind-holdout-file",
        default=DEFAULT_BLIND_HOLDOUT_FILE.as_posix(),
        help="Frozen blind holdout eval file to inspect separately from extended coverage.",
    )
    parser.add_argument(
        "--blind-holdout-minimum",
        type=int,
        default=DEFAULT_BLIND_HOLDOUT_MINIMUM,
        help="Minimum blind holdout row target for initial product gate review.",
    )
    parser.add_argument(
        "--blind-holdout-product-target",
        type=int,
        default=DEFAULT_BLIND_HOLDOUT_PRODUCT,
        help="Product-readiness blind holdout row target.",
    )
    parser.add_argument(
        "--enforce-minimums",
        action="store_true",
        help="Exit non-zero when total or per-file minimum targets are not met.",
    )
    parser.add_argument(
        "--promotion-baseline",
        choices=sorted(PROMOTION_BASELINE_TARGETS),
        default="extended160",
        help="Coverage baseline to use for fine-tuning promotion decisions.",
    )
    parser.add_argument(
        "--enforce-promotion-baseline",
        action="store_true",
        help="Exit non-zero when the chosen promotion baseline is not met.",
    )
    args = parser.parse_args()

    total = 0
    below_minimum: list[str] = []

    print("eval_file,current_rows,minimum_target,recommended_target,product_target,status")
    for file_name in args.files:
        path = Path(file_name)
        current = count_rows(path)
        total += current
        minimum = MINIMUM_TARGETS.get(path.name)
        recommended = RECOMMENDED_TARGETS.get(path.name)
        product = PRODUCT_TARGETS.get(path.name)
        status = "ok"
        if minimum is not None and current < minimum:
            status = "below_minimum"
            below_minimum.append(path.name)
        elif recommended is not None and current < recommended:
            status = "below_recommended"
        elif product is not None and current < product:
            status = "below_product"
        print(f"{path.name},{current},{minimum},{recommended},{product},{status}")

    print(f"total_rows,{total}")
    print(f"minimum_total_target,{args.minimum_total}")
    print(f"recommended_total_target,{args.recommended_total}")
    print(f"product_total_target,{args.product_total}")

    total_ok = total >= args.minimum_total
    recommended_ok = total >= args.recommended_total
    product_ok = total >= args.product_total
    print(f"minimum_total_pass,{str(total_ok).lower()}")
    print(f"recommended_total_pass,{str(recommended_ok).lower()}")
    print(f"product_total_pass,{str(product_ok).lower()}")
    promotion_target = PROMOTION_BASELINE_TARGETS[args.promotion_baseline]
    promotion_ok = total >= promotion_target and blind_holdout_rows >= args.blind_holdout_minimum
    print(f"promotion_baseline,{args.promotion_baseline}")
    print(f"promotion_baseline_total_target,{promotion_target}")

    blind_holdout_path = Path(args.blind_holdout_file)
    blind_holdout_rows = count_rows(blind_holdout_path)
    blind_holdout_minimum_ok = blind_holdout_rows >= args.blind_holdout_minimum
    blind_holdout_product_ok = blind_holdout_rows >= args.blind_holdout_product_target
    print(f"blind_holdout_file,{blind_holdout_path.as_posix()}")
    print(f"blind_holdout_rows,{blind_holdout_rows}")
    print(f"blind_holdout_minimum_target,{args.blind_holdout_minimum}")
    print(f"blind_holdout_product_target,{args.blind_holdout_product_target}")
    print(f"blind_holdout_minimum_pass,{str(blind_holdout_minimum_ok).lower()}")
    print(f"blind_holdout_product_pass,{str(blind_holdout_product_ok).lower()}")
    print(f"promotion_baseline_pass,{str(promotion_ok).lower()}")

    if args.enforce_minimums and (not total_ok or below_minimum):
        if not total_ok:
            print("error: total eval rows are below the minimum target.")
        if below_minimum:
            print(f"error: per-file minimums not met for {', '.join(sorted(below_minimum))}.")
        raise SystemExit(1)
    if args.enforce_promotion_baseline and not promotion_ok:
        print(
            "error: fine-tuning promotion baseline is not met. "
            f"required total rows: {promotion_target}, blind holdout minimum: {args.blind_holdout_minimum}."
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()

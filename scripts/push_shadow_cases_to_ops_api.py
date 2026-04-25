#!/usr/bin/env python3
"""Push shadow-mode cases into a running ops-api instance.

This is the production-path companion to
`scripts/run_shadow_mode_capture_cases.py`: instead of bypassing
ops-api and writing directly to the validator/shadow audit log files,
it POSTs cases through `POST /shadow/cases/capture` so the ops-api
auth, audit, and rotation guards are exercised the same way an
operator workflow would trigger them. The runner can then gate on
the `promotion_decision` returned by `GET /shadow/window` (e.g. to
fail a CI job when the shadow window slips to ``rollback`` or
``hold``).

Example usage:

    python3 scripts/push_shadow_cases_to_ops_api.py \
        --base-url http://localhost:8080 \
        --api-key operator-demo-token \
        --cases-file data/examples/shadow_mode_runtime_day0_seed_cases.jsonl \
        --gate promote

A batch-size flag splits the payload into sub-requests so very large
dumps do not exceed the request body limits.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from validate_shadow_cases import load_case_files, load_existing_request_ids, validate_case_rows


def _chunks(cases: list[dict[str, Any]], batch_size: int):
    for start in range(0, len(cases), batch_size):
        yield cases[start : start + batch_size]


def _post_capture(
    *,
    base_url: str,
    api_key: str | None,
    cases: list[dict[str, Any]],
    append: bool,
) -> dict[str, Any]:
    payload = {"append": append, "cases": cases}
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/shadow/cases/capture",
        data=data,
        headers={
            "content-type": "application/json",
            **({"x-api-key": api_key} if api_key else {}),
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:  # noqa: S310
        body = response.read().decode("utf-8")
    parsed = json.loads(body)
    return parsed.get("data") or parsed


def _fetch_window(*, base_url: str, api_key: str | None) -> dict[str, Any] | None:
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/shadow/window",
        headers={**({"x-api-key": api_key} if api_key else {})},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request) as response:  # noqa: S310
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    parsed = json.loads(body)
    return parsed.get("data") or parsed


def _evaluate_gate(gate: str | None, promotion_decision: str | None) -> tuple[bool, str]:
    if gate is None:
        return True, "no gate requested"
    if promotion_decision is None:
        return False, "shadow window is empty; cannot evaluate gate"
    order = {"rollback": 0, "hold": 1, "promote": 2}
    if promotion_decision not in order:
        return False, f"unknown promotion_decision={promotion_decision}"
    if gate not in order:
        return False, f"invalid --gate value {gate}"
    return order[promotion_decision] >= order[gate], f"promotion_decision={promotion_decision} gate>={gate}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        default="http://localhost:8080",
        help="ops-api base URL that exposes /shadow/cases/capture and /shadow/window.",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Value for the x-api-key header when ops-api runs with auth_mode=header_token.",
    )
    parser.add_argument(
        "--cases-file",
        action="append",
        required=True,
        help="JSONL file of shadow-mode cases. Pass multiple times to ingest several files.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the existing audit log instead of rotating it first (default).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Rotate the audit log before the first batch. Requires manage_runtime_mode.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Number of cases per /shadow/cases/capture call.",
    )
    parser.add_argument(
        "--gate",
        choices=("rollback", "hold", "promote"),
        default=None,
        help="Minimum promotion_decision required after ingestion. The runner exits 1 if the shadow window is below this level.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate input JSONL and exit without calling ops-api.",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip local shadow case validation before /shadow/cases/capture.",
    )
    parser.add_argument(
        "--real-case",
        action="store_true",
        help="Apply stricter real ops case rules during validation.",
    )
    parser.add_argument(
        "--expected-date",
        default=None,
        help="Expected YYYYMMDD for real ops case filename/request_id/eval_set_id consistency.",
    )
    parser.add_argument(
        "--existing-audit-log",
        action="append",
        default=[],
        help="Existing shadow audit log used to reject duplicate request_id values before append.",
    )
    args = parser.parse_args()

    if args.append and args.reset:
        print(json.dumps({"errors": ["--append and --reset are mutually exclusive"]}))
        return 2

    case_paths = [Path(path_str) for path_str in args.cases_file]
    case_rows = load_case_files(case_paths)
    cases = [row for _, _, row in case_rows]

    if not cases:
        print(json.dumps({"status": "blocked", "reason": "no cases to ingest"}))
        return 0

    if not args.skip_validation:
        existing_ids = load_existing_request_ids([Path(path) for path in args.existing_audit_log])
        validation_errors = validate_case_rows(
            case_rows,
            real_case=args.real_case,
            existing_request_ids=existing_ids,
            expected_date=args.expected_date,
        )
        if validation_errors:
            print(
                json.dumps(
                    {
                        "status": "failed",
                        "reason": "shadow case validation failed",
                        "validation_errors": validation_errors,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "validated_case_count": len(cases),
                    "real_case": args.real_case,
                    "expected_date": args.expected_date,
                    "case_files": [path.as_posix() for path in case_paths],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    first_batch = True
    last_summary: dict[str, Any] | None = None
    try:
        for batch in _chunks(cases, args.batch_size):
            first_append = args.append or not (first_batch and args.reset)
            summary = _post_capture(
                base_url=args.base_url,
                api_key=args.api_key,
                cases=batch,
                append=first_append,
            )
            last_summary = summary.get("shadow_window") or summary
            first_batch = False
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else ""
        print(
            json.dumps(
                {
                    "status": "failed",
                    "http_status": exc.code,
                    "detail": detail[:1000],
                },
                ensure_ascii=False,
            )
        )
        return 1

    window = _fetch_window(base_url=args.base_url, api_key=args.api_key)
    effective_window = window or last_summary or {}
    promotion_decision = effective_window.get("promotion_decision") if isinstance(effective_window, dict) else None
    gate_pass, gate_reason = _evaluate_gate(args.gate, promotion_decision)

    report = {
        "status": "ok" if gate_pass else "failed",
        "ingested_case_count": len(cases),
        "batch_size": args.batch_size,
        "promotion_decision": promotion_decision,
        "gate": args.gate,
        "gate_result": gate_reason,
        "window": {
            key: effective_window.get(key)
            for key in (
                "decision_count",
                "operator_agreement_rate",
                "citation_coverage",
                "critical_disagreement_count",
                "policy_mismatch_count",
                "promotion_decision",
                "window_start",
                "window_end",
            )
            if isinstance(effective_window, dict)
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if gate_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

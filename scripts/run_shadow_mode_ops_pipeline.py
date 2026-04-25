#!/usr/bin/env python3
"""Validate, ingest, report, and preflight a local ops-api shadow window."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from push_shadow_cases_to_ops_api import _chunks, _evaluate_gate, _fetch_window, _post_capture
from validate_shadow_cases import load_case_files, load_existing_request_ids, validate_case_rows


REPO_ROOT = Path(__file__).resolve().parents[1]


def _default_output_prefix() -> Path:
    yyyymmdd = datetime.now(UTC).strftime("%Y%m%d")
    return Path(f"artifacts/reports/shadow_mode_ops_api_real_window_{yyyymmdd}")


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--cases-file", action="append", required=True)
    parser.add_argument("--real-case", action="store_true", help="Apply real ops shadow-case rules.")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--gate", choices=("rollback", "hold", "promote"), default="hold")
    parser.add_argument("--reset", action="store_true", help="Rotate the audit log before the first batch.")
    parser.add_argument(
        "--audit-log",
        default="artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl",
        help="Local shadow audit JSONL path used by the ops-api stack.",
    )
    parser.add_argument("--output-prefix", default=None)
    parser.add_argument("--candidate-manifest", action="append", default=[])
    parser.add_argument("--preflight-output-prefix", default=None)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    case_paths = [Path(path) for path in args.cases_file]
    case_rows = load_case_files(case_paths)
    existing_ids = set()
    if args.real_case and not args.reset:
        existing_ids = load_existing_request_ids([Path(args.audit_log)])
    validation_errors = validate_case_rows(case_rows, real_case=args.real_case, existing_request_ids=existing_ids)
    if validation_errors:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "stage": "validate",
                    "case_rows": len(case_rows),
                    "validation_errors": validation_errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    cases = [row for _, _, row in case_rows]
    output_prefix = Path(args.output_prefix) if args.output_prefix else _default_output_prefix()
    preflight_output_prefix = (
        Path(args.preflight_output_prefix)
        if args.preflight_output_prefix
        else output_prefix.with_name(f"{output_prefix.name}_preflight")
    )

    if args.validate_only:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "stage": "validate",
                    "case_rows": len(cases),
                    "real_case": args.real_case,
                    "output_prefix": output_prefix.as_posix(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    first_batch = True
    for batch in _chunks(cases, args.batch_size):
        append = not (first_batch and args.reset)
        _post_capture(base_url=args.base_url, api_key=args.api_key, cases=batch, append=append)
        first_batch = False

    window = _fetch_window(base_url=args.base_url, api_key=args.api_key) or {}
    gate_pass, gate_reason = _evaluate_gate(args.gate, window.get("promotion_decision"))
    if not gate_pass:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "stage": "gate",
                    "gate": args.gate,
                    "gate_result": gate_reason,
                    "window": window,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 1

    _run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/build_shadow_mode_window_report.py"),
            "--audit-log",
            args.audit_log,
            "--output-prefix",
            output_prefix.as_posix(),
        ]
    )
    window_report_json = output_prefix.with_suffix(".json")

    preflight_json = None
    if args.candidate_manifest:
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts/build_challenger_submit_preflight.py"),
            "--real-shadow-report",
            window_report_json.as_posix(),
            "--output-prefix",
            preflight_output_prefix.as_posix(),
        ]
        for manifest in args.candidate_manifest:
            command.extend(["--candidate-manifest", manifest])
        _run(command)
        preflight_json = preflight_output_prefix.with_suffix(".json")

    print(
        json.dumps(
            {
                "status": "ok",
                "ingested_case_count": len(cases),
                "gate": args.gate,
                "gate_result": gate_reason,
                "window_report_json": window_report_json.as_posix(),
                "window_report_md": output_prefix.with_suffix(".md").as_posix(),
                "preflight_json": preflight_json.as_posix() if preflight_json else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

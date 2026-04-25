#!/usr/bin/env python3
"""Run the real shadow daily intake pipeline end to end.

This is the operator-facing daily wrapper around the lower-level scripts:

1. strict real-case validation
2. ops-api /shadow/cases/capture + window report
3. residual backlog validation/report
4. runtime gate blocker report
5. optional challenger submit preflight when candidate manifests are provided

It never uses SQLite. The ops-api server it talks to must be backed by the
PostgreSQL/TimescaleDB stack.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


class StepFailed(RuntimeError):
    def __init__(self, step: dict[str, Any]):
        super().__init__(f"{step['label']} failed with exit code {step['returncode']}")
        self.step = step


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _default_date() -> str:
    return datetime.now().strftime("%Y%m%d")


def _run_step(label: str, command: list[str], *, required: bool = True) -> dict[str, Any]:
    print(f"\n[{label}] {' '.join(command)}", flush=True)
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    step = {
        "label": label,
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
        "required": required,
    }
    if required and result.returncode != 0:
        raise StepFailed(step)
    return step


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_empty_residual_report(json_path: Path, md_path: Path, *, backlog_file: Path) -> None:
    payload = {
        "backlog_files": [],
        "validation_errors": [],
        "summary": {
            "generated_at": _now_iso(),
            "total_residual_count": 0,
            "open_residual_count": 0,
            "critical_residual_count": 0,
            "unverified_fix_count": 0,
            "counts_by_owner": {},
            "counts_by_status": {},
            "counts_by_severity": {},
            "counts_by_fix_type": {},
            "counts_by_failure_mode": {},
            "recent_open_items": [],
        },
        "skipped_reason": f"backlog file not found: {backlog_file}",
    }
    _write_json(json_path, payload)
    _write_text(
        md_path,
        "\n".join(
            [
                "# Shadow Residual Backlog Summary",
                "",
                f"- generated_at: `{payload['summary']['generated_at']}`",
                f"- skipped_reason: `{payload['skipped_reason']}`",
                "- total_residual_count: `0`",
                "- open_residual_count: `0`",
                "",
            ]
        ),
    )


def _render_daily_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Real Shadow Daily Intake",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- date: `{summary['date']}`",
        f"- status: `{summary['status']}`",
        f"- base_url: `{summary['base_url']}`",
        f"- cases_files: `{summary['cases_files']}`",
        f"- backlog_file: `{summary['backlog_file']}`",
        "",
        "## Outputs",
        "",
    ]
    for key, value in summary["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Steps", ""])
    for step in summary["steps"]:
        lines.append(f"- `{step['label']}` returncode=`{step['returncode']}` required=`{step['required']}`")
    if summary.get("failed_step"):
        lines.extend(["", "## Failed Step", "", f"- `{summary['failed_step']}`"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=_default_date(), help="Operating date in YYYYMMDD.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--cases-file", action="append", default=[])
    parser.add_argument("--backlog-file", default=None)
    parser.add_argument("--audit-log", default="artifacts/runtime/llm_orchestrator/shadow_mode_audit.jsonl")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--gate", choices=("rollback", "hold", "promote"), default="rollback")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--candidate-manifest", action="append", default=[])
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--skip-runtime-gate-report", action="store_true")
    parser.add_argument("--reports-dir", default="artifacts/reports")
    parser.add_argument("--output-prefix", default=None)
    args = parser.parse_args()

    cases_files = [Path(path) for path in args.cases_file] or [Path(f"data/ops/shadow_mode_cases_{args.date}.jsonl")]
    backlog_file = Path(args.backlog_file) if args.backlog_file else Path(f"data/ops/shadow_residual_backlog_{args.date}.jsonl")
    reports_dir = Path(args.reports_dir)
    daily_prefix = Path(args.output_prefix) if args.output_prefix else reports_dir / f"real_shadow_daily_intake_{args.date}"
    window_prefix = reports_dir / f"shadow_mode_ops_api_real_window_{args.date}"
    preflight_prefix = reports_dir / f"challenger_submit_preflight_real_shadow_{args.date}"
    residual_json = reports_dir / f"shadow_residual_backlog_{args.date}.json"
    residual_md = reports_dir / f"shadow_residual_backlog_{args.date}.md"
    runtime_gate_json = reports_dir / f"runtime_gate_blockers_{args.date}.json"
    runtime_gate_md = reports_dir / f"runtime_gate_blockers_{args.date}.md"

    outputs = {
        "daily_json": daily_prefix.with_suffix(".json").as_posix(),
        "daily_md": daily_prefix.with_suffix(".md").as_posix(),
        "window_json": window_prefix.with_suffix(".json").as_posix(),
        "window_md": window_prefix.with_suffix(".md").as_posix(),
        "residual_json": residual_json.as_posix(),
        "residual_md": residual_md.as_posix(),
        "runtime_gate_json": runtime_gate_json.as_posix() if not args.skip_runtime_gate_report else None,
        "runtime_gate_md": runtime_gate_md.as_posix() if not args.skip_runtime_gate_report else None,
        "preflight_json": preflight_prefix.with_suffix(".json").as_posix() if args.candidate_manifest else None,
        "preflight_md": preflight_prefix.with_suffix(".md").as_posix() if args.candidate_manifest else None,
    }
    steps: list[dict[str, Any]] = []
    status = "ok"
    failed_step = None

    try:
        validate_cmd = [
            sys.executable,
            "scripts/validate_shadow_cases.py",
            "--real-case",
            "--expected-date",
            args.date,
            "--existing-audit-log",
            args.audit_log,
        ]
        for cases_file in cases_files:
            validate_cmd.extend(["--cases-file", cases_file.as_posix()])
        steps.append(_run_step("validate_real_shadow_cases", validate_cmd))

        pipeline_cmd = [
            sys.executable,
            "scripts/run_shadow_mode_ops_pipeline.py",
            "--base-url",
            args.base_url,
            "--real-case",
            "--expected-date",
            args.date,
            "--batch-size",
            str(args.batch_size),
            "--gate",
            args.gate,
            "--audit-log",
            args.audit_log,
            "--output-prefix",
            window_prefix.as_posix(),
            "--preflight-output-prefix",
            preflight_prefix.as_posix(),
        ]
        if args.api_key:
            pipeline_cmd.extend(["--api-key", args.api_key])
        if args.reset:
            pipeline_cmd.append("--reset")
        if args.validate_only:
            pipeline_cmd.append("--validate-only")
        for cases_file in cases_files:
            pipeline_cmd.extend(["--cases-file", cases_file.as_posix()])
        for manifest in args.candidate_manifest:
            pipeline_cmd.extend(["--candidate-manifest", manifest])
        steps.append(_run_step("ops_api_shadow_pipeline", pipeline_cmd))

        if backlog_file.exists():
            residual_validate_cmd = [
                sys.executable,
                "scripts/validate_shadow_residual_backlog.py",
                "--backlog-file",
                backlog_file.as_posix(),
            ]
            for cases_file in cases_files:
                residual_validate_cmd.extend(["--source-cases-file", cases_file.as_posix()])
            steps.append(_run_step("validate_residual_backlog", residual_validate_cmd))
            steps.append(
                _run_step(
                    "report_residual_backlog",
                    [
                        sys.executable,
                        "scripts/report_shadow_residual_backlog.py",
                        "--backlog-file",
                        backlog_file.as_posix(),
                        "--output-json",
                        residual_json.as_posix(),
                        "--output-md",
                        residual_md.as_posix(),
                    ],
                )
            )
        else:
            _write_empty_residual_report(residual_json, residual_md, backlog_file=backlog_file)
            steps.append(
                {
                    "label": "report_residual_backlog",
                    "command": ["write-empty-residual-report", backlog_file.as_posix()],
                    "returncode": 0,
                    "stdout_tail": "",
                    "stderr_tail": "",
                    "required": False,
                }
            )

        if not args.skip_runtime_gate_report and not args.validate_only:
            runtime_gate_cmd = [
                sys.executable,
                "scripts/report_runtime_gate_blockers.py",
                "--base-url",
                args.base_url,
                "--output-json",
                runtime_gate_json.as_posix(),
                "--output-md",
                runtime_gate_md.as_posix(),
            ]
            if args.api_key:
                runtime_gate_cmd.extend(["--api-key", args.api_key])
            steps.append(_run_step("report_runtime_gate_blockers", runtime_gate_cmd))
    except StepFailed as exc:
        steps.append(exc.step)
        status = "failed"
        failed_step = str(exc)
    except Exception as exc:
        status = "failed"
        failed_step = str(exc)

    summary = {
        "generated_at": _now_iso(),
        "date": args.date,
        "status": status,
        "failed_step": failed_step,
        "base_url": args.base_url,
        "cases_files": [path.as_posix() for path in cases_files],
        "backlog_file": backlog_file.as_posix(),
        "validate_only": args.validate_only,
        "outputs": outputs,
        "steps": steps,
    }
    _write_json(daily_prefix.with_suffix(".json"), summary)
    _write_text(daily_prefix.with_suffix(".md"), _render_daily_markdown(summary))
    print(json.dumps({"status": status, "daily_json": outputs["daily_json"], "failed_step": failed_step}, ensure_ascii=False, indent=2))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

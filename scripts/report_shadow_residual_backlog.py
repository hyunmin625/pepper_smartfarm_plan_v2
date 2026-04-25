#!/usr/bin/env python3
"""Build summary reports for real shadow residual backlog JSONL files."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_shadow_residual_backlog import load_backlog_files, load_schema, validate_rows


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BACKLOG_GLOB = "data/ops/shadow_residual_backlog_*.jsonl"
OPEN_STATUSES = {"new", "triaged", "queued", "fixed"}


def discover_backlog_files(*, include_template: bool = False) -> list[Path]:
    paths = sorted(REPO_ROOT.glob(DEFAULT_BACKLOG_GLOB))
    if not include_template:
        paths = [path for path in paths if "template" not in path.name]
    return paths


def _parse_dt(value: Any) -> datetime:
    if not isinstance(value, str) or not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def summarize(rows: list[tuple[Path, int, dict[str, Any]]]) -> dict[str, Any]:
    items = [row for _, _, row in rows]
    open_items = [row for row in items if row.get("status") in OPEN_STATUSES]
    owner_counts = Counter(str(row.get("owner") or "unknown") for row in items)
    status_counts = Counter(str(row.get("status") or "unknown") for row in items)
    severity_counts = Counter(str(row.get("severity") or "unknown") for row in items)
    fix_type_counts = Counter(str((row.get("expected_fix") or {}).get("fix_type") or "unknown") for row in items)
    failure_mode_counts: Counter[str] = Counter()
    for row in items:
        for failure_mode in row.get("failure_modes") or []:
            failure_mode_counts[str(failure_mode)] += 1

    recent_open = sorted(
        open_items,
        key=lambda row: _parse_dt(row.get("updated_at") or row.get("created_at")),
        reverse=True,
    )[:12]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "total_residual_count": len(items),
        "open_residual_count": len(open_items),
        "critical_residual_count": sum(1 for row in open_items if row.get("severity") == "critical"),
        "unverified_fix_count": sum(1 for row in open_items if row.get("status") == "fixed"),
        "counts_by_owner": dict(sorted(owner_counts.items())),
        "counts_by_status": dict(sorted(status_counts.items())),
        "counts_by_severity": dict(sorted(severity_counts.items())),
        "counts_by_fix_type": dict(sorted(fix_type_counts.items())),
        "counts_by_failure_mode": dict(failure_mode_counts.most_common()),
        "recent_open_items": [
            {
                "residual_id": row.get("residual_id"),
                "source_case_request_id": row.get("source_case_request_id"),
                "owner": row.get("owner"),
                "severity": row.get("severity"),
                "status": row.get("status"),
                "failure_modes": row.get("failure_modes") or [],
                "expected_fix": row.get("expected_fix") or {},
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
            }
            for row in recent_open
        ],
    }


def _table(title: str, counts: dict[str, int]) -> str:
    if not counts:
        return f"## {title}\n\n없음\n"
    lines = [f"## {title}", "", "| key | count |", "| --- | ---: |"]
    for key, count in counts.items():
        lines.append(f"| {key} | {count} |")
    return "\n".join(lines) + "\n"


def render_markdown(summary: dict[str, Any], *, backlog_files: list[Path], validation_errors: list[str]) -> str:
    lines = [
        "# Shadow Residual Backlog Summary",
        "",
        f"- generated_at: `{summary['generated_at']}`",
        f"- backlog_files: `{len(backlog_files)}`",
        f"- total_residual_count: `{summary['total_residual_count']}`",
        f"- open_residual_count: `{summary['open_residual_count']}`",
        f"- critical_residual_count: `{summary['critical_residual_count']}`",
        f"- unverified_fix_count: `{summary['unverified_fix_count']}`",
        f"- validation_errors: `{len(validation_errors)}`",
        "",
    ]
    if backlog_files:
        lines.extend(["## Files", ""])
        lines.extend(f"- `{path}`" for path in backlog_files)
        lines.append("")
    if validation_errors:
        lines.extend(["## Validation Errors", ""])
        lines.extend(f"- {err}" for err in validation_errors)
        lines.append("")
    lines.append(_table("By Owner", summary["counts_by_owner"]))
    lines.append(_table("By Status", summary["counts_by_status"]))
    lines.append(_table("By Severity", summary["counts_by_severity"]))
    lines.append(_table("By Fix Type", summary["counts_by_fix_type"]))
    lines.append(_table("By Failure Mode", summary["counts_by_failure_mode"]))

    lines.extend(["## Recent Open Items", ""])
    if not summary["recent_open_items"]:
        lines.append("없음")
    else:
        lines.extend(["| residual_id | owner | severity | status | failure_modes | fix_type |", "| --- | --- | --- | --- | --- | --- |"])
        for item in summary["recent_open_items"]:
            fix = item.get("expected_fix") or {}
            failure_modes = ", ".join(item.get("failure_modes") or [])
            lines.append(
                f"| {item.get('residual_id')} | {item.get('owner')} | {item.get('severity')} | "
                f"{item.get('status')} | {failure_modes} | {fix.get('fix_type')} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backlog-file", action="append", default=[])
    parser.add_argument("--include-template", action="store_true")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-md", default="")
    parser.add_argument("--allow-validation-errors", action="store_true")
    args = parser.parse_args()

    backlog_files = [Path(path) for path in args.backlog_file] if args.backlog_file else discover_backlog_files(
        include_template=args.include_template
    )
    rows = load_backlog_files(backlog_files) if backlog_files else []
    schema = load_schema()
    validation_errors = validate_rows(rows, schema=schema) if rows else []
    summary = summarize(rows)
    payload = {
        "backlog_files": [str(path) for path in backlog_files],
        "validation_errors": validation_errors,
        "summary": summary,
    }
    text_json = json.dumps(payload, ensure_ascii=False, indent=2)
    text_md = render_markdown(summary, backlog_files=backlog_files, validation_errors=validation_errors)

    if args.output_json:
        output = Path(args.output_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text_json + "\n", encoding="utf-8")
    else:
        print(text_json)
    if args.output_md:
        output = Path(args.output_md)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text_md, encoding="utf-8")

    return 1 if validation_errors and not args.allow_validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

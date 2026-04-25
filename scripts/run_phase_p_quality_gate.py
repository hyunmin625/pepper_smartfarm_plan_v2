#!/usr/bin/env python3
"""Run the Phase P zero-cost quality gate.

This runner intentionally keeps PostgreSQL checks PostgreSQL-only. It loads
.env by default so OPS_API_DATABASE_URL is available when configured, but the
runtime review smoke still skips cleanly if no PostgreSQL URL exists.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"


def load_dotenv(path: Path, env: dict[str, str]) -> dict[str, str]:
    if not path.exists():
        return env
    loaded = dict(env)
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in loaded:
                loaded[key] = value
    return loaded


def python_for_runtime() -> str:
    return str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))


def run_step(label: str, cmd: list[str], *, env: dict[str, str]) -> None:
    print(f"\n[{label}] {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, cwd=REPO_ROOT, env=env, text=True)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-postgres-smoke", action="store_true")
    parser.add_argument("--no-env", action="store_true", help="Do not load .env before subprocesses.")
    parser.add_argument("--rehearsal-date", default=datetime.now().strftime("%Y%m%d"))
    args = parser.parse_args()

    env = dict(os.environ)
    if not args.no_env:
        env = load_dotenv(REPO_ROOT / ".env", env)

    runtime_python = python_for_runtime()
    with tempfile.TemporaryDirectory(prefix="phase-p-quality-") as tmp:
        tmp_root = Path(tmp)
        rehearsal_file = tmp_root / f"shadow_mode_rehearsal_{args.rehearsal_date}.jsonl"
        report_json = tmp_root / "shadow_residual_backlog_summary.json"
        report_md = tmp_root / "shadow_residual_backlog_summary.md"

        run_step(
            "py_compile",
            [
                sys.executable,
                "-m",
                "py_compile",
                "ops-api/ops_api/app.py",
                "scripts/generate_shadow_ops_rehearsal_day.py",
                "scripts/validate_shadow_cases.py",
                "scripts/validate_shadow_residual_backlog.py",
                "scripts/report_shadow_residual_backlog.py",
                "scripts/run_phase_p_quality_gate.py",
            ],
            env=env,
        )
        run_step(
            "dashboard_hooks",
            [
                runtime_python,
                "-c",
                (
                    "import sys; "
                    "sys.path[:0]=['ops-api','llm-orchestrator','policy-engine','state-estimator','execution-gateway']; "
                    "from ops_api.app import _dashboard_html; "
                    "h=_dashboard_html(); "
                    "hooks=['runtimeGateCard','renderRuntimeGateCard','shadowResidualSummary','renderShadowResiduals',"
                    "'policyEventQueueList','renderPolicyEventQueues','policyChangeList','renderPolicyChanges',"
                    "'automationReviewSummary','renderAutomationReviewSummary']; "
                    "missing=[x for x in hooks if x not in h]; "
                    "print({'missing': missing, 'html_len': len(h)}); "
                    "raise SystemExit(1 if missing else 0)"
                ),
            ],
            env=env,
        )
        run_step(
            "generate_rehearsal",
            [
                sys.executable,
                "scripts/generate_shadow_ops_rehearsal_day.py",
                "--date",
                args.rehearsal_date,
                "--count",
                "12",
                "--output",
                str(rehearsal_file),
            ],
            env=env,
        )
        run_step(
            "validate_rehearsal",
            [sys.executable, "scripts/validate_shadow_cases.py", "--cases-file", str(rehearsal_file)],
            env=env,
        )
        run_step(
            "pipeline_validate_only",
            [
                sys.executable,
                "scripts/run_shadow_mode_ops_pipeline.py",
                "--cases-file",
                str(rehearsal_file),
                "--validate-only",
            ],
            env=env,
        )
        run_step(
            "validate_backlog_template",
            [
                sys.executable,
                "scripts/validate_shadow_residual_backlog.py",
                "--backlog-file",
                "data/ops/shadow_residual_backlog_template.jsonl",
                "--source-cases-file",
                "data/ops/shadow_mode_cases_template.jsonl",
            ],
            env=env,
        )
        run_step(
            "report_backlog_template",
            [
                sys.executable,
                "scripts/report_shadow_residual_backlog.py",
                "--backlog-file",
                "data/ops/shadow_residual_backlog_template.jsonl",
                "--output-json",
                str(report_json),
                "--output-md",
                str(report_md),
            ],
            env=env,
        )
        if not args.skip_postgres_smoke:
            run_step(
                "postgres_runtime_review_smoke",
                [runtime_python, "scripts/validate_ops_api_runtime_review_surfaces.py"],
                env=env,
            )
        run_step("diff_check", ["git", "diff", "--check"], env=env)

    print("\nPhase P quality gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

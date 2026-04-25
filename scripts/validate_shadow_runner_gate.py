#!/usr/bin/env python3
"""Validate push_shadow_cases_to_ops_api gate semantics in-process.

Spinning a real uvicorn server with a free port is brittle in CI, so
this smoke exercises the runner's gate logic and its HTTP call shape
directly against a TestClient-wrapped ops-api app. We monkey-patch
``urllib.request.urlopen`` to route HTTP calls into the TestClient so
the runner's production code path (POST /shadow/cases/capture + GET
/shadow/window) is exercised end-to-end without binding a socket.

This smoke is PostgreSQL-only. If no PostgreSQL URL is configured through
``OPS_API_POSTGRES_SMOKE_URL`` or ``OPS_API_DATABASE_URL``, it reports
``blocked`` and exits 0.

Scenarios:

1. Gate ``promote`` satisfied – ingest four healthy seed cases and
   verify the runner exits zero with ``promotion_decision=promote``.
2. Gate ``promote`` rejected – inject a synthetic mismatch case so
   the shadow window falls to ``hold``, then run the same gate and
   expect a non-zero exit with the hold reason surfaced.
3. Gate ``hold`` satisfied – using the same hold window, relax the
   gate to ``hold`` and verify the runner now exits zero.
"""

from __future__ import annotations

import copy
import io
import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))

from fastapi.testclient import TestClient  # noqa: E402

from ops_api.app import create_app  # noqa: E402
from ops_api.config import Settings  # noqa: E402


runner_module_path = REPO_ROOT / "scripts" / "push_shadow_cases_to_ops_api.py"
runner_ns: dict[str, Any] = {"__name__": "push_shadow_cases_to_ops_api"}
exec(compile(runner_module_path.read_text(encoding="utf-8"), str(runner_module_path), "exec"), runner_ns)


def _resolve_postgres_url() -> str | None:
    for name in ("OPS_API_POSTGRES_SMOKE_URL", "OPS_API_DATABASE_URL"):
        value = os.getenv(name, "").strip()
        if value.startswith("postgresql://") or value.startswith("postgresql+"):
            return value
    return None


def _make_settings(tmp_path: Path, postgres_url: str) -> Settings:
    return Settings(
        database_url=postgres_url,
        runtime_mode_path=tmp_path / "runtime_mode.json",
        auth_mode="disabled",
        auth_tokens_json="",
        shadow_audit_log_path=tmp_path / "shadow.jsonl",
        validator_audit_log_path=tmp_path / "validator.jsonl",
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=5.0,
        llm_max_retries=1,
    )


class _TestClientResponse:
    """Wrap httpx Response as the minimal urllib urlopen contract."""

    def __init__(self, response) -> None:
        self._response = response
        self.fp = io.BytesIO(response.content)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._response.content


def _install_urlopen_shim(client: TestClient):
    def _fake_urlopen(request, *args, **kwargs):
        method = request.get_method()
        url = request.full_url
        path = url.split("://", 1)[-1].split("/", 1)[-1]
        if not path.startswith("/"):
            path = "/" + path
        headers = {key.lower(): value for key, value in request.headers.items()}
        body = request.data
        if method == "POST":
            resp = client.post(path, content=body, headers=headers)
        else:
            resp = client.get(path, headers=headers)
        if resp.status_code >= 400:
            raise urllib.error.HTTPError(
                url=url,
                code=resp.status_code,
                msg=resp.reason_phrase,
                hdrs=None,
                fp=io.BytesIO(resp.content),
            )
        return _TestClientResponse(resp)

    urllib.request.urlopen = _fake_urlopen


def _invoke_runner(argv: list[str]) -> int:
    original_argv = sys.argv[:]
    original_stdout = sys.stdout
    sys.argv = ["push_shadow_cases_to_ops_api.py", *argv]
    sys.stdout = io.StringIO()
    try:
        try:
            return runner_ns["main"]()
        except SystemExit as exc:
            return int(exc.code or 0)
    finally:
        sys.argv = original_argv
        sys.stdout = original_stdout


def _write_cases(path: Path, cases: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=False))
            handle.write("\n")


def _load_seed_cases() -> list[dict[str, Any]]:
    path = REPO_ROOT / "data/examples/shadow_mode_runtime_day0_seed_cases.jsonl"
    cases: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def _make_hold_case(template: dict[str, Any]) -> dict[str, Any]:
    hold_case = copy.deepcopy(template)
    hold_case["request_id"] = f"{template['request_id']}-hold-shadow"
    observed = hold_case.setdefault("observed", {})
    observed["operator_agreement"] = False
    observed["critical_disagreement"] = False
    observed["operator_action_types"] = ["inspect_crop"]
    observed["operator_robot_task_types"] = []
    return hold_case


def main() -> int:
    errors: list[str] = []
    for key in ("OPS_API_AUTH_MODE", "OPS_API_AUTH_TOKENS_JSON"):
        os.environ.pop(key, None)

    postgres_url = _resolve_postgres_url()
    if not postgres_url:
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "postgres URL is not configured",
                    "expected_env": ["OPS_API_POSTGRES_SMOKE_URL", "OPS_API_DATABASE_URL"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    seed_cases = _load_seed_cases()
    if len(seed_cases) < 4:
        errors.append("seed case pool must contain at least 4 cases for the gate smoke")
        print(json.dumps({"errors": errors}))
        return 1

    report: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="shadow-runner-gate-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        happy_file = tmp_path / "happy_cases.jsonl"
        hold_file = tmp_path / "hold_case.jsonl"
        _write_cases(happy_file, seed_cases[:4])
        _write_cases(hold_file, [_make_hold_case(seed_cases[0])])

        app = create_app(settings=_make_settings(tmp_path, postgres_url))
        client = TestClient(app)
        _install_urlopen_shim(client)

        # Scenario 1: gate promote satisfied
        exit_code = _invoke_runner(
            [
                "--base-url",
                "http://ops-api.test",
                "--cases-file",
                str(happy_file),
                "--gate",
                "promote",
                "--batch-size",
                "2",
            ]
        )
        if exit_code != 0:
            errors.append(f"happy-path gate promote should exit 0, got {exit_code}")
        window_resp = client.get("/shadow/window")
        if window_resp.status_code != 200:
            errors.append(f"shadow window should be populated after ingestion, got {window_resp.status_code}")
        else:
            happy_window = window_resp.json().get("data") or {}
            report["happy_window"] = {
                "promotion_decision": happy_window.get("promotion_decision"),
                "operator_agreement_rate": happy_window.get("operator_agreement_rate"),
                "decision_count": happy_window.get("decision_count"),
            }
            if happy_window.get("promotion_decision") != "promote":
                errors.append(
                    f"happy window should be promote, got {happy_window.get('promotion_decision')}"
                )

        # Scenario 2: gate promote rejected after mismatch injection
        # Append the hold case; the runner will POST it with append=True and
        # the rolling window will slip below the promote threshold.
        exit_code = _invoke_runner(
            [
                "--base-url",
                "http://ops-api.test",
                "--cases-file",
                str(hold_file),
                "--gate",
                "promote",
                "--append",
            ]
        )
        if exit_code == 0:
            errors.append("mismatch ingestion should fail the promote gate")
        degraded_resp = client.get("/shadow/window")
        degraded_window = degraded_resp.json().get("data") or {}
        report["degraded_window"] = {
            "promotion_decision": degraded_window.get("promotion_decision"),
            "operator_agreement_rate": degraded_window.get("operator_agreement_rate"),
            "decision_count": degraded_window.get("decision_count"),
        }
        if degraded_window.get("promotion_decision") not in {"hold", "rollback"}:
            errors.append(
                f"mismatch window should be hold or rollback, got {degraded_window.get('promotion_decision')}"
            )

        # Scenario 3: relaxed gate hold now passes against the same window
        exit_code = _invoke_runner(
            [
                "--base-url",
                "http://ops-api.test",
                "--cases-file",
                str(hold_file),  # any cases; the runner posts then re-checks
                "--gate",
                "hold",
                "--append",
            ]
        )
        if exit_code != 0:
            errors.append(
                f"relaxed hold gate should accept the degraded window, got exit {exit_code}"
            )

    report["errors"] = errors
    report["status"] = "ok" if not errors else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a real localhost server smoke against ops-api."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]


def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        return int(sock.getsockname()[1])


def _request_json(url: str, *, method: str = "GET", payload: dict | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, method=method)
    request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raw = exc.read().decode("utf-8")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {"raw": raw}
        return exc.code, body


def main() -> int:
    errors: list[str] = []
    server_log_tail: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ops-api-server-smoke-") as tmp_dir:
        db_path = Path(tmp_dir) / "ops_api_server.db"
        runtime_mode_path = Path(tmp_dir) / "runtime_mode.json"
        server_log = Path(tmp_dir) / "uvicorn.log"
        port = _reserve_port()
        env = os.environ.copy()
        pythonpath_entries = [
            str(REPO_ROOT / "ops-api"),
            str(REPO_ROOT / "state-estimator"),
            str(REPO_ROOT / "llm-orchestrator"),
            str(REPO_ROOT / "execution-gateway"),
            str(REPO_ROOT / "policy-engine"),
        ]
        existing_pythonpath = env.get("PYTHONPATH", "")
        if existing_pythonpath:
            pythonpath_entries.append(existing_pythonpath)
        env.update(
            {
                "PYTHONPATH": os.pathsep.join(pythonpath_entries),
                "OPS_API_DATABASE_URL": f"sqlite:///{db_path}",
                "OPS_API_RUNTIME_MODE_PATH": str(runtime_mode_path),
                "OPS_API_LLM_PROVIDER": "stub",
                "OPS_API_MODEL_ID": "pepper-ops-local-stub",
                "OPS_API_AUTH_MODE": "disabled",
            }
        )

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "ops_api.app:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",
            ],
            cwd=str(REPO_ROOT),
            env=env,
            stdout=server_log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
        )
        try:
            base_url = f"http://127.0.0.1:{port}"
            health = None
            for _ in range(30):
                try:
                    status, body = _request_json(f"{base_url}/health")
                    if status == 200:
                        health = body
                        break
                except URLError:
                    time.sleep(0.25)
            observations: dict[str, object] = {}
            if health is None:
                errors.append("server did not become healthy within timeout")
            else:
                if health.get("data", {}).get("status") != "ok":
                    errors.append("health endpoint did not return ok envelope")

                _, auth_me = _request_json(
                    f"{base_url}/auth/me",
                    headers={"X-Actor-Id": "server-smoke", "X-Actor-Role": "operator"},
                )
                observations["auth_me"] = auth_me
                if auth_me.get("actor", {}).get("actor_id") != "server-smoke":
                    errors.append("auth/me did not echo actor envelope")
                if auth_me.get("actor", {}).get("role") != "operator":
                    errors.append("auth/me did not resolve operator role")

                _, runtime_before = _request_json(f"{base_url}/runtime/mode")
                observations["runtime_before"] = runtime_before
                if runtime_before.get("data", {}).get("mode") != "shadow":
                    errors.append("runtime mode should start in shadow")

                _, runtime_after = _request_json(
                    f"{base_url}/runtime/mode",
                    method="POST",
                    payload={"mode": "approval", "actor_id": "server-smoke", "reason": "server smoke"},
                )
                observations["runtime_after"] = runtime_after
                if runtime_after.get("data", {}).get("runtime_mode", {}).get("mode") != "approval":
                    errors.append("runtime mode toggle to approval failed")

                _, policies_before = _request_json(
                    f"{base_url}/policies",
                    headers={"X-Actor-Id": "admin-01", "X-Actor-Role": "admin"},
                )
                observations["policies_before"] = policies_before
                policy_items = policies_before.get("data", {}).get("items", [])
                if not policy_items:
                    errors.append("policies endpoint returned no seeded rows")
                policy_id = policy_items[0]["policy_id"] if policy_items else None

                if isinstance(policy_id, str):
                    _, policy_update = _request_json(
                        f"{base_url}/policies/{policy_id}",
                        method="POST",
                        payload={"enabled": False},
                        headers={"X-Actor-Id": "admin-01", "X-Actor-Role": "admin"},
                    )
                    observations["policy_update"] = policy_update
                    updated_enabled = policy_update.get("data", {}).get("policy", {}).get("enabled")
                    if updated_enabled is not False:
                        errors.append("policy update did not disable policy")

                decision_status, decision = _request_json(
                    f"{base_url}/decisions/evaluate-zone",
                    method="POST",
                    payload={
                        "request_id": "server-smoke-001",
                        "zone_id": "gh-01-zone-a",
                        "task_type": "action_recommendation",
                        "growth_stage": "fruiting",
                        "current_state": {
                            "air_temp_c": 30.4,
                            "rh_pct": 82.0,
                            "substrate_moisture_pct": 26.0,
                            "ripe_fruit_count": 41,
                        },
                        "sensor_quality": {"overall": "good"},
                    },
                    headers={"X-Actor-Id": "ops-service", "X-Actor-Role": "service"},
                )
                observations["decision_response"] = {"status": decision_status, "body": decision}
                decision_id = decision.get("data", {}).get("decision_id")
                if not isinstance(decision_id, int):
                    errors.append("evaluate-zone did not return decision_id envelope")

                if isinstance(decision_id, int):
                    _, approve = _request_json(
                        f"{base_url}/actions/approve",
                        method="POST",
                        payload={"decision_id": decision_id, "actor_id": "ignored", "reason": "server smoke approve"},
                        headers={"X-Actor-Id": "operator-01", "X-Actor-Role": "operator"},
                    )
                    observations["approve_response"] = approve
                    if approve.get("data", {}).get("approval_status") != "approved":
                        errors.append("approve endpoint did not return approved envelope")

                    _, dashboard = _request_json(f"{base_url}/dashboard/data")
                    observations["dashboard_response"] = dashboard
                    summary = dashboard.get("data", {}).get("summary", {})
                    if summary.get("decision_count", 0) < 1:
                        errors.append("dashboard summary missing decisions")
                    if summary.get("command_count", 0) < 1:
                        errors.append("dashboard summary missing commands")
                    if summary.get("policy_count", 0) < 1:
                        errors.append("dashboard summary missing policy count")
                    if dashboard.get("actor", {}).get("role") != "admin":
                        errors.append("dashboard actor envelope missing admin role")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            if server_log.exists():
                server_log_tail = server_log.read_text(encoding="utf-8").splitlines()[-20:]

    print(
        json.dumps(
            {
                "errors": errors,
                "observations": observations if "observations" in locals() else {},
                "log_tail": server_log_tail,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

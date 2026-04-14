#!/usr/bin/env python3
"""Validate ops-api auth/role configuration without ASGI client."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))
sys.path.insert(0, str(REPO_ROOT / "llm-orchestrator"))
sys.path.insert(0, str(REPO_ROOT / "policy-engine"))
sys.path.insert(0, str(REPO_ROOT / "state-estimator"))
sys.path.insert(0, str(REPO_ROOT / "execution-gateway"))

from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from ops_api.app import create_app  # noqa: E402
from ops_api.auth import ROLE_PERMISSIONS, get_authenticated_actor, require_permission  # noqa: E402
from ops_api.config import Settings  # noqa: E402


def _settings(*, auth_mode: str, auth_tokens_json: str = "") -> Settings:
    return Settings(
        database_url="sqlite://",
        runtime_mode_path=Path("/tmp/ops-api-runtime-mode.json"),
        auth_mode=auth_mode,
        auth_tokens_json=auth_tokens_json,
        shadow_audit_log_path=Path("/tmp/ops-api-shadow-audit.jsonl"),
        validator_audit_log_path=Path("/tmp/ops-api-validator-audit.jsonl"),
        llm_provider="stub",
        llm_model_id="pepper-ops-local-stub",
        llm_prompt_version="sft_v10",
        llm_timeout_seconds=30.0,
        llm_max_retries=3,
    )


def main() -> int:
    errors: list[str] = []

    disabled_actor = get_authenticated_actor(
        x_api_key=None,
        x_actor_id="local-user",
        x_actor_role="operator",
        settings=_settings(auth_mode="disabled"),
    )
    if disabled_actor.actor_id != "local-user" or disabled_actor.role != "operator":
        errors.append("disabled auth should trust local headers")

    header_settings = _settings(
        auth_mode="header_token",
        auth_tokens_json=json.dumps(
            {
                "operator-secret": {"actor_id": "operator-01", "role": "operator"},
                "service-secret": {"actor_id": "ops-service", "role": "service"},
            }
        ),
    )
    operator_actor = get_authenticated_actor(
        x_api_key="operator-secret",
        x_actor_id=None,
        x_actor_role=None,
        settings=header_settings,
    )
    if operator_actor.actor_id != "operator-01" or operator_actor.role != "operator":
        errors.append("header token should resolve operator identity")

    try:
        get_authenticated_actor(
            x_api_key="missing-token",
            x_actor_id=None,
            x_actor_role=None,
            settings=header_settings,
        )
        errors.append("invalid token should fail")
    except HTTPException as exc:
        if exc.status_code != 401:
            errors.append(f"invalid token returned wrong status {exc.status_code}")

    if "approve_actions" not in ROLE_PERMISSIONS["operator"]:
        errors.append("operator role missing approve_actions permission")
    if "manage_runtime_mode" in ROLE_PERMISSIONS["service"]:
        errors.append("service role should not manage runtime mode")

    if require_permission("execute_actions")(operator_actor).role != "operator":
        errors.append("operator should satisfy execute_actions permission")

    try:
        require_permission("manage_runtime_mode")(operator_actor)
        errors.append("operator should not satisfy manage_runtime_mode")
    except HTTPException as exc:
        if exc.status_code != 403:
            errors.append(f"permission denial returned wrong status {exc.status_code}")

    di_checks = _verify_dependency_injection(errors)

    print(
        json.dumps(
            {
                "errors": errors,
                "checked_roles": sorted(ROLE_PERMISSIONS.keys()),
                "disabled_actor": disabled_actor.as_dict(),
                "operator_actor": operator_actor.as_dict(),
                "dependency_injection": di_checks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


def _verify_dependency_injection(errors: list[str]) -> dict[str, int]:
    """Ensure create_app(settings=...) propagates settings to the auth dependency.

    Historically get_authenticated_actor used ``Depends(load_settings)`` which
    re-read env vars regardless of the settings injected into create_app. Since
    the app now registers ``dependency_overrides[load_settings]``, an explicit
    header_token Settings should take effect without touching os.environ.
    """
    for key in ("OPS_API_AUTH_MODE", "OPS_API_AUTH_TOKENS_JSON"):
        if key in os.environ:
            errors.append(f"unexpected env var {key} present before DI check")
            return {}

    with tempfile.TemporaryDirectory(prefix="ops-api-auth-di-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        settings = Settings(
            database_url=f"sqlite:///{tmp_path}/ops_api.db",
            runtime_mode_path=tmp_path / "runtime_mode.json",
            auth_mode="header_token",
            auth_tokens_json="",
            shadow_audit_log_path=tmp_path / "shadow.jsonl",
            validator_audit_log_path=tmp_path / "validator.jsonl",
            llm_provider="stub",
            llm_model_id="pepper-ops-local-stub",
            llm_prompt_version="sft_v10",
            llm_timeout_seconds=5.0,
            llm_max_retries=1,
        )
        app = create_app(settings=settings)
        client = TestClient(app)

        status_map: dict[str, int] = {}
        no_key = client.get("/decisions")
        status_map["no_key"] = no_key.status_code
        if no_key.status_code != 401:
            errors.append(
                f"header_token mode should 401 without x-api-key, got {no_key.status_code}"
            )

        viewer = client.get("/decisions", headers={"x-api-key": "viewer-demo-token"})
        status_map["viewer"] = viewer.status_code
        if viewer.status_code != 200:
            errors.append(
                f"viewer token should access /decisions, got {viewer.status_code}"
            )

        invalid = client.get("/decisions", headers={"x-api-key": "bogus"})
        status_map["invalid_token"] = invalid.status_code
        if invalid.status_code != 401:
            errors.append(
                f"invalid token should 401, got {invalid.status_code}"
            )

        return status_map


if __name__ == "__main__":
    raise SystemExit(main())

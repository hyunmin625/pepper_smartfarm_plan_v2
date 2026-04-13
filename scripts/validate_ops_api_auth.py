#!/usr/bin/env python3
"""Validate ops-api auth/role configuration without ASGI client."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "ops-api"))

from fastapi import HTTPException  # noqa: E402
from ops_api.auth import ROLE_PERMISSIONS, get_authenticated_actor, require_permission  # noqa: E402
from ops_api.config import Settings  # noqa: E402


def _settings(*, auth_mode: str, auth_tokens_json: str = "") -> Settings:
    return Settings(
        database_url="sqlite://",
        runtime_mode_path=Path("/tmp/ops-api-runtime-mode.json"),
        auth_mode=auth_mode,
        auth_tokens_json=auth_tokens_json,
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

    print(
        json.dumps(
            {
                "errors": errors,
                "checked_roles": sorted(ROLE_PERMISSIONS.keys()),
                "disabled_actor": disabled_actor.as_dict(),
                "operator_actor": operator_actor.as_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

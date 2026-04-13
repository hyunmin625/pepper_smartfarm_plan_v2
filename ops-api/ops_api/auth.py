from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from fastapi import Depends, Header, HTTPException

from .config import Settings, load_settings


ROLE_PERMISSIONS = {
    "viewer": {
        "read_catalog",
        "read_runtime",
    },
    "operator": {
        "read_catalog",
        "read_runtime",
        "review_shadow",
        "approve_actions",
        "execute_actions",
        "write_robot_tasks",
    },
    "service": {
        "read_catalog",
        "read_runtime",
        "evaluate_zone",
    },
    "admin": {
        "read_catalog",
        "read_runtime",
        "review_shadow",
        "approve_actions",
        "execute_actions",
        "write_robot_tasks",
        "manage_runtime_mode",
        "manage_policies",
    },
}


DEFAULT_TOKEN_STORE = {
    "viewer-demo-token": {"actor_id": "viewer-demo", "role": "viewer"},
    "operator-demo-token": {"actor_id": "operator-demo", "role": "operator"},
    "service-demo-token": {"actor_id": "ops-service", "role": "service"},
    "admin-demo-token": {"actor_id": "admin-demo", "role": "admin"},
}


@dataclass(frozen=True)
class ActorIdentity:
    actor_id: str
    role: str
    auth_mode: str

    def as_dict(self) -> dict[str, str]:
        return {
            "actor_id": self.actor_id,
            "role": self.role,
            "auth_mode": self.auth_mode,
        }


def _resolve_token_store(settings: Settings) -> dict[str, dict[str, str]]:
    raw = settings.auth_tokens_json.strip()
    if not raw:
        return DEFAULT_TOKEN_STORE
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OPS_API_AUTH_TOKENS_JSON must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("OPS_API_AUTH_TOKENS_JSON must be a JSON object")
    token_store: dict[str, dict[str, str]] = {}
    for token, payload in parsed.items():
        if not isinstance(payload, dict):
            continue
        actor_id = str(payload.get("actor_id") or "").strip()
        role = str(payload.get("role") or "").strip()
        if actor_id and role:
            token_store[str(token)] = {"actor_id": actor_id, "role": role}
    return token_store or DEFAULT_TOKEN_STORE


def get_authenticated_actor(
    x_api_key: str | None = Header(default=None),
    x_actor_id: str | None = Header(default=None),
    x_actor_role: str | None = Header(default=None),
    settings: Settings = Depends(load_settings),
) -> ActorIdentity:
    if settings.auth_mode == "disabled":
        actor_id = (x_actor_id or "local-admin").strip()
        role = (x_actor_role or "admin").strip()
        if role not in ROLE_PERMISSIONS:
            role = "admin"
        return ActorIdentity(actor_id=actor_id, role=role, auth_mode="disabled")

    if settings.auth_mode != "header_token":
        raise HTTPException(status_code=500, detail="unsupported auth mode")

    if not x_api_key:
        raise HTTPException(status_code=401, detail="missing x-api-key")
    token_store = _resolve_token_store(settings)
    payload = token_store.get(x_api_key)
    if payload is None:
        raise HTTPException(status_code=401, detail="invalid api key")
    role = payload["role"]
    if role not in ROLE_PERMISSIONS:
        raise HTTPException(status_code=403, detail="unknown actor role")
    return ActorIdentity(actor_id=payload["actor_id"], role=role, auth_mode="header_token")


def require_permission(permission: str) -> Callable[[ActorIdentity], ActorIdentity]:
    def dependency(actor: ActorIdentity = Depends(get_authenticated_actor)) -> ActorIdentity:
        permissions = ROLE_PERMISSIONS.get(actor.role, set())
        if permission not in permissions:
            raise HTTPException(status_code=403, detail=f"permission denied: {permission}")
        return actor

    return dependency

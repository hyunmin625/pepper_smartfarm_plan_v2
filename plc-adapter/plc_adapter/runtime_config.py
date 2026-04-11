from __future__ import annotations

import os
from dataclasses import dataclass


def endpoint_env_var(controller_id: str) -> str:
    normalized = controller_id.upper().replace("-", "_")
    return f"PLC_ENDPOINT_{normalized}"


@dataclass
class RuntimeEndpointResolver:
    use_env_overrides: bool = True

    def resolve(self, *, controller_id: str, configured_endpoint: str) -> str:
        if not self.use_env_overrides:
            return configured_endpoint
        env_key = endpoint_env_var(controller_id)
        override = os.environ.get(env_key)
        if override:
            return override
        return configured_endpoint

    def describe(self, *, controller_id: str, configured_endpoint: str) -> dict[str, object]:
        env_key = endpoint_env_var(controller_id)
        resolved = self.resolve(
            controller_id=controller_id,
            configured_endpoint=configured_endpoint,
        )
        return {
            "env_key": env_key,
            "configured_endpoint": configured_endpoint,
            "resolved_endpoint": resolved,
            "override_active": resolved != configured_endpoint,
        }

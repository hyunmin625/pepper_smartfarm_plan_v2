from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeviceCommandRequest:
    request_id: str
    device_id: str
    action_type: str
    parameters: dict[str, Any]
    approval_required: bool
    approval_status: str
    policy_result: str
    operator_present: bool
    manual_override: bool
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "DeviceCommandRequest":
        approval_context = raw.get("approval_context", {})
        policy_snapshot = raw.get("policy_snapshot", {})
        operator_context = raw.get("operator_context", {})
        return cls(
            request_id=raw["request_id"],
            device_id=raw["device_id"],
            action_type=raw["action_type"],
            parameters=raw.get("parameters", {}),
            approval_required=bool(raw.get("approval_required")),
            approval_status=approval_context.get("approval_status", "not_required"),
            policy_result=policy_snapshot.get("policy_result", "pass"),
            operator_present=bool(operator_context.get("operator_present")),
            manual_override=bool(operator_context.get("manual_override")),
            raw=raw,
        )


@dataclass(frozen=True)
class ControlOverrideRequest:
    request_id: str
    scope_type: str
    scope_id: str
    override_type: str
    approval_required: bool
    approval_status: str
    actor_type: str
    policy_result: str
    operator_present: bool
    manual_override_active: bool
    estop_active: bool
    preconditions: dict[str, bool]
    raw: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ControlOverrideRequest":
        approval_context = raw.get("approval_context", {})
        policy_snapshot = raw.get("policy_snapshot", {})
        operator_context = raw.get("operator_context", {})
        preconditions = raw.get("preconditions", {})
        return cls(
            request_id=raw["request_id"],
            scope_type=raw["scope_type"],
            scope_id=raw["scope_id"],
            override_type=raw["override_type"],
            approval_required=bool(raw.get("approval_required")),
            approval_status=approval_context.get("approval_status", "not_required"),
            actor_type=raw.get("requested_by", {}).get("actor_type", ""),
            policy_result=policy_snapshot.get("policy_result", "pass"),
            operator_present=bool(operator_context.get("operator_present")),
            manual_override_active=bool(operator_context.get("manual_override_active")),
            estop_active=bool(operator_context.get("estop_active")),
            preconditions={
                key: bool(value)
                for key, value in preconditions.items()
            },
            raw=raw,
        )

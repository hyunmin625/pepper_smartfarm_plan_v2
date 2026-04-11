from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import ControlOverrideRequest, DeviceCommandRequest


@dataclass(frozen=True)
class NormalizedRequest:
    request_id: str
    request_kind: str
    target_scope: str
    target_id: str
    operation_name: str
    dedupe_key: str
    cooldown_key: str
    approval_required: bool
    approval_status: str
    policy_result: str
    raw: dict[str, Any]


def normalize_device_command(request: DeviceCommandRequest) -> NormalizedRequest:
    dedupe_key = f"device:{request.device_id}:{request.action_type}"
    zone_id = request.raw.get("zone_id", request.device_id)
    return NormalizedRequest(
        request_id=request.request_id,
        request_kind="device_command",
        target_scope="device",
        target_id=request.device_id,
        operation_name=request.action_type,
        dedupe_key=dedupe_key,
        cooldown_key=dedupe_key,
        approval_required=request.approval_required,
        approval_status=request.approval_status,
        policy_result=request.policy_result,
        raw={**request.raw, "normalized_zone_id": zone_id},
    )


def normalize_control_override(request: ControlOverrideRequest) -> NormalizedRequest:
    dedupe_key = f"override:{request.scope_type}:{request.scope_id}:{request.override_type}"
    return NormalizedRequest(
        request_id=request.request_id,
        request_kind="control_override",
        target_scope=request.scope_type,
        target_id=request.scope_id,
        operation_name=request.override_type,
        dedupe_key=dedupe_key,
        cooldown_key=dedupe_key,
        approval_required=request.approval_required,
        approval_status=request.approval_status,
        policy_result=request.policy_result,
        raw=request.raw,
    )

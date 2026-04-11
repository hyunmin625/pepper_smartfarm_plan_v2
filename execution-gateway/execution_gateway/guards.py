from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from plc_adapter.device_catalog import DeviceCatalog
from plc_adapter.device_profiles import DeviceProfileRegistry

from .contracts import ControlOverrideRequest, DeviceCommandRequest
from .normalizer import NormalizedRequest, normalize_control_override, normalize_device_command


@dataclass
class PreflightDecision:
    status: str
    allow_dispatch: bool
    reasons: list[str]
    dedupe_key: str
    cooldown_key: str


class DuplicateDetector:
    def __init__(self) -> None:
        self.seen_keys: set[str] = set()

    def is_duplicate(self, key: str) -> bool:
        return key in self.seen_keys

    def record(self, key: str) -> None:
        self.seen_keys.add(key)


class CooldownManager:
    def __init__(self, *, active_keys: set[str] | None = None) -> None:
        self.active_keys = set(active_keys or set())

    def is_active(self, key: str) -> bool:
        return key in self.active_keys

    def activate(self, key: str) -> None:
        self.active_keys.add(key)


def evaluate_device_command(
    request: DeviceCommandRequest,
    *,
    catalog: DeviceCatalog,
    registry: DeviceProfileRegistry,
    duplicates: DuplicateDetector,
    cooldowns: CooldownManager,
) -> tuple[NormalizedRequest, PreflightDecision]:
    normalized = normalize_device_command(request)
    reasons: list[str] = []

    device = catalog.get(request.device_id)
    profile = registry.get(device.profile_id)
    try:
        profile.validate_parameters(request.action_type, request.parameters)
    except ValueError as exc:
        reasons.append(f"range_validation_failed:{exc}")

    if request.manual_override and request.action_type != "pause_automation":
        reasons.append("manual_override_active")
    if request.policy_result == "blocked":
        reasons.append("policy_blocked")
    if duplicates.is_duplicate(normalized.dedupe_key):
        reasons.append("duplicate_request")
    if cooldowns.is_active(normalized.cooldown_key):
        reasons.append("cooldown_active")

    if request.approval_required or request.policy_result == "approval_required":
        if request.approval_status != "approved":
            reasons.append("approval_pending")

    status = "ready" if not reasons else "rejected"
    allow_dispatch = not reasons
    if allow_dispatch:
        duplicates.record(normalized.dedupe_key)
    return normalized, PreflightDecision(
        status=status,
        allow_dispatch=allow_dispatch,
        reasons=reasons,
        dedupe_key=normalized.dedupe_key,
        cooldown_key=normalized.cooldown_key,
    )


def evaluate_control_override(
    request: ControlOverrideRequest,
    *,
    duplicates: DuplicateDetector,
    cooldowns: CooldownManager,
) -> tuple[NormalizedRequest, PreflightDecision]:
    normalized = normalize_control_override(request)
    reasons: list[str] = []

    if request.policy_result == "blocked":
        reasons.append("policy_blocked")
    if duplicates.is_duplicate(normalized.dedupe_key):
        reasons.append("duplicate_request")
    if cooldowns.is_active(normalized.cooldown_key):
        reasons.append("cooldown_active")

    if request.override_type in {"manual_override_start", "manual_override_release"} and request.actor_type != "operator":
        reasons.append("operator_required")
    if request.override_type in {"emergency_stop_reset_request", "manual_override_release", "auto_mode_reentry_request"}:
        if request.approval_status != "approved":
            reasons.append("approval_pending")
    if request.override_type == "auto_mode_reentry_request":
        for key in ("state_sync_completed", "manual_override_cleared", "estop_cleared"):
            if not request.preconditions.get(key):
                reasons.append(f"missing_precondition:{key}")

    status = "ready" if not reasons else "rejected"
    allow_dispatch = not reasons
    if allow_dispatch:
        duplicates.record(normalized.dedupe_key)
    return normalized, PreflightDecision(
        status=status,
        allow_dispatch=allow_dispatch,
        reasons=reasons,
        dedupe_key=normalized.dedupe_key,
        cooldown_key=normalized.cooldown_key,
    )

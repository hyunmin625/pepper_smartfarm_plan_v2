from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from plc_adapter.device_catalog import DeviceCatalog
from plc_adapter.device_profiles import DeviceProfileRegistry
from policy_engine import evaluate_device_policy_precheck, evaluate_override_policy_precheck

from .contracts import ControlOverrideRequest, DeviceCommandRequest
from .normalizer import NormalizedRequest, normalize_control_override, normalize_device_command

SAFE_DEVICE_ACTIONS_UNDER_INTERLOCK = {"pause_automation"}
INTERLOCK_FLAG_REASON = {
    "worker_present": "hard_guard_worker_present",
    "manual_override_active": "hard_guard_manual_override_interlock",
    "manual_override": "hard_guard_manual_override_interlock",
    "safe_mode_active": "hard_guard_safe_mode_interlock",
    "safe_mode": "hard_guard_safe_mode_interlock",
    "estop_active": "hard_guard_estop_interlock",
    "estop": "hard_guard_estop_interlock",
    "sensor_quality_blocked": "hard_guard_sensor_quality_blocked",
}


@dataclass
class PreflightDecision:
    status: str
    allow_dispatch: bool
    reasons: list[str]
    dedupe_key: str
    cooldown_key: str
    policy_result: str = "pass"
    policy_ids: list[str] = field(default_factory=list)


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


def active_interlock_flags(request: DeviceCommandRequest) -> set[str]:
    flags: set[str] = set()

    if request.operator_present:
        flags.add("worker_present")
    if request.manual_override:
        flags.add("manual_override_active")

    raw = request.raw
    for field_name in ("active_interlocks", "active_constraints", "safety_interlocks"):
        value = raw.get(field_name)
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str) and item.strip():
                flags.add(item.strip())

    sensor_quality = raw.get("sensor_quality")
    if isinstance(sensor_quality, dict):
        overall = sensor_quality.get("overall")
        if overall == "bad" or sensor_quality.get("automation_gate") == "blocked":
            flags.add("sensor_quality_blocked")

    return flags


def evaluate_hard_safety_guards(
    request: DeviceCommandRequest,
    *,
    device: Any,
    profile: Any,
) -> list[str]:
    del device, profile  # reserved for future profile-specific guard extension
    if request.action_type in SAFE_DEVICE_ACTIONS_UNDER_INTERLOCK:
        return []

    reasons: list[str] = []
    for flag in sorted(active_interlock_flags(request)):
        reason = INTERLOCK_FLAG_REASON.get(flag)
        if reason and reason not in reasons:
            reasons.append(reason)
    return reasons


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
    policy_precheck = evaluate_device_policy_precheck(request.raw)

    device = catalog.get(request.device_id)
    profile = registry.get(device.profile_id)
    try:
        profile.validate_parameters(request.action_type, request.parameters)
    except ValueError as exc:
        reasons.append(f"range_validation_failed:{exc}")

    reasons.extend(
        evaluate_hard_safety_guards(
            request,
            device=device,
            profile=profile,
        )
    )

    if request.manual_override and request.action_type != "pause_automation":
        reasons.append("manual_override_active")
    reasons.extend(policy_precheck.reasons)
    resolved_policy_result = policy_precheck.policy_result
    if resolved_policy_result == "blocked":
        reasons.append("policy_blocked")
    if duplicates.is_duplicate(normalized.dedupe_key):
        reasons.append("duplicate_request")
    if cooldowns.is_active(normalized.cooldown_key):
        reasons.append("cooldown_active")

    if request.approval_required or resolved_policy_result == "approval_required":
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
        policy_result=resolved_policy_result,
        policy_ids=policy_precheck.policy_ids,
    )


def evaluate_control_override(
    request: ControlOverrideRequest,
    *,
    duplicates: DuplicateDetector,
    cooldowns: CooldownManager,
) -> tuple[NormalizedRequest, PreflightDecision]:
    normalized = normalize_control_override(request)
    reasons: list[str] = []
    policy_precheck = evaluate_override_policy_precheck(request.raw)

    reasons.extend(policy_precheck.reasons)
    resolved_policy_result = policy_precheck.policy_result
    if resolved_policy_result == "blocked":
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
        policy_result=resolved_policy_result,
        policy_ids=policy_precheck.policy_ids,
    )

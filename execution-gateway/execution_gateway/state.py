from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .contracts import ControlOverrideRequest, DeviceCommandRequest


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScopeControlState:
    scope_type: str
    scope_id: str
    estop_active: bool = False
    manual_override_active: bool = False
    safe_mode_active: bool = False
    auto_mode_enabled: bool = True
    last_transition_at: str | None = None
    last_transition_reason: str | None = None
    last_request_id: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "estop_active": self.estop_active,
            "manual_override_active": self.manual_override_active,
            "safe_mode_active": self.safe_mode_active,
            "auto_mode_enabled": self.auto_mode_enabled,
            "last_transition_at": self.last_transition_at,
            "last_transition_reason": self.last_transition_reason,
            "last_request_id": self.last_request_id,
        }


@dataclass
class RuntimeFaultState:
    scope_type: str
    scope_id: str
    consecutive_timeout_count: int = 0
    consecutive_fault_count: int = 0
    last_status: str | None = None
    last_failure_reason: str | None = None
    last_recorded_at: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope_type": self.scope_type,
            "scope_id": self.scope_id,
            "consecutive_timeout_count": self.consecutive_timeout_count,
            "consecutive_fault_count": self.consecutive_fault_count,
            "last_status": self.last_status,
            "last_failure_reason": self.last_failure_reason,
            "last_recorded_at": self.last_recorded_at,
        }


@dataclass
class ControlStateStore:
    states: dict[str, ScopeControlState] = field(default_factory=dict)

    def _key(self, scope_type: str, scope_id: str) -> str:
        return f"{scope_type}:{scope_id}"

    def get(self, scope_type: str, scope_id: str) -> ScopeControlState:
        key = self._key(scope_type, scope_id)
        if key not in self.states:
            self.states[key] = ScopeControlState(scope_type=scope_type, scope_id=scope_id)
        return self.states[key]

    def peek(self, scope_type: str, scope_id: str) -> ScopeControlState | None:
        return self.states.get(self._key(scope_type, scope_id))

    def enter_safe_mode(
        self,
        *,
        scope_type: str,
        scope_id: str,
        reason: str,
        request_id: str,
    ) -> dict[str, Any]:
        state = self.get(scope_type, scope_id)
        before = state.as_dict()
        if state.safe_mode_active:
            return {
                "before": before,
                "after": state.as_dict(),
                "transition": "safe_mode_already_active",
            }
        state.safe_mode_active = True
        state.auto_mode_enabled = False
        state.last_transition_at = utc_now()
        state.last_transition_reason = reason
        state.last_request_id = request_id
        return {
            "before": before,
            "after": state.as_dict(),
            "transition": "safe_mode_entry",
        }

    def apply_override(self, request: ControlOverrideRequest) -> dict[str, Any]:
        state = self.get(request.scope_type, request.scope_id)
        before = state.as_dict()
        transition = request.override_type

        if request.override_type == "emergency_stop_latch":
            state.estop_active = True
            state.auto_mode_enabled = False
        elif request.override_type == "emergency_stop_reset_request":
            state.estop_active = False
        elif request.override_type == "manual_override_start":
            state.manual_override_active = True
            state.auto_mode_enabled = False
        elif request.override_type == "manual_override_release":
            state.manual_override_active = False
        elif request.override_type == "safe_mode_entry":
            state.safe_mode_active = True
            state.auto_mode_enabled = False
        elif request.override_type == "auto_mode_reentry_request":
            state.estop_active = False
            state.manual_override_active = False
            state.safe_mode_active = False
            state.auto_mode_enabled = True
        else:  # pragma: no cover - defensive branch
            raise ValueError(f"unsupported override_type {request.override_type}")

        state.last_transition_at = utc_now()
        state.last_transition_reason = transition
        state.last_request_id = request.request_id
        return {
            "before": before,
            "after": state.as_dict(),
            "transition": transition,
        }

    def evaluate_device_block(self, request: DeviceCommandRequest) -> list[str]:
        reasons: list[str] = []
        zone_id = request.raw.get("zone_id", "unknown")
        zone_state = self.peek("zone", zone_id)
        candidate_site_ids = {
            value
            for value in (
                request.raw.get("farm_id"),
                zone_id.split("-zone-")[0] if "-zone-" in zone_id else None,
                request.device_id.split("--", 1)[0] if "--" in request.device_id else None,
            )
            if isinstance(value, str) and value
        }
        site_states = [state for site_id in candidate_site_ids if (state := self.peek("site", site_id)) is not None]

        if (zone_state and zone_state.estop_active) or any(state.estop_active for state in site_states):
            reasons.append("estop_active")
        if (zone_state and zone_state.manual_override_active) or any(state.manual_override_active for state in site_states):
            if request.action_type != "pause_automation":
                reasons.append("manual_override_state_active")
        if (zone_state and zone_state.safe_mode_active) or any(state.safe_mode_active for state in site_states):
            reasons.append("safe_mode_active")
        return reasons


@dataclass
class RuntimeFaultTracker:
    safe_mode_threshold: int = 2
    states: dict[str, RuntimeFaultState] = field(default_factory=dict)

    def _key(self, scope_type: str, scope_id: str) -> str:
        return f"{scope_type}:{scope_id}"

    def get(self, scope_type: str, scope_id: str) -> RuntimeFaultState:
        key = self._key(scope_type, scope_id)
        if key not in self.states:
            self.states[key] = RuntimeFaultState(scope_type=scope_type, scope_id=scope_id)
        return self.states[key]

    def record(
        self,
        *,
        scope_type: str,
        scope_id: str,
        status: str,
        failure_reason: str | None,
    ) -> RuntimeFaultState:
        state = self.get(scope_type, scope_id)
        if status == "acknowledged":
            state.consecutive_timeout_count = 0
            state.consecutive_fault_count = 0
        elif status == "timeout":
            state.consecutive_timeout_count += 1
            state.consecutive_fault_count = 0
        elif status == "fault":
            state.consecutive_fault_count += 1
            state.consecutive_timeout_count = 0
        state.last_status = status
        state.last_failure_reason = failure_reason
        state.last_recorded_at = utc_now()
        return state

    def should_enter_safe_mode(self, scope_type: str, scope_id: str) -> bool:
        state = self.get(scope_type, scope_id)
        return (
            state.consecutive_timeout_count >= self.safe_mode_threshold
            or state.consecutive_fault_count >= self.safe_mode_threshold
        )

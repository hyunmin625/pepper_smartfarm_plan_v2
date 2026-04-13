from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bootstrap import REPO_ROOT, configure_repo_paths

configure_repo_paths()

from execution_gateway.contracts import ControlOverrideRequest, DeviceCommandRequest  # noqa: E402


DEVICE_TYPE_BY_ACTION = {
    "adjust_fan": "circulation_fan",
    "adjust_shade": "shade_curtain",
    "adjust_vent": "vent_window",
    "short_irrigation": "irrigation_valve",
    "adjust_heating": "heater",
    "adjust_co2": "co2_doser",
    "adjust_fertigation": "nutrient_mixer",
}


@dataclass(frozen=True)
class PlannedDispatch:
    kind: str
    action_type: str
    target_id: str
    payload: dict[str, Any]


class ActionDispatchPlanner:
    def __init__(self, catalog_path: Path | None = None) -> None:
        catalog_file = catalog_path or REPO_ROOT / "data" / "examples" / "sensor_catalog_seed.json"
        raw = json.loads(catalog_file.read_text(encoding="utf-8"))
        self.devices = raw.get("devices", [])

    def plan(
        self,
        *,
        decision_id: int,
        request_id: str,
        zone_id: str,
        validated_output: dict[str, Any],
        actor_id: str,
    ) -> list[PlannedDispatch]:
        plans: list[PlannedDispatch] = []
        actions = validated_output.get("recommended_actions")
        if not isinstance(actions, list):
            return plans
        for index, action in enumerate(actions, start=1):
            if not isinstance(action, dict):
                continue
            action_type = str(action.get("action_type") or "")
            action_request_id = f"{request_id}-dispatch-{index:02d}"
            if action_type in {"pause_automation", "enter_safe_mode"}:
                override_request = self._build_override_request(
                    request_id=action_request_id,
                    zone_id=zone_id,
                    actor_id=actor_id,
                    action_type=action_type,
                )
                plans.append(
                    PlannedDispatch(
                        kind="control_override",
                        action_type=action_type,
                        target_id=zone_id,
                        payload=override_request,
                    )
                )
                continue

            device_type = DEVICE_TYPE_BY_ACTION.get(action_type)
            if not device_type:
                plans.append(
                    PlannedDispatch(
                        kind="log_only",
                        action_type=action_type,
                        target_id=zone_id,
                        payload={"reason": "non_dispatchable_action"},
                    )
                )
                continue
            device_id = self._resolve_device_id(zone_id=zone_id, device_type=device_type)
            command_request = self._build_command_request(
                request_id=action_request_id,
                zone_id=zone_id,
                device_id=device_id,
                action_type=action_type,
                approval_required=bool(action.get("approval_required", False)),
            )
            plans.append(
                PlannedDispatch(
                    kind="device_command",
                    action_type=action_type,
                    target_id=device_id,
                    payload=command_request,
                )
            )
        return plans

    def _resolve_device_id(self, *, zone_id: str, device_type: str) -> str:
        if device_type == "nutrient_mixer":
            zone_id = "gh-01-nutrient-room"
        for device in self.devices:
            if device.get("zone_id") == zone_id and device.get("device_type") == device_type:
                return str(device["device_id"])
        raise KeyError(f"device not found for zone_id={zone_id} device_type={device_type}")

    @staticmethod
    def _build_command_request(
        *,
        request_id: str,
        zone_id: str,
        device_id: str,
        action_type: str,
        approval_required: bool,
    ) -> dict[str, Any]:
        return {
            "request_id": request_id,
            "device_id": device_id,
            "action_type": action_type,
            "zone_id": zone_id,
            "parameters": _default_parameters(action_type),
            "approval_required": approval_required,
            "approval_context": {
                "approval_status": "approved",
                "approver_id": "operator",
                "approved_at": _utc_now(),
            },
            "operator_context": {
                "operator_present": False,
                "manual_override": False,
            },
            "policy_snapshot": {
                "policy_result": "approval_required" if approval_required else "pass",
                "policy_ids": ["api-approval-mode"],
            },
            "sensor_quality": {"overall": "good"},
        }

    @staticmethod
    def _build_override_request(
        *,
        request_id: str,
        zone_id: str,
        actor_id: str,
        action_type: str,
    ) -> dict[str, Any]:
        reason = "AI requested pause_automation" if action_type == "pause_automation" else "AI requested enter_safe_mode"
        return {
            "request_id": request_id,
            "farm_id": "demo-farm",
            "scope_type": "zone",
            "scope_id": zone_id,
            "override_type": "safe_mode_entry",
            "approval_required": False,
            "requested_by": {
                "actor_type": "policy_engine",
                "actor_id": actor_id,
            },
            "reason": reason,
            "approval_context": {
                "approval_status": "approved",
                "approver_id": actor_id,
                "approved_at": _utc_now(),
            },
            "operator_context": {
                "operator_present": False,
                "manual_override_active": False,
                "estop_active": False,
            },
            "preconditions": {
                "state_sync_completed": True,
                "manual_override_cleared": True,
                "estop_cleared": True,
            },
            "policy_snapshot": {
                "policy_result": "pass",
                "policy_ids": ["api-approval-mode"],
            },
        }


def _default_parameters(action_type: str) -> dict[str, Any]:
    defaults = {
        "adjust_fan": {"run_state": "on", "speed_pct": 60},
        "adjust_shade": {"position_pct": 65},
        "adjust_vent": {"position_pct": 40},
        "short_irrigation": {"run_state": "open", "duration_seconds": 90},
        "adjust_heating": {"run_state": "on", "stage": 1},
        "adjust_co2": {"run_state": "on", "dose_pct": 30},
        "adjust_fertigation": {"recipe_id": "default-recipe", "mix_volume_l": 50},
    }
    return defaults.get(action_type, {})


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()

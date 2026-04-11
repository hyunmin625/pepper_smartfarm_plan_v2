from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .device_profiles import DeviceProfile, DeviceProfileRegistry
from .interface import CommandResult, PlcAdapterInterface
from .resolver import DeviceCommandResolver


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MockPlcAdapter(PlcAdapterInterface):
    def __init__(
        self,
        registry: DeviceProfileRegistry,
        *,
        resolver: DeviceCommandResolver | None = None,
    ) -> None:
        self.registry = registry
        self.resolver = resolver
        self.connected = False
        self.last_payload_by_device: dict[str, dict[str, Any]] = {}

    def connect(self) -> None:
        self.connected = True

    def health(self) -> dict[str, Any]:
        return {"status": "ok" if self.connected else "disconnected"}

    def validate_command(
        self,
        *,
        profile_id: str,
        action_type: str,
        parameters: dict[str, Any],
    ) -> None:
        profile = self.registry.get(profile_id)
        profile.validate_parameters(action_type, parameters)

    def build_command_payload(
        self,
        *,
        device_id: str,
        profile: DeviceProfile,
        action_type: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        self.validate_command(
            profile_id=profile.profile_id,
            action_type=action_type,
            parameters=parameters,
        )
        payload = {
            "device_id": device_id,
            "profile_id": profile.profile_id,
            "device_type": profile.device_type,
            "protocol": profile.protocol,
            "action_type": action_type,
            "parameters": parameters,
            "issued_at": utc_now(),
        }
        if self.resolver is None:
            payload["write_channel_ref"] = profile.mapping["write_channel_ref"]
            payload["read_channel_refs"] = profile.mapping["read_channel_refs"]
            payload["command_encoder"] = profile.mapping["command_encoder"]
            payload["readback_decoder"] = profile.mapping["readback_decoder"]
            return payload

        resolved = self.resolver.resolve(device_id)
        payload["controller_id"] = resolved.controller.controller_id
        payload["controller_endpoint"] = resolved.controller.endpoint
        payload["write_channel_ref"] = resolved.write_channel_ref
        payload["read_channel_refs"] = resolved.read_channel_refs
        payload["command_encoder"] = resolved.command_encoder
        payload["readback_decoder"] = resolved.readback_decoder
        return payload

    def write_command(
        self,
        *,
        device_id: str,
        profile_id: str,
        action_type: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.connected:
            self.connect()
        profile = self.registry.get(profile_id)
        payload = self.build_command_payload(
            device_id=device_id,
            profile=profile,
            action_type=action_type,
            parameters=parameters,
        )
        self.last_payload_by_device[device_id] = payload
        readback = self.readback(device_id=device_id, profile_id=profile_id)
        ack_ok, failure_reason = self.evaluate_ack(
            profile_id=profile_id,
            readback=readback,
            expected_parameters=parameters,
        )
        result = CommandResult(
            request_id=f"mock-{device_id}",
            device_id=device_id,
            profile_id=profile_id,
            status="acknowledged" if ack_ok else "fault",
            payload=payload,
            readback=readback,
            latency_ms=5,
            failure_reason=failure_reason,
        )
        return result.__dict__

    def write_device_command(
        self,
        *,
        device_id: str,
        action_type: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if self.resolver is None:
            raise ValueError("resolver is required for write_device_command")
        resolved = self.resolver.resolve(device_id)
        return self.write_command(
            device_id=device_id,
            profile_id=resolved.profile.profile_id,
            action_type=action_type,
            parameters=parameters,
        )

    def readback(self, *, device_id: str, profile_id: str) -> dict[str, Any]:
        profile = self.registry.get(profile_id)
        last = self.last_payload_by_device.get(device_id, {})
        base = {
            "device_id": device_id,
            "profile_id": profile_id,
            "read_at": utc_now(),
        }
        for field in profile.readback_fields:
            name = field["field_name"]
            if name in last.get("parameters", {}):
                base[name] = last["parameters"][name]
            elif name == "recipe_stage":
                base[name] = last.get("parameters", {}).get("recipe_id")
            elif name == "run_state":
                base[name] = "off"
            elif name in {"position_pct", "speed_pct", "dose_pct"}:
                base[name] = 0
            elif name == "stage":
                base[name] = 0
            elif name == "fault_code":
                base[name] = ""
            else:
                base[name] = None
        return base

    def evaluate_ack(
        self,
        *,
        profile_id: str,
        readback: dict[str, Any],
        expected_parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        profile = self.registry.get(profile_id)
        return profile.evaluate_ack(readback=readback, expected_parameters=expected_parameters)

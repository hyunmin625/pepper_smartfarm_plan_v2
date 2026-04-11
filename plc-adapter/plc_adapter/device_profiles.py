from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY_PATH = REPO_ROOT / "data/examples/device_profile_registry_seed.json"


@dataclass
class ParameterSpec:
    name: str
    data_type: str
    required: bool
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    allowed_values: list[Any] | None = None


@dataclass
class AckPolicy:
    requires_ack: bool
    ack_timeout_seconds: int
    verify_readback: bool
    success_conditions: list[str]


@dataclass
class DeviceProfile:
    profile_id: str
    device_type: str
    protocol: str
    control_mode: str
    command_family: str
    supported_action_types: list[str]
    supported_modes: list[str]
    parameter_specs: list[ParameterSpec]
    readback_fields: list[dict[str, Any]]
    safety_interlocks: list[str]
    ack_policy: AckPolicy
    mapping: dict[str, Any]

    def validate_parameters(self, action_type: str, parameters: dict[str, Any]) -> None:
        if action_type not in self.supported_action_types:
            raise ValueError(f"{self.profile_id}: unsupported action_type {action_type}")

        by_name = {spec.name: spec for spec in self.parameter_specs}
        for spec in self.parameter_specs:
            if spec.required and spec.name not in parameters:
                raise ValueError(f"{self.profile_id}: missing required parameter {spec.name}")

        for key, value in parameters.items():
            spec = by_name.get(key)
            if spec is None:
                raise ValueError(f"{self.profile_id}: unknown parameter {key}")
            if spec.data_type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
                raise ValueError(f"{self.profile_id}: parameter {key} must be integer")
            if spec.data_type == "number" and not isinstance(value, (int, float)):
                raise ValueError(f"{self.profile_id}: parameter {key} must be numeric")
            if spec.data_type == "boolean" and not isinstance(value, bool):
                raise ValueError(f"{self.profile_id}: parameter {key} must be boolean")
            if spec.data_type == "string" and not isinstance(value, str):
                raise ValueError(f"{self.profile_id}: parameter {key} must be string")
            if spec.minimum is not None and value < spec.minimum:
                raise ValueError(f"{self.profile_id}: parameter {key} below minimum")
            if spec.maximum is not None and value > spec.maximum:
                raise ValueError(f"{self.profile_id}: parameter {key} above maximum")
            if spec.allowed_values is not None and value not in spec.allowed_values:
                raise ValueError(f"{self.profile_id}: parameter {key} has unsupported value")

    def evaluate_ack(
        self,
        *,
        readback: dict[str, Any],
        expected_parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        if not self.ack_policy.requires_ack:
            return True, None
        if not self.ack_policy.verify_readback:
            return True, None

        for condition in self.ack_policy.success_conditions:
            ok, failure_reason = _evaluate_success_condition(
                condition=condition,
                readback=readback,
                expected_parameters=expected_parameters,
            )
            if not ok:
                return False, failure_reason
        return True, None


class DeviceProfileRegistry:
    def __init__(self, *, registry_version: str, profiles: dict[str, DeviceProfile]) -> None:
        self.registry_version = registry_version
        self.profiles = profiles

    def get(self, profile_id: str) -> DeviceProfile:
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise KeyError(f"unknown device profile {profile_id}")
        return profile

    def list_profile_ids(self) -> list[str]:
        return sorted(self.profiles)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


def _evaluate_success_condition(
    *,
    condition: str,
    readback: dict[str, Any],
    expected_parameters: dict[str, Any],
) -> tuple[bool, str | None]:
    if condition == "run_state_matches":
        expected = expected_parameters.get("run_state")
        actual = readback.get("run_state")
        if expected == actual:
            return True, None
        return False, f"run_state_mismatch expected={expected} actual={actual}"

    if condition == "stage_matches":
        expected = expected_parameters.get("stage")
        actual = readback.get("stage")
        if expected == actual:
            return True, None
        return False, f"stage_mismatch expected={expected} actual={actual}"

    if condition == "recipe_stage_matches":
        expected = expected_parameters.get("recipe_id")
        actual = readback.get("recipe_stage")
        if expected == actual:
            return True, None
        return False, f"recipe_stage_mismatch expected={expected} actual={actual}"

    if condition == "position_pct_within_tolerance":
        return _within_tolerance("position_pct", readback, expected_parameters, tolerance=5)

    if condition == "speed_pct_within_tolerance":
        return _within_tolerance("speed_pct", readback, expected_parameters, tolerance=5)

    if condition == "dose_pct_within_tolerance":
        return _within_tolerance("dose_pct", readback, expected_parameters, tolerance=5)

    return False, f"unsupported_success_condition {condition}"


def _within_tolerance(
    field_name: str,
    readback: dict[str, Any],
    expected_parameters: dict[str, Any],
    *,
    tolerance: float,
) -> tuple[bool, str | None]:
    expected = expected_parameters.get(field_name)
    actual = readback.get(field_name)
    if expected is None or actual is None:
        return False, f"{field_name}_missing_for_ack"
    if abs(actual - expected) <= tolerance:
        return True, None
    return False, f"{field_name}_outside_tolerance expected={expected} actual={actual}"


def load_profile_registry(path: Path = DEFAULT_REGISTRY_PATH) -> DeviceProfileRegistry:
    raw = _load_json(path)
    registry_version = raw.get("registry_version")
    if not isinstance(registry_version, str) or not registry_version.strip():
        raise ValueError(f"{path}: registry_version must be a non-empty string")

    profiles: dict[str, DeviceProfile] = {}
    for item in raw.get("device_profiles", []):
        parameter_specs = [
            ParameterSpec(
                name=spec["name"],
                data_type=spec["data_type"],
                required=spec["required"],
                unit=spec.get("unit"),
                minimum=spec.get("minimum"),
                maximum=spec.get("maximum"),
                allowed_values=spec.get("allowed_values"),
            )
            for spec in item["parameter_specs"]
        ]
        ack_policy = AckPolicy(**item["ack_policy"])
        profile = DeviceProfile(
            profile_id=item["profile_id"],
            device_type=item["device_type"],
            protocol=item["protocol"],
            control_mode=item["control_mode"],
            command_family=item["command_family"],
            supported_action_types=item["supported_action_types"],
            supported_modes=item["supported_modes"],
            parameter_specs=parameter_specs,
            readback_fields=item["readback_fields"],
            safety_interlocks=item["safety_interlocks"],
            ack_policy=ack_policy,
            mapping=item["mapping"],
        )
        if profile.profile_id in profiles:
            raise ValueError(f"{path}: duplicate profile_id {profile.profile_id}")
        profiles[profile.profile_id] = profile
    return DeviceProfileRegistry(registry_version=registry_version, profiles=profiles)

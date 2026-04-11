#!/usr/bin/env python3
"""Validate device profile registry and cross-check it with the device catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "data/examples/device_profile_registry_seed.json"
DEFAULT_CATALOG = REPO_ROOT / "data/examples/sensor_catalog_seed.json"
DEFAULT_ACTION_SCHEMA = REPO_ROOT / "schemas/action_schema.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


def validate_profile(profile: dict[str, Any], index: int, errors: list[str]) -> None:
    prefix = f"device_profiles[{index}]"
    required_strings = ["profile_id", "device_type", "protocol", "control_mode", "command_family"]
    for field_name in required_strings:
        value = profile.get(field_name)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}: {field_name} must be a non-empty string")

    for field_name in ("supported_action_types", "supported_modes", "safety_interlocks"):
        value = profile.get(field_name)
        if not isinstance(value, list) or not value:
            errors.append(f"{prefix}: {field_name} must be a non-empty array")
            continue
        for item_index, item in enumerate(value, start=1):
            if not isinstance(item, str) or not item.strip():
                errors.append(f"{prefix}: {field_name}[{item_index}] must be a non-empty string")

    parameter_specs = profile.get("parameter_specs")
    if not isinstance(parameter_specs, list):
        errors.append(f"{prefix}: parameter_specs must be an array")
    else:
        for param_index, parameter in enumerate(parameter_specs, start=1):
            if not isinstance(parameter, dict):
                errors.append(f"{prefix}: parameter_specs[{param_index}] must be an object")
                continue
            name = parameter.get("name")
            data_type = parameter.get("data_type")
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{prefix}: parameter_specs[{param_index}].name must be a non-empty string")
            if data_type not in {"number", "integer", "boolean", "string"}:
                errors.append(f"{prefix}: parameter_specs[{param_index}].data_type is invalid")
            if not isinstance(parameter.get("required"), bool):
                errors.append(f"{prefix}: parameter_specs[{param_index}].required must be a boolean")
            minimum = parameter.get("minimum")
            maximum = parameter.get("maximum")
            if minimum is not None and maximum is not None and maximum < minimum:
                errors.append(f"{prefix}: parameter_specs[{param_index}] maximum must be >= minimum")

    readback_fields = profile.get("readback_fields")
    if not isinstance(readback_fields, list) or not readback_fields:
        errors.append(f"{prefix}: readback_fields must be a non-empty array")
    else:
        for field_index, field in enumerate(readback_fields, start=1):
            if not isinstance(field, dict):
                errors.append(f"{prefix}: readback_fields[{field_index}] must be an object")
                continue
            if not isinstance(field.get("field_name"), str) or not field["field_name"].strip():
                errors.append(f"{prefix}: readback_fields[{field_index}].field_name must be a non-empty string")
            if field.get("data_type") not in {"number", "integer", "boolean", "string"}:
                errors.append(f"{prefix}: readback_fields[{field_index}].data_type is invalid")
            if not isinstance(field.get("required"), bool):
                errors.append(f"{prefix}: readback_fields[{field_index}].required must be a boolean")

    ack_policy = profile.get("ack_policy")
    if not isinstance(ack_policy, dict):
        errors.append(f"{prefix}: ack_policy must be an object")
    else:
        if not isinstance(ack_policy.get("requires_ack"), bool):
            errors.append(f"{prefix}: ack_policy.requires_ack must be a boolean")
        if not isinstance(ack_policy.get("ack_timeout_seconds"), int) or ack_policy["ack_timeout_seconds"] < 1:
            errors.append(f"{prefix}: ack_policy.ack_timeout_seconds must be a positive integer")
        if not isinstance(ack_policy.get("verify_readback"), bool):
            errors.append(f"{prefix}: ack_policy.verify_readback must be a boolean")
        success_conditions = ack_policy.get("success_conditions")
        if not isinstance(success_conditions, list) or not success_conditions:
            errors.append(f"{prefix}: ack_policy.success_conditions must be a non-empty array")

    mapping = profile.get("mapping")
    if not isinstance(mapping, dict):
        errors.append(f"{prefix}: mapping must be an object")
    else:
        if mapping.get("write_channel_type") not in {"plc_register", "plc_coil", "opcua_node", "virtual"}:
            errors.append(f"{prefix}: mapping.write_channel_type is invalid")
        for field_name in ("write_channel_ref", "command_encoder", "readback_decoder"):
            value = mapping.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{prefix}: mapping.{field_name} must be a non-empty string")
        read_refs = mapping.get("read_channel_refs")
        if not isinstance(read_refs, list) or not read_refs:
            errors.append(f"{prefix}: mapping.read_channel_refs must be a non-empty array")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--action-schema", default=str(DEFAULT_ACTION_SCHEMA))
    args = parser.parse_args()

    registry = load_json(Path(args.registry))
    catalog = load_json(Path(args.catalog))
    action_schema = load_json(Path(args.action_schema))

    errors: list[str] = []
    action_type_enum = (
        action_schema.get("$defs", {})
        .get("recommended_action", {})
        .get("properties", {})
        .get("action_type", {})
        .get("enum", [])
    )
    valid_action_types = {
        action_type
        for action_type in action_type_enum
        if isinstance(action_type, str) and action_type.strip()
    }

    profiles = registry.get("device_profiles")
    if not isinstance(profiles, list) or not profiles:
        errors.append("registry: device_profiles must be a non-empty array")
        profiles = []

    profile_counter: Counter[str] = Counter()
    profile_by_id: dict[str, dict[str, Any]] = {}
    for index, profile in enumerate(profiles, start=1):
        if not isinstance(profile, dict):
            errors.append(f"device_profiles[{index}] must be an object")
            continue
        validate_profile(profile, index, errors)
        profile_id = profile.get("profile_id")
        if isinstance(profile_id, str):
            profile_counter[profile_id] += 1
            profile_by_id[profile_id] = profile
        supported_action_types = profile.get("supported_action_types", [])
        if isinstance(supported_action_types, list):
            for action_type in supported_action_types:
                if action_type not in valid_action_types:
                    errors.append(
                        f"device_profiles[{index}]: unsupported action_type {action_type} is not defined in action_schema"
                    )

    for profile_id, count in sorted(profile_counter.items()):
        if count > 1:
            errors.append(f"registry: duplicate profile_id {profile_id}")

    catalog_devices = catalog.get("devices")
    if not isinstance(catalog_devices, list):
        errors.append("catalog: devices must be an array")
        catalog_devices = []

    referenced_profiles: Counter[str] = Counter()
    for index, device in enumerate(catalog_devices, start=1):
        if not isinstance(device, dict):
            errors.append(f"catalog.devices[{index}] must be an object")
            continue
        profile_id = device.get("model_profile")
        device_id = device.get("device_id", f"catalog.devices[{index}]")
        if not isinstance(profile_id, str) or not profile_id.strip():
            errors.append(f"{device_id}: model_profile must be a non-empty string")
            continue
        referenced_profiles[profile_id] += 1
        profile = profile_by_id.get(profile_id)
        if profile is None:
            errors.append(f"{device_id}: model_profile {profile_id} is missing from registry")
            continue
        device_type = device.get("device_type")
        if profile.get("device_type") != device_type:
            errors.append(f"{device_id}: registry device_type mismatch for profile {profile_id}")
        if profile.get("protocol") != device.get("protocol"):
            errors.append(f"{device_id}: registry protocol mismatch for profile {profile_id}")
        if profile.get("control_mode") != device.get("control_mode"):
            errors.append(f"{device_id}: registry control_mode mismatch for profile {profile_id}")
        interlocks = set(device.get("safety_interlocks", []))
        profile_interlocks = set(profile.get("safety_interlocks", []))
        if interlocks != profile_interlocks:
            errors.append(f"{device_id}: registry safety_interlocks mismatch for profile {profile_id}")

    unused_profiles = sorted(set(profile_by_id) - set(referenced_profiles))

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"registry_path: {args.registry}")
    print(f"catalog_path: {args.catalog}")
    print(f"action_schema_path: {args.action_schema}")
    print(f"device_profiles: {len(profile_by_id)}")
    print(f"catalog_devices: {len(catalog_devices)}")
    print(f"referenced_profiles: {len(referenced_profiles)}")
    print(f"unused_profiles: {len(unused_profiles)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate site override address map against device catalog and device profile registry."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))

from plc_adapter.channel_refs import parse_plc_tag_ref

DEFAULT_SITE_OVERRIDE = REPO_ROOT / "data/examples/device_site_override_seed.json"
DEFAULT_CATALOG = REPO_ROOT / "data/examples/sensor_catalog_seed.json"
DEFAULT_REGISTRY = REPO_ROOT / "data/examples/device_profile_registry_seed.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-override", default=str(DEFAULT_SITE_OVERRIDE))
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    args = parser.parse_args()

    site_override = load_json(Path(args.site_override))
    catalog = load_json(Path(args.catalog))
    registry = load_json(Path(args.registry))

    errors: list[str] = []
    controllers = site_override.get("controllers")
    bindings = site_override.get("device_bindings")
    devices = catalog.get("devices")
    profiles = registry.get("device_profiles")

    if not isinstance(controllers, list) or not controllers:
        errors.append("site_override: controllers must be a non-empty array")
        controllers = []
    if not isinstance(bindings, list) or not bindings:
        errors.append("site_override: device_bindings must be a non-empty array")
        bindings = []
    if not isinstance(devices, list):
        errors.append("catalog: devices must be an array")
        devices = []
    if not isinstance(profiles, list):
        errors.append("registry: device_profiles must be an array")
        profiles = []

    controller_by_id = {}
    controller_counter: Counter[str] = Counter()
    for item in controllers:
        controller_id = item.get("controller_id")
        if isinstance(controller_id, str):
            controller_counter[controller_id] += 1
            controller_by_id[controller_id] = item

    for controller_id, count in sorted(controller_counter.items()):
        if count > 1:
            errors.append(f"site_override: duplicate controller_id {controller_id}")

    profile_by_id = {
        item["profile_id"]: item
        for item in profiles
        if isinstance(item, dict) and isinstance(item.get("profile_id"), str)
    }
    device_by_id = {
        item["device_id"]: item
        for item in devices
        if isinstance(item, dict) and isinstance(item.get("device_id"), str)
    }

    binding_by_device = {}
    binding_counter: Counter[str] = Counter()
    for item in bindings:
        if not isinstance(item, dict):
            errors.append("site_override: each device binding must be an object")
            continue
        device_id = item.get("device_id")
        if not isinstance(device_id, str) or not device_id.strip():
            errors.append("site_override: device_id must be a non-empty string")
            continue
        binding_counter[device_id] += 1
        binding_by_device[device_id] = item

        controller_id = item.get("controller_id")
        controller = controller_by_id.get(controller_id)
        if controller is None:
            errors.append(f"{device_id}: unknown controller_id {controller_id}")
            continue

        device = device_by_id.get(device_id)
        if device is None:
            errors.append(f"{device_id}: not found in device catalog")
            continue

        profile_id = item.get("profile_id")
        profile = profile_by_id.get(profile_id)
        if profile is None:
            errors.append(f"{device_id}: unknown profile_id {profile_id}")
            continue

        if profile_id != device.get("model_profile"):
            errors.append(f"{device_id}: profile_id {profile_id} does not match catalog model_profile {device.get('model_profile')}")
        if item.get("protocol") != device.get("protocol"):
            errors.append(f"{device_id}: binding protocol {item.get('protocol')} does not match catalog protocol {device.get('protocol')}")
        if controller.get("protocol") != item.get("protocol"):
            errors.append(f"{device_id}: controller protocol {controller.get('protocol')} does not match binding protocol {item.get('protocol')}")

        write_channel_ref = item.get("write_channel_ref")
        if isinstance(write_channel_ref, str):
            try:
                parsed_write = parse_plc_tag_ref(write_channel_ref)
                if parsed_write.controller_id != controller_id:
                    errors.append(
                        f"{device_id}: write_channel_ref controller {parsed_write.controller_id} does not match controller_id {controller_id}"
                    )
            except ValueError as exc:
                errors.append(f"{device_id}: invalid write_channel_ref {exc}")
        else:
            errors.append(f"{device_id}: write_channel_ref must be a non-empty string")

        read_channel_refs = item.get("read_channel_refs")
        profile_read_fields = profile.get("readback_fields", [])
        if not isinstance(read_channel_refs, list) or not read_channel_refs:
            errors.append(f"{device_id}: read_channel_refs must be a non-empty array")
        elif len(read_channel_refs) != len(profile_read_fields):
            errors.append(
                f"{device_id}: read_channel_refs count {len(read_channel_refs)} does not match profile readback_fields {len(profile_read_fields)}"
            )
        else:
            for read_channel_ref in read_channel_refs:
                try:
                    parsed_read = parse_plc_tag_ref(read_channel_ref)
                    if parsed_read.controller_id != controller_id:
                        errors.append(
                            f"{device_id}: read_channel_ref controller {parsed_read.controller_id} does not match controller_id {controller_id}"
                        )
                except ValueError as exc:
                    errors.append(f"{device_id}: invalid read_channel_ref {exc}")

    for device_id, count in sorted(binding_counter.items()):
        if count > 1:
            errors.append(f"site_override: duplicate binding for {device_id}")

    plc_devices = [item for item in devices if item.get("protocol") == "plc_tag_modbus_tcp"]
    missing_bindings = sorted(
        item["device_id"] for item in plc_devices if item.get("device_id") not in binding_by_device
    )
    for device_id in missing_bindings:
        errors.append(f"{device_id}: missing binding in site override")

    unused_bindings = sorted(set(binding_by_device) - {item["device_id"] for item in plc_devices})

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"site_override_path: {args.site_override}")
    print(f"catalog_path: {args.catalog}")
    print(f"registry_path: {args.registry}")
    print(f"controllers: {len(controller_by_id)}")
    print(f"device_bindings: {len(binding_by_device)}")
    print(f"plc_devices_in_catalog: {len(plc_devices)}")
    print(f"unused_bindings: {len(unused_bindings)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Validate Modbus channel address registry against the site override map."""

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
DEFAULT_CHANNEL_MAP = REPO_ROOT / "data/examples/device_channel_address_registry_seed.json"

WRITE_TABLES = {"holding_register", "coil"}
READ_TABLES = {"input_register", "discrete_input", "holding_register", "coil"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-override", default=str(DEFAULT_SITE_OVERRIDE))
    parser.add_argument("--channel-map", default=str(DEFAULT_CHANNEL_MAP))
    args = parser.parse_args()

    site_override = load_json(Path(args.site_override))
    channel_map = load_json(Path(args.channel_map))

    errors: list[str] = []
    expected_channels: dict[str, tuple[str, str]] = {}
    for binding in site_override.get("device_bindings", []):
        if not isinstance(binding, dict):
            continue
        controller_id = binding.get("controller_id")
        write_channel_ref = binding.get("write_channel_ref")
        if isinstance(write_channel_ref, str):
            expected_channels[write_channel_ref] = (controller_id, "write")
        for read_channel_ref in binding.get("read_channel_refs", []):
            if isinstance(read_channel_ref, str):
                expected_channels[read_channel_ref] = (controller_id, "read")

    channels = channel_map.get("channels")
    if not isinstance(channels, list) or not channels:
        errors.append("channel_map: channels must be a non-empty array")
        channels = []

    channel_counter: Counter[str] = Counter()
    address_counter: Counter[tuple[str, str, int, int | None]] = Counter()
    present_channels: set[str] = set()

    for item in channels:
        if not isinstance(item, dict):
            errors.append("channel_map: each channel must be an object")
            continue

        channel_ref = item.get("channel_ref")
        controller_id = item.get("controller_id")
        access = item.get("access")
        table = item.get("table")
        address = item.get("address")
        protocol = item.get("protocol")
        bit_index = item.get("bit_index")

        if not isinstance(channel_ref, str) or not channel_ref:
            errors.append("channel_map: channel_ref must be a non-empty string")
            continue

        channel_counter[channel_ref] += 1
        present_channels.add(channel_ref)

        try:
            parsed = parse_plc_tag_ref(channel_ref)
        except ValueError as exc:
            errors.append(f"{channel_ref}: invalid channel_ref {exc}")
            continue

        if parsed.controller_id != controller_id:
            errors.append(
                f"{channel_ref}: controller_id {controller_id} does not match ref controller {parsed.controller_id}"
            )

        expected = expected_channels.get(channel_ref)
        if expected is None:
            errors.append(f"{channel_ref}: not referenced by site override")
        else:
            expected_controller_id, expected_access = expected
            if controller_id != expected_controller_id:
                errors.append(
                    f"{channel_ref}: controller_id {controller_id} does not match site override controller {expected_controller_id}"
                )
            if access != expected_access:
                errors.append(f"{channel_ref}: access {access} does not match expected {expected_access}")

        if protocol != "plc_tag_modbus_tcp":
            errors.append(f"{channel_ref}: unsupported protocol {protocol}")
        if not isinstance(address, int) or address <= 0:
            errors.append(f"{channel_ref}: address must be a positive integer")

        allowed_tables = WRITE_TABLES if access == "write" else READ_TABLES
        if table not in allowed_tables:
            errors.append(f"{channel_ref}: table {table} is invalid for access {access}")

        if bit_index is not None and (not isinstance(bit_index, int) or bit_index < 0):
            errors.append(f"{channel_ref}: bit_index must be a non-negative integer when present")

        if isinstance(address, int) and isinstance(table, str) and isinstance(controller_id, str):
            address_counter[(controller_id, table, address, bit_index)] += 1

    for channel_ref, count in sorted(channel_counter.items()):
        if count > 1:
            errors.append(f"channel_map: duplicate channel_ref {channel_ref}")

    for key, count in sorted(address_counter.items()):
        if count > 1:
            controller_id, table, address, bit_index = key
            errors.append(
                f"channel_map: duplicate address controller={controller_id} table={table} address={address} bit_index={bit_index}"
            )

    missing_channels = sorted(set(expected_channels) - present_channels)
    for channel_ref in missing_channels:
        errors.append(f"{channel_ref}: missing from channel_map")

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"site_override_path: {args.site_override}")
    print(f"channel_map_path: {args.channel_map}")
    print(f"expected_channels: {len(expected_channels)}")
    print(f"mapped_channels: {len(present_channels)}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()

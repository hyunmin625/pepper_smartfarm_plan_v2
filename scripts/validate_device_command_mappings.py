#!/usr/bin/env python3
"""Execute representative device commands through plc-adapter and verify mapping paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))

from plc_adapter.channel_address_registry import load_channel_address_registry
from plc_adapter.codecs import CodecRegistry
from plc_adapter.device_catalog import load_device_catalog
from plc_adapter.device_profiles import load_profile_registry
from plc_adapter.plc_tag_modbus_tcp import PlcTagModbusTcpAdapter
from plc_adapter.resolver import DeviceCommandResolver
from plc_adapter.site_overrides import load_site_override_registry
from plc_adapter.transports import InMemoryPlcTagTransport


DEFAULT_INPUT = REPO_ROOT / "data/examples/device_command_mapping_samples.jsonl"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(item)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    args = parser.parse_args()

    rows = load_jsonl(Path(args.input))
    catalog = load_device_catalog()
    registry = load_profile_registry()
    site_overrides = load_site_override_registry()
    channel_addresses = load_channel_address_registry()
    resolver = DeviceCommandResolver(
        catalog=catalog,
        profiles=registry,
        site_overrides=site_overrides,
    )
    adapter = PlcTagModbusTcpAdapter(
        registry=registry,
        resolver=resolver,
        transport=InMemoryPlcTagTransport(),
        channel_addresses=channel_addresses,
        codec_registry=CodecRegistry(),
        max_retries=0,
    )

    errors: list[str] = []
    summaries: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        prefix = f"rows[{index}]"
        device_id = row["device_id"]
        action_type = row["action_type"]
        parameters = row["parameters"]

        try:
            result = adapter.write_device_command(
                device_id=device_id,
                action_type=action_type,
                parameters=parameters,
            )
        except Exception as exc:  # pragma: no cover - surfaced as validator error
            errors.append(f"{prefix}: adapter error {exc}")
            continue

        payload = result.get("payload", {})
        transport_write_values = payload.get("transport_write_values", {})
        transport_read_refs = payload.get("transport_read_refs", [])
        write_channel_address = payload.get("write_channel_address", {})
        read_channel_addresses = payload.get("read_channel_addresses", [])

        if result.get("status") != "acknowledged":
            errors.append(f"{prefix}: status {result.get('status')} is not acknowledged")
        if not transport_write_values:
            errors.append(f"{prefix}: transport_write_values is empty")
        if not transport_read_refs:
            errors.append(f"{prefix}: transport_read_refs is empty")
        if write_channel_address.get("access") != "write":
            errors.append(f"{prefix}: write_channel_address access must be write")
        if not read_channel_addresses:
            errors.append(f"{prefix}: read_channel_addresses is empty")
        elif any(address.get("access") != "read" for address in read_channel_addresses):
            errors.append(f"{prefix}: read_channel_addresses must all be read")

        summaries.append(
            {
                "request_id": row["request_id"],
                "device_id": device_id,
                "action_type": action_type,
                "status": result.get("status"),
                "profile_id": result.get("profile_id"),
                "write_transport_refs": sorted(transport_write_values),
                "read_transport_refs": transport_read_refs,
            }
        )

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"input_path: {args.input}")
    print(f"rows: {len(rows)}")
    print(f"errors: {len(errors)}")
    print("validated_commands:")
    for item in summaries:
        print(json.dumps(item, ensure_ascii=False))

    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()

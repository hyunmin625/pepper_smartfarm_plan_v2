#!/usr/bin/env python3
"""Generate a deterministic Modbus address registry from the site override map."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_OVERRIDE = REPO_ROOT / "data/examples/device_site_override_seed.json"
DEFAULT_OUTPUT = REPO_ROOT / "data/examples/device_channel_address_registry_seed.json"

TABLE_BASES = {
    "gh-01-main-plc": {
        "holding_register": 40001,
        "input_register": 30001,
        "discrete_input": 10001,
    },
    "gh-01-dry-plc": {
        "holding_register": 41001,
        "input_register": 31001,
        "discrete_input": 11001,
    },
}


def classify_channel(*, channel_ref: str, write_refs: set[str]) -> tuple[str, str, str, float]:
    field = channel_ref.rsplit("/", 1)[-1]
    if channel_ref in write_refs:
        data_type = "boolean" if field == "open_close_cmd" else "uint16"
        return "write", "holding_register", data_type, 1.0

    if field == "run_state":
        return "read", "discrete_input", "boolean", 1.0
    if field in {"speed_feedback", "position_feedback", "dose_feedback"}:
        return "read", "input_register", "uint16", 1.0
    if field in {"fault_code", "stage_feedback", "recipe_stage"}:
        return "read", "input_register", "uint16", 1.0
    return "read", "input_register", "uint16", 1.0


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


def build_registry(site_override: dict) -> dict:
    device_bindings = site_override["device_bindings"]
    write_refs = {item["write_channel_ref"] for item in device_bindings}

    channels_by_controller: dict[str, list[str]] = {}
    for item in device_bindings:
        controller_id = item["controller_id"]
        refs = [item["write_channel_ref"], *item["read_channel_refs"]]
        channels_by_controller.setdefault(controller_id, []).extend(refs)

    channels: list[dict[str, object]] = []
    for controller_id, refs in sorted(channels_by_controller.items()):
        bases = dict(TABLE_BASES.get(controller_id, {}))
        if not bases:
            bases = {
                "holding_register": 49001,
                "input_register": 39001,
                "discrete_input": 19001,
            }
        next_address = dict(bases)
        for channel_ref in sorted(set(refs)):
            access, table, data_type, scale = classify_channel(
                channel_ref=channel_ref,
                write_refs=write_refs,
            )
            address = next_address[table]
            next_address[table] += 1
            channels.append(
                {
                    "channel_ref": channel_ref,
                    "controller_id": controller_id,
                    "protocol": "plc_tag_modbus_tcp",
                    "access": access,
                    "table": table,
                    "address": address,
                    "data_type": data_type,
                    "quantity": 1,
                    "scale": scale,
                    "notes": "generated placeholder address map",
                }
            )

    return {
        "site_id": site_override["site_id"],
        "site_version": site_override["site_version"],
        "catalog_version": site_override["catalog_version"],
        "registry_version": site_override["registry_version"],
        "channel_map_version": site_override["site_version"],
        "channels": channels,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-override", default=str(DEFAULT_SITE_OVERRIDE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    site_override = load_json(Path(args.site_override))
    output = Path(args.output)
    registry = build_registry(site_override)
    output.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"site_override_path: {args.site_override}")
    print(f"output_path: {args.output}")
    print(f"channels: {len(registry['channels'])}")


if __name__ == "__main__":
    main()

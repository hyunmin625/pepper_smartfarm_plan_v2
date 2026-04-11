from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


def resolve_catalog_path(config_path: Path, catalog_ref: str) -> Path:
    reference = Path(catalog_ref)
    if reference.is_absolute():
        return reference
    candidate = config_path.parent / reference
    if candidate.exists():
        return candidate
    return Path(catalog_ref)


@dataclass
class LoadedConfig:
    config_path: Path
    catalog_path: Path
    config: dict[str, Any]
    catalog: dict[str, Any]
    poller_profiles: dict[str, dict[str, Any]]
    connections: dict[str, dict[str, Any]]
    quality_rule_sets: dict[str, dict[str, Any]]
    sensors: dict[str, dict[str, Any]]
    devices: dict[str, dict[str, Any]]
    publish_targets: dict[str, dict[str, Any]]

    @classmethod
    def from_files(cls, config_path: str, catalog_path: str | None = None) -> "LoadedConfig":
        config_file = Path(config_path)
        config = load_json(config_file)
        resolved_catalog = Path(catalog_path) if catalog_path else resolve_catalog_path(config_file, config["catalog_ref"])
        catalog = load_json(resolved_catalog)

        poller_profiles = {
            item["profile_id"]: item
            for item in config.get("poller_profiles", [])
            if isinstance(item, dict) and isinstance(item.get("profile_id"), str)
        }
        connections = {
            item["connection_id"]: item
            for item in config.get("connections", [])
            if isinstance(item, dict) and isinstance(item.get("connection_id"), str)
        }
        quality_rule_sets = {
            item["rule_set_id"]: item
            for item in config.get("quality_rule_sets", [])
            if isinstance(item, dict) and isinstance(item.get("rule_set_id"), str)
        }
        sensors = {
            item["sensor_id"]: item
            for item in catalog.get("sensors", [])
            if isinstance(item, dict) and isinstance(item.get("sensor_id"), str)
        }
        devices = {
            item["device_id"]: item
            for item in catalog.get("devices", [])
            if isinstance(item, dict) and isinstance(item.get("device_id"), str)
        }
        publish_targets = {
            item["target_id"]: item
            for item in config.get("publish_targets", [])
            if isinstance(item, dict) and isinstance(item.get("target_id"), str)
        }

        return cls(
            config_path=config_file,
            catalog_path=resolved_catalog,
            config=config,
            catalog=catalog,
            poller_profiles=poller_profiles,
            connections=connections,
            quality_rule_sets=quality_rule_sets,
            sensors=sensors,
            devices=devices,
            publish_targets=publish_targets,
        )

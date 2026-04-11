from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = REPO_ROOT / "data/examples/sensor_catalog_seed.json"


@dataclass
class DeviceCatalogEntry:
    device_id: str
    device_type: str
    profile_id: str
    protocol: str
    control_mode: str
    safety_interlocks: list[str]


class DeviceCatalog:
    def __init__(self, *, catalog_version: str, devices: dict[str, DeviceCatalogEntry]) -> None:
        self.catalog_version = catalog_version
        self.devices = devices

    def get(self, device_id: str) -> DeviceCatalogEntry:
        device = self.devices.get(device_id)
        if device is None:
            raise KeyError(f"unknown device_id {device_id}")
        return device

    def list_device_ids(self) -> list[str]:
        return sorted(self.devices)


def load_device_catalog(path: Path = DEFAULT_CATALOG_PATH) -> DeviceCatalog:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: root must be a JSON object")

    catalog_version = raw.get("catalog_version")
    if not isinstance(catalog_version, str) or not catalog_version.strip():
        raise ValueError(f"{path}: catalog_version must be a non-empty string")

    devices: dict[str, DeviceCatalogEntry] = {}
    for item in raw.get("devices", []):
        device = DeviceCatalogEntry(
            device_id=item["device_id"],
            device_type=item["device_type"],
            profile_id=item["model_profile"],
            protocol=item["protocol"],
            control_mode=item["control_mode"],
            safety_interlocks=item.get("safety_interlocks", []),
        )
        if device.device_id in devices:
            raise ValueError(f"{path}: duplicate device_id {device.device_id}")
        devices[device.device_id] = device

    return DeviceCatalog(catalog_version=catalog_version, devices=devices)

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SITE_OVERRIDE_PATH = REPO_ROOT / "data/examples/device_site_override_seed.json"


@dataclass
class ControllerBinding:
    controller_id: str
    protocol: str
    endpoint: str
    role: str


@dataclass
class SiteDeviceBinding:
    device_id: str
    profile_id: str
    controller_id: str
    protocol: str
    write_channel_ref: str
    read_channel_refs: list[str]
    command_encoder: str | None = None
    readback_decoder: str | None = None


class SiteOverrideRegistry:
    def __init__(
        self,
        *,
        site_id: str,
        site_version: str,
        registry_version: str,
        catalog_version: str,
        controllers: dict[str, ControllerBinding],
        bindings: dict[str, SiteDeviceBinding],
    ) -> None:
        self.site_id = site_id
        self.site_version = site_version
        self.registry_version = registry_version
        self.catalog_version = catalog_version
        self.controllers = controllers
        self.bindings = bindings

    def get_binding(self, device_id: str) -> SiteDeviceBinding:
        binding = self.bindings.get(device_id)
        if binding is None:
            raise KeyError(f"unknown site override binding for {device_id}")
        return binding

    def get_controller(self, controller_id: str) -> ControllerBinding:
        controller = self.controllers.get(controller_id)
        if controller is None:
            raise KeyError(f"unknown controller_id {controller_id}")
        return controller


def load_site_override_registry(path: Path = DEFAULT_SITE_OVERRIDE_PATH) -> SiteOverrideRegistry:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: root must be a JSON object")

    controllers: dict[str, ControllerBinding] = {}
    for item in raw.get("controllers", []):
        controller = ControllerBinding(
            controller_id=item["controller_id"],
            protocol=item["protocol"],
            endpoint=item["endpoint"],
            role=item["role"],
        )
        if controller.controller_id in controllers:
            raise ValueError(f"{path}: duplicate controller_id {controller.controller_id}")
        controllers[controller.controller_id] = controller

    bindings: dict[str, SiteDeviceBinding] = {}
    for item in raw.get("device_bindings", []):
        binding = SiteDeviceBinding(
            device_id=item["device_id"],
            profile_id=item["profile_id"],
            controller_id=item["controller_id"],
            protocol=item["protocol"],
            write_channel_ref=item["write_channel_ref"],
            read_channel_refs=item["read_channel_refs"],
            command_encoder=item.get("command_encoder"),
            readback_decoder=item.get("readback_decoder"),
        )
        if binding.device_id in bindings:
            raise ValueError(f"{path}: duplicate device binding {binding.device_id}")
        bindings[binding.device_id] = binding

    return SiteOverrideRegistry(
        site_id=raw["site_id"],
        site_version=raw["site_version"],
        registry_version=raw["registry_version"],
        catalog_version=raw["catalog_version"],
        controllers=controllers,
        bindings=bindings,
    )

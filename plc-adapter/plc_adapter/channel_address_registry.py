from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .channel_refs import parse_plc_tag_ref


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHANNEL_ADDRESS_REGISTRY_PATH = (
    REPO_ROOT / "data/examples/device_channel_address_registry_seed.json"
)


@dataclass(frozen=True)
class ChannelAddress:
    channel_ref: str
    controller_id: str
    protocol: str
    access: str
    table: str
    address: int
    data_type: str
    quantity: int = 1
    scale: float = 1.0
    bit_index: int | None = None
    notes: str | None = None

    def transport_ref(self) -> str:
        base = f"modbus://{self.controller_id}/{self.table}/{self.address}"
        if self.bit_index is None:
            return base
        return f"{base}/{self.bit_index}"

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "channel_ref": self.channel_ref,
            "controller_id": self.controller_id,
            "protocol": self.protocol,
            "access": self.access,
            "table": self.table,
            "address": self.address,
            "data_type": self.data_type,
            "quantity": self.quantity,
            "scale": self.scale,
            "transport_ref": self.transport_ref(),
        }
        if self.bit_index is not None:
            payload["bit_index"] = self.bit_index
        if self.notes:
            payload["notes"] = self.notes
        return payload


class ChannelAddressRegistry:
    def __init__(
        self,
        *,
        site_id: str,
        site_version: str,
        catalog_version: str,
        registry_version: str,
        channel_map_version: str,
        channels: dict[str, ChannelAddress],
    ) -> None:
        self.site_id = site_id
        self.site_version = site_version
        self.catalog_version = catalog_version
        self.registry_version = registry_version
        self.channel_map_version = channel_map_version
        self.channels = channels

    def get(self, channel_ref: str) -> ChannelAddress:
        channel = self.channels.get(channel_ref)
        if channel is None:
            raise KeyError(f"unknown channel_ref {channel_ref}")
        return channel

    def get_many(self, channel_refs: list[str]) -> list[ChannelAddress]:
        return [self.get(channel_ref) for channel_ref in channel_refs]


def load_channel_address_registry(
    path: Path = DEFAULT_CHANNEL_ADDRESS_REGISTRY_PATH,
) -> ChannelAddressRegistry:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: root must be a JSON object")

    channels: dict[str, ChannelAddress] = {}
    for item in raw.get("channels", []):
        channel_ref = item["channel_ref"]
        parsed_ref = parse_plc_tag_ref(channel_ref)
        controller_id = item["controller_id"]
        if parsed_ref.controller_id != controller_id:
            raise ValueError(
                f"{path}: controller mismatch for {channel_ref}: {parsed_ref.controller_id} != {controller_id}"
            )

        channel = ChannelAddress(
            channel_ref=channel_ref,
            controller_id=controller_id,
            protocol=item["protocol"],
            access=item["access"],
            table=item["table"],
            address=item["address"],
            data_type=item["data_type"],
            quantity=item.get("quantity", 1),
            scale=item.get("scale", 1.0),
            bit_index=item.get("bit_index"),
            notes=item.get("notes"),
        )
        if channel.channel_ref in channels:
            raise ValueError(f"{path}: duplicate channel_ref {channel.channel_ref}")
        channels[channel.channel_ref] = channel

    return ChannelAddressRegistry(
        site_id=raw["site_id"],
        site_version=raw["site_version"],
        catalog_version=raw["catalog_version"],
        registry_version=raw["registry_version"],
        channel_map_version=raw["channel_map_version"],
        channels=channels,
    )

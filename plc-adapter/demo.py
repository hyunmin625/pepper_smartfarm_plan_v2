#!/usr/bin/env python3
"""Small demo for the plc-adapter device profile abstraction."""

from __future__ import annotations

import json

from plc_adapter.channel_address_registry import load_channel_address_registry
from plc_adapter.codecs import CodecRegistry
from plc_adapter.device_catalog import load_device_catalog
from plc_adapter.device_profiles import load_profile_registry
from plc_adapter.plc_tag_modbus_tcp import PlcTagModbusTcpAdapter
from plc_adapter.resolver import DeviceCommandResolver
from plc_adapter.site_overrides import load_site_override_registry
from plc_adapter.transports import InMemoryPlcTagTransport


def main() -> None:
    catalog = load_device_catalog()
    registry = load_profile_registry()
    site_overrides = load_site_override_registry()
    channel_addresses = load_channel_address_registry()
    resolver = DeviceCommandResolver(
        catalog=catalog,
        profiles=registry,
        site_overrides=site_overrides,
    )
    transport = InMemoryPlcTagTransport(
        write_failures_before_success={"placeholder://gh-01-main-plc": 1}
    )
    adapter = PlcTagModbusTcpAdapter(
        registry=registry,
        resolver=resolver,
        transport=transport,
        channel_addresses=channel_addresses,
        codec_registry=CodecRegistry(),
        max_retries=1,
    )
    result = {
        "catalog_version": catalog.catalog_version,
        "registry_version": registry.registry_version,
        "site_version": site_overrides.site_version,
        "channel_map_version": channel_addresses.channel_map_version,
        "adapter_health_before": adapter.health(),
        "fan_command": adapter.write_device_command(
            device_id="gh-01-zone-a--circulation-fan--01",
            action_type="adjust_fan",
            parameters={"run_state": "on", "speed_pct": 55},
        ),
        "source_water_command": adapter.write_device_command(
            device_id="gh-01-nutrient-room--source-water-valve--01",
            action_type="pause_automation",
            parameters={"run_state": "closed"},
        ),
        "adapter_health_after": adapter.health(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

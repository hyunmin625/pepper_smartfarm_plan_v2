#!/usr/bin/env python3
"""Validate the optional pymodbus transport path with a fake Modbus client."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "plc-adapter"))

from plc_adapter.channel_address_registry import load_channel_address_registry  # noqa: E402
from plc_adapter.codecs import CodecRegistry  # noqa: E402
from plc_adapter.device_catalog import load_device_catalog  # noqa: E402
from plc_adapter.device_profiles import load_profile_registry  # noqa: E402
from plc_adapter.plc_tag_modbus_tcp import PlcTagModbusTcpAdapter  # noqa: E402
from plc_adapter.resolver import DeviceCommandResolver  # noqa: E402
from plc_adapter.site_overrides import load_site_override_registry  # noqa: E402
from plc_adapter.transports import ModbusTcpEndpoint, PymodbusTcpTransport  # noqa: E402


class FakeResponse:
    def __init__(self, *, registers: list[Any] | None = None, bits: list[Any] | None = None, error: bool = False) -> None:
        self.registers = registers or []
        self.bits = bits or []
        self._error = error

    def isError(self) -> bool:  # noqa: N802
        return self._error


@dataclass
class FakeClientConfig:
    remaining_write_timeouts: int = 0
    always_timeout: bool = False


class FakeModbusTcpClient:
    def __init__(self, config: ModbusTcpEndpoint, behavior: FakeClientConfig) -> None:
        self.config = config
        self.behavior = behavior
        self.connected = False
        self.storage: dict[tuple[str, int], Any] = {}
        self.write_calls = 0

    def connect(self) -> bool:
        self.connected = True
        return True

    def close(self) -> None:
        self.connected = False

    def write_register(self, address: int, value: int, **kwargs: Any) -> FakeResponse:
        self._maybe_timeout()
        self.storage[("holding_register", address)] = value
        return FakeResponse()

    def write_coil(self, address: int, value: bool, **kwargs: Any) -> FakeResponse:
        self._maybe_timeout()
        self.storage[("coil", address)] = value
        return FakeResponse()

    def read_input_registers(self, address: int, count: int = 1, **kwargs: Any) -> FakeResponse:
        value = self.storage.get(("input_register", address))
        return FakeResponse(registers=[value])

    def read_holding_registers(self, address: int, count: int = 1, **kwargs: Any) -> FakeResponse:
        value = self.storage.get(("holding_register", address))
        return FakeResponse(registers=[value])

    def read_discrete_inputs(self, address: int, count: int = 1, **kwargs: Any) -> FakeResponse:
        value = self.storage.get(("discrete_input", address))
        return FakeResponse(bits=[value])

    def read_coils(self, address: int, count: int = 1, **kwargs: Any) -> FakeResponse:
        value = self.storage.get(("coil", address))
        return FakeResponse(bits=[value])

    def _maybe_timeout(self) -> None:
        self.write_calls += 1
        if self.behavior.always_timeout:
            raise TimeoutError(f"write_timeout {self.config.endpoint}")
        if self.behavior.remaining_write_timeouts > 0:
            self.behavior.remaining_write_timeouts -= 1
            raise TimeoutError(f"write_timeout {self.config.endpoint}")


def build_factory(behavior_map: dict[str, FakeClientConfig]):
    def factory(config: ModbusTcpEndpoint) -> FakeModbusTcpClient:
        return FakeModbusTcpClient(config, behavior_map.get(config.endpoint, FakeClientConfig()))

    return factory


def build_adapter(*, transport: PymodbusTcpTransport) -> PlcTagModbusTcpAdapter:
    catalog = load_device_catalog()
    registry = load_profile_registry()
    site_overrides = load_site_override_registry()
    resolver = DeviceCommandResolver(
        catalog=catalog,
        profiles=registry,
        site_overrides=site_overrides,
    )
    return PlcTagModbusTcpAdapter(
        registry=registry,
        resolver=resolver,
        transport=transport,
        channel_addresses=load_channel_address_registry(),
        codec_registry=CodecRegistry(),
        max_retries=1,
    )


def main() -> int:
    main_endpoint = "modbus-tcp://127.0.0.1:502?unit_id=1&timeout=1.0"
    dry_endpoint = "modbus-tcp://127.0.0.1:503?unit_id=2&timeout=1.0"
    os.environ["PLC_ENDPOINT_GH_01_MAIN_PLC"] = main_endpoint
    os.environ["PLC_ENDPOINT_GH_01_DRY_PLC"] = dry_endpoint

    success_transport = PymodbusTcpTransport(
        client_factory=build_factory(
            {
                main_endpoint: FakeClientConfig(remaining_write_timeouts=1),
                dry_endpoint: FakeClientConfig(),
            }
        )
    )
    success_adapter = build_adapter(transport=success_transport)

    fan_result = success_adapter.write_device_command(
        device_id="gh-01-zone-a--circulation-fan--01",
        action_type="adjust_fan",
        parameters={"run_state": "on", "speed_pct": 55},
    )
    source_water_result = success_adapter.write_device_command(
        device_id="gh-01-nutrient-room--source-water-valve--01",
        action_type="pause_automation",
        parameters={"run_state": "closed"},
    )

    timeout_transport = PymodbusTcpTransport(
        client_factory=build_factory({main_endpoint: FakeClientConfig(always_timeout=True)})
    )
    timeout_adapter = build_adapter(transport=timeout_transport)
    timeout_result = timeout_adapter.write_device_command(
        device_id="gh-01-zone-b--heater--01",
        action_type="adjust_heating",
        parameters={"run_state": "on", "stage": 2},
    )

    errors: list[str] = []
    if fan_result["status"] != "acknowledged":
        errors.append("fan_result not acknowledged")
    if source_water_result["status"] != "acknowledged":
        errors.append("source_water_result not acknowledged")
    if timeout_result["status"] != "timeout":
        errors.append("timeout_result did not timeout")
    if success_transport.health()["connect_count"] < 2:
        errors.append("expected reconnect/connect events on success transport")
    if fan_result["latency_ms"] < 1 or source_water_result["latency_ms"] < 1 or timeout_result["latency_ms"] < 1:
        errors.append("latency_ms must be measured as a positive value")
    if fan_result["payload"]["transport_write_values"] != {"modbus://gh-01-main-plc/holding_register/40003": 55}:
        errors.append("fan transport write values mismatch")
    if source_water_result["payload"]["transport_write_values"] != {
        "modbus://gh-01-main-plc/holding_register/40002": False
    }:
        errors.append("source water transport write values mismatch")

    summary = {
        "fan_status": fan_result["status"],
        "source_water_status": source_water_result["status"],
        "timeout_status": timeout_result["status"],
        "success_transport_health": success_transport.health(),
        "timeout_transport_health": timeout_transport.health(),
        "errors": errors,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

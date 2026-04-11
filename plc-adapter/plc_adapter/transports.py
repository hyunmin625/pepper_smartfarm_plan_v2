from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit


@dataclass
class PlcTagTransportHealth:
    status: str
    connected_endpoints: int
    connect_count: int
    write_count: int
    read_count: int
    last_error: str | None = None


@dataclass(frozen=True)
class ModbusTcpEndpoint:
    endpoint: str
    host: str
    port: int
    unit_id: int
    timeout_seconds: float


@dataclass(frozen=True)
class ParsedTransportRef:
    controller_id: str
    table: str
    address: int
    bit_index: int | None = None


def parse_modbus_tcp_endpoint(endpoint: str) -> ModbusTcpEndpoint:
    parsed = urlsplit(endpoint)
    if parsed.scheme != "modbus-tcp":
        raise ValueError(f"unsupported endpoint scheme {parsed.scheme!r}")
    if not parsed.hostname:
        raise ValueError(f"endpoint host is required: {endpoint}")
    query = parse_qs(parsed.query)
    unit_id = int(query.get("unit_id", query.get("slave", ["1"]))[0])
    timeout_seconds = float(query.get("timeout", ["2.0"])[0])
    return ModbusTcpEndpoint(
        endpoint=endpoint,
        host=parsed.hostname,
        port=parsed.port or 502,
        unit_id=unit_id,
        timeout_seconds=timeout_seconds,
    )


def parse_transport_ref(ref: str) -> ParsedTransportRef:
    parsed = urlsplit(ref)
    if parsed.scheme != "modbus":
        raise ValueError(f"unsupported transport ref scheme {parsed.scheme!r}")
    controller_id = parsed.netloc
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) not in {2, 3}:
        raise ValueError(f"invalid transport ref path: {ref}")
    table = parts[0]
    address = int(parts[1])
    bit_index = int(parts[2]) if len(parts) == 3 else None
    return ParsedTransportRef(
        controller_id=controller_id,
        table=table,
        address=address,
        bit_index=bit_index,
    )


def table_address_to_offset(table: str, address: int) -> int:
    base_by_table = {
        "holding_register": 40001,
        "input_register": 30001,
        "discrete_input": 10001,
        "coil": 1,
    }
    if table not in base_by_table:
        raise ValueError(f"unsupported modbus table {table}")
    offset = address - base_by_table[table]
    if offset < 0:
        raise ValueError(f"{table} address {address} is below expected base {base_by_table[table]}")
    return offset


class PlcTagTransport(ABC):
    @abstractmethod
    def connect(self, endpoint: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self, endpoint: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_connected(self, endpoint: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def write(
        self,
        *,
        endpoint: str,
        write_values: dict[str, Any],
        mirror_read_values: dict[str, Any],
        timeout_ms: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self, *, endpoint: str, refs: list[str], timeout_ms: int) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict[str, Any]:
        raise NotImplementedError


class InMemoryPlcTagTransport(PlcTagTransport):
    def __init__(
        self,
        *,
        write_failures_before_success: dict[str, int] | None = None,
        read_failures_before_success: dict[str, int] | None = None,
    ) -> None:
        self.connected_endpoints: set[str] = set()
        self.channel_state: dict[str, dict[str, Any]] = defaultdict(dict)
        self.connect_count = 0
        self.write_count = 0
        self.read_count = 0
        self.last_error: str | None = None
        self.write_failures_before_success = dict(write_failures_before_success or {})
        self.read_failures_before_success = dict(read_failures_before_success or {})

    def connect(self, endpoint: str) -> None:
        self.connected_endpoints.add(endpoint)
        self.connect_count += 1
        self.last_error = None

    def disconnect(self, endpoint: str) -> None:
        self.connected_endpoints.discard(endpoint)

    def is_connected(self, endpoint: str) -> bool:
        return endpoint in self.connected_endpoints

    def write(
        self,
        *,
        endpoint: str,
        write_values: dict[str, Any],
        mirror_read_values: dict[str, Any],
        timeout_ms: int,
    ) -> None:
        if not self.is_connected(endpoint):
            self.last_error = f"endpoint_not_connected {endpoint}"
            raise ConnectionError(self.last_error)

        remaining_failures = self.write_failures_before_success.get(endpoint, 0)
        if remaining_failures > 0:
            self.write_failures_before_success[endpoint] = remaining_failures - 1
            self.last_error = f"write_timeout {endpoint} timeout_ms={timeout_ms}"
            raise TimeoutError(self.last_error)

        self.write_count += 1
        self.channel_state[endpoint].update(write_values)
        self.channel_state[endpoint].update(mirror_read_values)
        self.last_error = None

    def read(self, *, endpoint: str, refs: list[str], timeout_ms: int) -> dict[str, Any]:
        if not self.is_connected(endpoint):
            self.last_error = f"endpoint_not_connected {endpoint}"
            raise ConnectionError(self.last_error)

        remaining_failures = self.read_failures_before_success.get(endpoint, 0)
        if remaining_failures > 0:
            self.read_failures_before_success[endpoint] = remaining_failures - 1
            self.last_error = f"read_timeout {endpoint} timeout_ms={timeout_ms}"
            raise TimeoutError(self.last_error)

        self.read_count += 1
        self.last_error = None
        return {ref: self.channel_state[endpoint].get(ref) for ref in refs}

    def health(self) -> dict[str, Any]:
        status = "ok" if self.last_error is None else "degraded"
        return PlcTagTransportHealth(
            status=status,
            connected_endpoints=len(self.connected_endpoints),
            connect_count=self.connect_count,
            write_count=self.write_count,
            read_count=self.read_count,
            last_error=self.last_error,
        ).__dict__


class PymodbusTcpTransport(PlcTagTransport):
    def __init__(
        self,
        *,
        client_factory: Callable[[ModbusTcpEndpoint], Any] | None = None,
    ) -> None:
        self.client_factory = client_factory or self._default_client_factory
        self.clients: dict[str, Any] = {}
        self.shadow_state: dict[str, dict[str, Any]] = defaultdict(dict)
        self.connect_count = 0
        self.write_count = 0
        self.read_count = 0
        self.last_error: str | None = None

    def connect(self, endpoint: str) -> None:
        config = parse_modbus_tcp_endpoint(endpoint)
        try:
            client = self.client_factory(config)
            connected = client.connect()
            if connected is False:
                self.last_error = f"connect_failed {endpoint}"
                raise ConnectionError(self.last_error)
            self.clients[endpoint] = client
            self.connect_count += 1
            self.last_error = None
        except Exception as exc:
            self.last_error = str(exc)
            raise

    def disconnect(self, endpoint: str) -> None:
        client = self.clients.pop(endpoint, None)
        if client is not None and hasattr(client, "close"):
            client.close()

    def is_connected(self, endpoint: str) -> bool:
        client = self.clients.get(endpoint)
        if client is None:
            return False
        return bool(getattr(client, "connected", True))

    def write(
        self,
        *,
        endpoint: str,
        write_values: dict[str, Any],
        mirror_read_values: dict[str, Any],
        timeout_ms: int,
    ) -> None:
        try:
            client = self._require_client(endpoint)
            config = parse_modbus_tcp_endpoint(endpoint)
            for ref, value in write_values.items():
                parsed = parse_transport_ref(ref)
                offset = table_address_to_offset(parsed.table, parsed.address)
                self._write_single(
                    client=client,
                    config=config,
                    parsed_ref=parsed,
                    offset=offset,
                    value=value,
                )
            self.shadow_state[endpoint].update(mirror_read_values)
            self.write_count += 1
            self.last_error = None
        except Exception as exc:
            self.last_error = str(exc)
            raise

    def read(self, *, endpoint: str, refs: list[str], timeout_ms: int) -> dict[str, Any]:
        try:
            client = self._require_client(endpoint)
            config = parse_modbus_tcp_endpoint(endpoint)
            result: dict[str, Any] = {}
            for ref in refs:
                parsed = parse_transport_ref(ref)
                offset = table_address_to_offset(parsed.table, parsed.address)
                value = self._read_single(
                    client=client,
                    config=config,
                    parsed_ref=parsed,
                    offset=offset,
                )
                if value is None and ref in self.shadow_state[endpoint]:
                    value = self.shadow_state[endpoint][ref]
                result[ref] = value
            self.read_count += 1
            self.last_error = None
            return result
        except Exception as exc:
            self.last_error = str(exc)
            raise

    def health(self) -> dict[str, Any]:
        status = "ok" if self.last_error is None else "degraded"
        return PlcTagTransportHealth(
            status=status,
            connected_endpoints=len(self.clients),
            connect_count=self.connect_count,
            write_count=self.write_count,
            read_count=self.read_count,
            last_error=self.last_error,
        ).__dict__

    def _require_client(self, endpoint: str) -> Any:
        client = self.clients.get(endpoint)
        if client is None:
            self.last_error = f"endpoint_not_connected {endpoint}"
            raise ConnectionError(self.last_error)
        return client

    def _write_single(
        self,
        *,
        client: Any,
        config: ModbusTcpEndpoint,
        parsed_ref: ParsedTransportRef,
        offset: int,
        value: Any,
    ) -> None:
        if parsed_ref.table == "holding_register":
            raw_value = self._coerce_register_value(value)
            response = self._invoke_with_unit(
                client.write_register,
                address=offset,
                value=raw_value,
                unit_id=config.unit_id,
            )
            self._ensure_response_ok(response, operation="write_register")
            return
        if parsed_ref.table == "coil":
            response = self._invoke_with_unit(
                client.write_coil,
                address=offset,
                value=bool(value),
                unit_id=config.unit_id,
            )
            self._ensure_response_ok(response, operation="write_coil")
            return
        raise ValueError(f"write attempted on read-only table {parsed_ref.table}")

    def _read_single(
        self,
        *,
        client: Any,
        config: ModbusTcpEndpoint,
        parsed_ref: ParsedTransportRef,
        offset: int,
    ) -> Any:
        if parsed_ref.table == "holding_register":
            response = self._invoke_with_unit(
                client.read_holding_registers,
                address=offset,
                count=1,
                unit_id=config.unit_id,
            )
            self._ensure_response_ok(response, operation="read_holding_registers")
            return response.registers[0] if getattr(response, "registers", None) else None
        if parsed_ref.table == "input_register":
            response = self._invoke_with_unit(
                client.read_input_registers,
                address=offset,
                count=1,
                unit_id=config.unit_id,
            )
            self._ensure_response_ok(response, operation="read_input_registers")
            return response.registers[0] if getattr(response, "registers", None) else None
        if parsed_ref.table == "discrete_input":
            response = self._invoke_with_unit(
                client.read_discrete_inputs,
                address=offset,
                count=1,
                unit_id=config.unit_id,
            )
            self._ensure_response_ok(response, operation="read_discrete_inputs")
            return response.bits[0] if getattr(response, "bits", None) else None
        if parsed_ref.table == "coil":
            response = self._invoke_with_unit(
                client.read_coils,
                address=offset,
                count=1,
                unit_id=config.unit_id,
            )
            self._ensure_response_ok(response, operation="read_coils")
            return response.bits[0] if getattr(response, "bits", None) else None
        raise ValueError(f"unsupported read table {parsed_ref.table}")

    @staticmethod
    def _coerce_register_value(value: Any) -> int:
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(round(value))
        raise ValueError(f"unsupported register write type {type(value).__name__}")

    @staticmethod
    def _invoke_with_unit(method: Any, *, unit_id: int, **kwargs: Any) -> Any:
        for unit_key in ("device_id", "slave", "unit"):
            try:
                return method(**kwargs, **{unit_key: unit_id})
            except TypeError:
                continue
        return method(**kwargs)

    def _ensure_response_ok(self, response: Any, *, operation: str) -> None:
        if response is None:
            self.last_error = f"{operation}_no_response"
            raise TimeoutError(self.last_error)
        is_error = getattr(response, "isError", None)
        if callable(is_error) and is_error():
            self.last_error = f"{operation}_error"
            raise TimeoutError(self.last_error)

    @staticmethod
    def _default_client_factory(config: ModbusTcpEndpoint) -> Any:
        try:
            from pymodbus.client import ModbusTcpClient
        except ImportError as exc:  # pragma: no cover - depends on optional dependency
            raise RuntimeError("pymodbus is not installed") from exc
        return ModbusTcpClient(host=config.host, port=config.port, timeout=config.timeout_seconds)

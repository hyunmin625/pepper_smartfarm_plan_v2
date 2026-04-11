from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass
class PlcTagTransportHealth:
    status: str
    connected_endpoints: int
    connect_count: int
    write_count: int
    read_count: int
    last_error: str | None = None


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

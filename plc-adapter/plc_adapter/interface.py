from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .device_profiles import DeviceProfile


@dataclass
class CommandRequest:
    device_id: str
    profile_id: str
    action_type: str
    parameters: dict[str, Any]
    request_id: str | None = None


@dataclass
class CommandResult:
    request_id: str
    device_id: str
    profile_id: str
    status: str
    payload: dict[str, Any]
    readback: dict[str, Any]
    latency_ms: int
    failure_reason: str | None = None


class PlcAdapterInterface(ABC):
    @abstractmethod
    def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def health(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def validate_command(
        self,
        *,
        profile_id: str,
        action_type: str,
        parameters: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def build_command_payload(
        self,
        *,
        device_id: str,
        profile: DeviceProfile,
        action_type: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def write_command(
        self,
        *,
        device_id: str,
        profile_id: str,
        action_type: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def readback(self, *, device_id: str, profile_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def evaluate_ack(
        self,
        *,
        profile_id: str,
        readback: dict[str, Any],
        expected_parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        raise NotImplementedError

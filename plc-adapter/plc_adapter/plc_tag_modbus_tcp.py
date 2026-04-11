from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from .channel_address_registry import ChannelAddressRegistry, load_channel_address_registry
from .codecs import CodecRegistry
from .device_profiles import DeviceProfileRegistry
from .interface import CommandResult, PlcAdapterInterface
from .resolver import DeviceCommandResolver
from .runtime_config import RuntimeEndpointResolver
from .transports import PlcTagTransport


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PlcTagModbusTcpAdapter(PlcAdapterInterface):
    def __init__(
        self,
        *,
        registry: DeviceProfileRegistry,
        resolver: DeviceCommandResolver,
        transport: PlcTagTransport,
        channel_addresses: ChannelAddressRegistry | None = None,
        codec_registry: CodecRegistry | None = None,
        runtime_endpoint_resolver: RuntimeEndpointResolver | None = None,
        write_timeout_ms: int = 2_000,
        read_timeout_ms: int = 2_000,
        max_retries: int = 1,
    ) -> None:
        self.registry = registry
        self.resolver = resolver
        self.transport = transport
        self.channel_addresses = channel_addresses or load_channel_address_registry()
        self.codec_registry = codec_registry or CodecRegistry()
        self.runtime_endpoint_resolver = runtime_endpoint_resolver or RuntimeEndpointResolver()
        self.write_timeout_ms = write_timeout_ms
        self.read_timeout_ms = read_timeout_ms
        self.max_retries = max_retries

    def connect(self) -> None:
        for controller in self.resolver.site_overrides.controllers.values():
            resolved_endpoint = self.runtime_endpoint_resolver.resolve(
                controller_id=controller.controller_id,
                configured_endpoint=controller.endpoint,
            )
            if not self.transport.is_connected(resolved_endpoint):
                self.transport.connect(resolved_endpoint)

    def health(self) -> dict[str, Any]:
        transport_health = self.transport.health()
        return {
            "status": transport_health.get("status", "unknown"),
            "transport": transport_health,
            "max_retries": self.max_retries,
            "write_timeout_ms": self.write_timeout_ms,
            "read_timeout_ms": self.read_timeout_ms,
        }

    def validate_command(
        self,
        *,
        profile_id: str,
        action_type: str,
        parameters: dict[str, Any],
    ) -> None:
        profile = self.registry.get(profile_id)
        profile.validate_parameters(action_type, parameters)

    def build_command_payload(
        self,
        *,
        device_id: str,
        profile,
        action_type: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        self.validate_command(
            profile_id=profile.profile_id,
            action_type=action_type,
            parameters=parameters,
        )
        context = self.resolver.resolve(device_id)
        if context.profile.profile_id != profile.profile_id:
            raise ValueError(
                f"{device_id}: resolved profile {context.profile.profile_id} does not match requested profile {profile.profile_id}"
            )
        encoded = self.codec_registry.encode(
            context=context,
            action_type=action_type,
            parameters=parameters,
            encoder_name=context.command_encoder,
        )
        runtime_endpoint = self.runtime_endpoint_resolver.describe(
            controller_id=context.controller.controller_id,
            configured_endpoint=context.controller.endpoint,
        )
        write_channel_address = self.channel_addresses.get(context.write_channel_ref)
        read_channel_addresses = self.channel_addresses.get_many(context.read_channel_refs)
        transport_write_values = self._map_values_to_transport_refs(
            values=encoded.write_values,
        )
        transport_mirror_read_values = self._map_values_to_transport_refs(
            values=encoded.mirror_read_values,
        )
        return {
            "device_id": device_id,
            "profile_id": profile.profile_id,
            "device_type": profile.device_type,
            "protocol": profile.protocol,
            "action_type": action_type,
            "parameters": parameters,
            "issued_at": utc_now(),
            "controller_id": context.controller.controller_id,
            "controller_endpoint": context.controller.endpoint,
            "controller_endpoint_resolved": runtime_endpoint["resolved_endpoint"],
            "controller_endpoint_env_key": runtime_endpoint["env_key"],
            "controller_endpoint_override_active": runtime_endpoint["override_active"],
            "write_channel_ref": context.write_channel_ref,
            "write_channel": context.write_channel.to_dict(),
            "write_channel_address": write_channel_address.to_dict(),
            "read_channel_refs": context.read_channel_refs,
            "read_channels": [channel.to_dict() for channel in context.read_channels],
            "read_channel_addresses": [address.to_dict() for address in read_channel_addresses],
            "command_encoder": context.command_encoder,
            "readback_decoder": context.readback_decoder,
            "write_values": encoded.write_values,
            "mirror_read_values": encoded.mirror_read_values,
            "transport_write_values": transport_write_values,
            "transport_mirror_read_values": transport_mirror_read_values,
            "transport_read_refs": [address.transport_ref() for address in read_channel_addresses],
        }

    def write_command(
        self,
        *,
        device_id: str,
        profile_id: str,
        action_type: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        profile = self.registry.get(profile_id)
        payload = self.build_command_payload(
            device_id=device_id,
            profile=profile,
            action_type=action_type,
            parameters=parameters,
        )
        endpoint = payload["controller_endpoint_resolved"]
        start_time = perf_counter()

        last_error: str | None = None
        for attempt in range(self.max_retries + 1):
            try:
                self._ensure_connected(endpoint)
                self.transport.write(
                    endpoint=endpoint,
                    write_values=payload["transport_write_values"],
                    mirror_read_values=payload["transport_mirror_read_values"],
                    timeout_ms=self.write_timeout_ms,
                )
                readback = self.readback(device_id=device_id, profile_id=profile_id)
                ack_ok, failure_reason = self.evaluate_ack(
                    profile_id=profile_id,
                    readback=readback,
                    expected_parameters=parameters,
                )
                status = "acknowledged" if ack_ok else "fault"
                result = CommandResult(
                    request_id=f"plc-tag-{device_id}",
                    device_id=device_id,
                    profile_id=profile_id,
                    status=status,
                    payload=payload,
                    readback=readback,
                    latency_ms=max(1, int((perf_counter() - start_time) * 1000)),
                    failure_reason=failure_reason,
                )
                return result.__dict__
            except (TimeoutError, ConnectionError) as exc:
                last_error = str(exc)
                self.transport.disconnect(endpoint)
                if attempt >= self.max_retries:
                    break

        return CommandResult(
            request_id=f"plc-tag-{device_id}",
            device_id=device_id,
            profile_id=profile_id,
            status="timeout",
            payload=payload,
            readback={},
            latency_ms=max(1, int((perf_counter() - start_time) * 1000)),
            failure_reason=last_error,
        ).__dict__

    def write_device_command(
        self,
        *,
        device_id: str,
        action_type: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        context = self.resolver.resolve(device_id)
        return self.write_command(
            device_id=device_id,
            profile_id=context.profile.profile_id,
            action_type=action_type,
            parameters=parameters,
        )

    def readback(self, *, device_id: str, profile_id: str) -> dict[str, Any]:
        context = self.resolver.resolve(device_id)
        endpoint = self.runtime_endpoint_resolver.resolve(
            controller_id=context.controller.controller_id,
            configured_endpoint=context.controller.endpoint,
        )
        read_channel_addresses = self.channel_addresses.get_many(context.read_channel_refs)
        transport_refs = [address.transport_ref() for address in read_channel_addresses]
        raw_transport_values = self.transport.read(
            endpoint=endpoint,
            refs=transport_refs,
            timeout_ms=self.read_timeout_ms,
        )
        raw_values = {
            address.channel_ref: raw_transport_values.get(address.transport_ref())
            for address in read_channel_addresses
        }
        decoded = self.codec_registry.decode(
            context=context,
            raw_values=raw_values,
            decoder_name=context.readback_decoder,
        )
        decoded["read_at"] = utc_now()
        return decoded

    def evaluate_ack(
        self,
        *,
        profile_id: str,
        readback: dict[str, Any],
        expected_parameters: dict[str, Any],
    ) -> tuple[bool, str | None]:
        profile = self.registry.get(profile_id)
        return profile.evaluate_ack(readback=readback, expected_parameters=expected_parameters)

    def _ensure_connected(self, endpoint: str) -> None:
        if not self.transport.is_connected(endpoint):
            self.transport.connect(endpoint)

    def _map_values_to_transport_refs(self, *, values: dict[str, Any]) -> dict[str, Any]:
        mapped: dict[str, Any] = {}
        for channel_ref, value in values.items():
            mapped[self.channel_addresses.get(channel_ref).transport_ref()] = value
        return mapped

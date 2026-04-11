from __future__ import annotations

from dataclasses import dataclass

from .channel_refs import PlcTagChannelRef, parse_plc_tag_ref
from .device_catalog import DeviceCatalog, DeviceCatalogEntry
from .device_profiles import DeviceProfile, DeviceProfileRegistry
from .site_overrides import ControllerBinding, SiteDeviceBinding, SiteOverrideRegistry


@dataclass
class ResolvedDeviceContext:
    device: DeviceCatalogEntry
    profile: DeviceProfile
    binding: SiteDeviceBinding
    controller: ControllerBinding

    @property
    def write_channel_ref(self) -> str:
        return self.binding.write_channel_ref

    @property
    def read_channel_refs(self) -> list[str]:
        return self.binding.read_channel_refs

    @property
    def write_channel(self) -> PlcTagChannelRef:
        return parse_plc_tag_ref(self.binding.write_channel_ref)

    @property
    def read_channels(self) -> list[PlcTagChannelRef]:
        return [parse_plc_tag_ref(ref) for ref in self.binding.read_channel_refs]

    @property
    def command_encoder(self) -> str:
        return self.binding.command_encoder or self.profile.mapping["command_encoder"]

    @property
    def readback_decoder(self) -> str:
        return self.binding.readback_decoder or self.profile.mapping["readback_decoder"]


class DeviceCommandResolver:
    def __init__(
        self,
        *,
        catalog: DeviceCatalog,
        profiles: DeviceProfileRegistry,
        site_overrides: SiteOverrideRegistry,
    ) -> None:
        self.catalog = catalog
        self.profiles = profiles
        self.site_overrides = site_overrides

    def resolve(self, device_id: str) -> ResolvedDeviceContext:
        device = self.catalog.get(device_id)
        profile = self.profiles.get(device.profile_id)
        binding = self.site_overrides.get_binding(device_id)
        controller = self.site_overrides.get_controller(binding.controller_id)

        if binding.profile_id != device.profile_id:
            raise ValueError(
                f"{device_id}: site binding profile {binding.profile_id} does not match catalog profile {device.profile_id}"
            )
        if profile.profile_id != device.profile_id:
            raise ValueError(
                f"{device_id}: registry profile {profile.profile_id} does not match catalog profile {device.profile_id}"
            )
        if binding.protocol != device.protocol:
            raise ValueError(f"{device_id}: binding protocol {binding.protocol} does not match catalog protocol {device.protocol}")
        if controller.protocol != binding.protocol:
            raise ValueError(
                f"{device_id}: controller protocol {controller.protocol} does not match binding protocol {binding.protocol}"
            )
        if self._write_channel_controller_mismatch(binding.write_channel_ref, controller.controller_id):
            raise ValueError(
                f"{device_id}: write_channel_ref controller does not match controller_id {controller.controller_id}"
            )
        for read_channel_ref in binding.read_channel_refs:
            if self._write_channel_controller_mismatch(read_channel_ref, controller.controller_id):
                raise ValueError(
                    f"{device_id}: read_channel_ref controller does not match controller_id {controller.controller_id}"
                )

        return ResolvedDeviceContext(
            device=device,
            profile=profile,
            binding=binding,
            controller=controller,
        )

    @staticmethod
    def _write_channel_controller_mismatch(channel_ref: str, controller_id: str) -> bool:
        parsed = parse_plc_tag_ref(channel_ref)
        return parsed.controller_id != controller_id

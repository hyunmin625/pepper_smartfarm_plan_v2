from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .resolver import ResolvedDeviceContext


@dataclass
class EncodedCommand:
    write_values: dict[str, Any]
    mirror_read_values: dict[str, Any]


CommandEncoder = Callable[[ResolvedDeviceContext, str, dict[str, Any]], EncodedCommand]
ReadbackDecoder = Callable[[ResolvedDeviceContext, dict[str, Any]], dict[str, Any]]


def encode_fan_percent(
    context: ResolvedDeviceContext,
    action_type: str,
    parameters: dict[str, Any],
) -> EncodedCommand:
    return _encode_single_write_with_expected(context, action_type, parameters)


def encode_position(
    context: ResolvedDeviceContext,
    action_type: str,
    parameters: dict[str, Any],
) -> EncodedCommand:
    return _encode_single_write_with_expected(context, action_type, parameters, default_run_state="moving")


def encode_binary_open_close(
    context: ResolvedDeviceContext,
    action_type: str,
    parameters: dict[str, Any],
) -> EncodedCommand:
    return _encode_single_write_with_expected(context, action_type, parameters)


def encode_stage(
    context: ResolvedDeviceContext,
    action_type: str,
    parameters: dict[str, Any],
) -> EncodedCommand:
    return _encode_single_write_with_expected(context, action_type, parameters)


def encode_recipe(
    context: ResolvedDeviceContext,
    action_type: str,
    parameters: dict[str, Any],
) -> EncodedCommand:
    return _encode_single_write_with_expected(
        context,
        action_type,
        parameters,
        expected_field_overrides={"recipe_stage": parameters.get("recipe_id"), "run_state": "running"},
    )


def decode_generic_readback(
    context: ResolvedDeviceContext,
    raw_values: dict[str, Any],
) -> dict[str, Any]:
    decoded = {
        "device_id": context.device.device_id,
        "profile_id": context.profile.profile_id,
        "controller_id": context.controller.controller_id,
    }
    for field, ref in zip(context.profile.readback_fields, context.read_channel_refs):
        decoded[field["field_name"]] = raw_values.get(ref)
    return decoded


def _encode_single_write_with_expected(
    context: ResolvedDeviceContext,
    action_type: str,
    parameters: dict[str, Any],
    *,
    default_run_state: str | None = None,
    expected_field_overrides: dict[str, Any] | None = None,
) -> EncodedCommand:
    mirror_read_values: dict[str, Any] = {}
    expected_field_overrides = expected_field_overrides or {}

    for field, ref in zip(context.profile.readback_fields, context.read_channel_refs):
        field_name = field["field_name"]
        if field_name in expected_field_overrides:
            mirror_read_values[ref] = expected_field_overrides[field_name]
        elif field_name in parameters:
            mirror_read_values[ref] = parameters[field_name]
        elif field_name == "run_state" and default_run_state is not None:
            mirror_read_values[ref] = default_run_state
        elif field_name == "fault_code":
            mirror_read_values[ref] = ""
        elif field_name in {"speed_pct", "position_pct", "dose_pct", "stage"}:
            mirror_read_values[ref] = parameters.get(field_name, 0)
        else:
            mirror_read_values[ref] = None

    return EncodedCommand(
        write_values={
            context.write_channel_ref: {
                "action_type": action_type,
                "parameters": parameters,
            }
        },
        mirror_read_values=mirror_read_values,
    )


class CodecRegistry:
    def __init__(self) -> None:
        self.command_encoders: dict[str, CommandEncoder] = {
            "fan_percent_encoder_v1": encode_fan_percent,
            "position_encoder_v1": encode_position,
            "binary_open_close_encoder_v1": encode_binary_open_close,
            "stage_encoder_v1": encode_stage,
            "co2_percent_encoder_v1": encode_fan_percent,
            "recipe_encoder_v1": encode_recipe,
        }
        self.readback_decoders: dict[str, ReadbackDecoder] = {
            "fan_readback_decoder_v1": decode_generic_readback,
            "position_readback_decoder_v1": decode_generic_readback,
            "binary_readback_decoder_v1": decode_generic_readback,
            "stage_readback_decoder_v1": decode_generic_readback,
            "co2_readback_decoder_v1": decode_generic_readback,
            "recipe_readback_decoder_v1": decode_generic_readback,
        }

    def encode(
        self,
        *,
        context: ResolvedDeviceContext,
        action_type: str,
        parameters: dict[str, Any],
        encoder_name: str,
    ) -> EncodedCommand:
        encoder = self.command_encoders.get(encoder_name)
        if encoder is None:
            raise KeyError(f"unknown command encoder {encoder_name}")
        return encoder(context, action_type, parameters)

    def decode(
        self,
        *,
        context: ResolvedDeviceContext,
        raw_values: dict[str, Any],
        decoder_name: str,
    ) -> dict[str, Any]:
        decoder = self.readback_decoders.get(decoder_name)
        if decoder is None:
            raise KeyError(f"unknown readback decoder {decoder_name}")
        return decoder(context, raw_values)

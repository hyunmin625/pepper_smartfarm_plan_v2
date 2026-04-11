#!/usr/bin/env python3
"""Validate sensor-ingestor config against the sensor catalog."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = Path("data/examples/sensor_ingestor_config_seed.json")
ALLOWED_PROTOCOLS = {
    "rs485_modbus_rtu",
    "pulse_counter",
    "rtsp_onvif",
    "manual_batch_import",
    "plc_tag_modbus_tcp",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a JSON object")
    return data


def require_string(value: Any, prefix: str, field_name: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix}: {field_name} must be a non-empty string")


def require_bool(value: Any, prefix: str, field_name: str, errors: list[str]) -> None:
    if not isinstance(value, bool):
        errors.append(f"{prefix}: {field_name} must be a boolean")


def require_positive_int(value: Any, prefix: str, field_name: str, errors: list[str], *, allow_zero: bool = False) -> None:
    minimum = 0 if allow_zero else 1
    if not isinstance(value, int) or value < minimum:
        errors.append(f"{prefix}: {field_name} must be an integer >= {minimum}")


def require_string_array(value: Any, prefix: str, field_name: str, errors: list[str], *, allow_empty: bool = False) -> list[str]:
    items: list[str] = []
    if not isinstance(value, list):
        errors.append(f"{prefix}: {field_name} must be an array")
        return items
    if not allow_empty and not value:
        errors.append(f"{prefix}: {field_name} must be a non-empty array")
        return items
    for index, item in enumerate(value, start=1):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{prefix}: {field_name}[{index}] must be a non-empty string")
            continue
        items.append(item)
    return items


def as_object_list(value: Any, field_name: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"config: {field_name} must be an array")
        return []
    objects: list[dict[str, Any]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            errors.append(f"config: {field_name}[{index}] must be an object")
            continue
        objects.append(item)
    return objects


def resolve_catalog_path(config_path: Path, catalog_ref: str) -> Path:
    ref_path = Path(catalog_ref)
    if ref_path.is_absolute():
        return ref_path
    candidate = config_path.parent / ref_path
    if candidate.exists():
        return candidate
    return Path(catalog_ref)


def validate_id_duplicates(items: list[dict[str, Any]], id_field: str, label: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    counter: Counter[str] = Counter()
    mapping: dict[str, dict[str, Any]] = {}
    for item in items:
        identifier = item.get(id_field)
        if isinstance(identifier, str):
            counter[identifier] += 1
            mapping[identifier] = item
    for identifier, count in sorted(counter.items()):
        if count > 1:
            errors.append(f"{label}: duplicate {id_field} {identifier}")
    return mapping


def validate_quality_rule_sets(rule_sets: list[dict[str, Any]], errors: list[str]) -> dict[str, dict[str, Any]]:
    mapping = validate_id_duplicates(rule_sets, "rule_set_id", "quality_rule_sets", errors)
    for index, rule_set in enumerate(rule_sets, start=1):
        prefix = f"quality_rule_sets[{index}]"
        require_string(rule_set.get("rule_set_id"), prefix, "rule_set_id", errors)
        applies_to = require_string_array(rule_set.get("applies_to"), prefix, "applies_to", errors)
        require_positive_int(rule_set.get("stale_after_seconds"), prefix, "stale_after_seconds", errors)
        require_positive_int(rule_set.get("bad_after_seconds"), prefix, "bad_after_seconds", errors)
        if isinstance(rule_set.get("stale_after_seconds"), int) and isinstance(rule_set.get("bad_after_seconds"), int):
            if rule_set["bad_after_seconds"] <= rule_set["stale_after_seconds"]:
                errors.append(f"{prefix}: bad_after_seconds must be greater than stale_after_seconds")
        if "flatline_window_seconds" in rule_set:
            require_positive_int(rule_set.get("flatline_window_seconds"), prefix, "flatline_window_seconds", errors)
        if "jump_threshold_pct" in rule_set:
            jump = rule_set["jump_threshold_pct"]
            if not isinstance(jump, (int, float)) or jump < 0:
                errors.append(f"{prefix}: jump_threshold_pct must be a number >= 0")
        if "allowed_range" in rule_set:
            allowed_range = rule_set["allowed_range"]
            if not isinstance(allowed_range, dict):
                errors.append(f"{prefix}: allowed_range must be an object")
            else:
                minimum = allowed_range.get("min")
                maximum = allowed_range.get("max")
                if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
                    errors.append(f"{prefix}: allowed_range.min/max must be numeric")
                elif maximum < minimum:
                    errors.append(f"{prefix}: allowed_range.max must be >= min")
        if not applies_to:
            errors.append(f"{prefix}: applies_to cannot be empty")
    return mapping


def validate_publish_targets(targets: list[dict[str, Any]], errors: list[str]) -> dict[str, dict[str, Any]]:
    mapping = validate_id_duplicates(targets, "target_id", "publish_targets", errors)
    for index, target in enumerate(targets, start=1):
        prefix = f"publish_targets[{index}]"
        for field_name in ("target_id", "target_type", "route", "payload_format"):
            require_string(target.get(field_name), prefix, field_name, errors)
    return mapping


def validate_poller_profiles(profiles: list[dict[str, Any]], errors: list[str]) -> dict[str, dict[str, Any]]:
    mapping = validate_id_duplicates(profiles, "profile_id", "poller_profiles", errors)
    for index, profile in enumerate(profiles, start=1):
        prefix = f"poller_profiles[{index}]"
        require_string(profile.get("profile_id"), prefix, "profile_id", errors)
        protocol = profile.get("protocol")
        require_string(protocol, prefix, "protocol", errors)
        if isinstance(protocol, str) and protocol not in ALLOWED_PROTOCOLS:
            errors.append(f"{prefix}: unsupported protocol {protocol}")
        require_positive_int(profile.get("poll_interval_seconds"), prefix, "poll_interval_seconds", errors)
        require_positive_int(profile.get("timeout_seconds"), prefix, "timeout_seconds", errors)
        require_positive_int(profile.get("retry_count"), prefix, "retry_count", errors, allow_zero=True)
        require_positive_int(profile.get("retry_backoff_seconds"), prefix, "retry_backoff_seconds", errors, allow_zero=True)
        require_bool(profile.get("enabled"), prefix, "enabled", errors)
    return mapping


def validate_connections(connections: list[dict[str, Any]], errors: list[str]) -> dict[str, dict[str, Any]]:
    mapping = validate_id_duplicates(connections, "connection_id", "connections", errors)
    for index, connection in enumerate(connections, start=1):
        prefix = f"connections[{index}]"
        for field_name in ("connection_id", "protocol", "transport", "endpoint_ref"):
            require_string(connection.get(field_name), prefix, field_name, errors)
        protocol = connection.get("protocol")
        if isinstance(protocol, str) and protocol not in ALLOWED_PROTOCOLS:
            errors.append(f"{prefix}: unsupported protocol {protocol}")
        require_bool(connection.get("enabled"), prefix, "enabled", errors)
    return mapping


def validate_snapshot_pipeline(snapshot_pipeline: dict[str, Any], errors: list[str]) -> None:
    prefix = "snapshot_pipeline"
    require_positive_int(snapshot_pipeline.get("snapshot_interval_seconds"), prefix, "snapshot_interval_seconds", errors)
    trend_windows = snapshot_pipeline.get("trend_windows_seconds")
    if not isinstance(trend_windows, list) or not trend_windows:
        errors.append(f"{prefix}: trend_windows_seconds must be a non-empty array")
    else:
        previous = 0
        for index, item in enumerate(trend_windows, start=1):
            if not isinstance(item, int) or item <= 0:
                errors.append(f"{prefix}: trend_windows_seconds[{index}] must be a positive integer")
                continue
            if item <= previous:
                errors.append(f"{prefix}: trend_windows_seconds must be strictly ascending")
            previous = item
    require_positive_int(snapshot_pipeline.get("raw_retention_days"), prefix, "raw_retention_days", errors)
    require_positive_int(snapshot_pipeline.get("snapshot_retention_days"), prefix, "snapshot_retention_days", errors)
    require_bool(snapshot_pipeline.get("exclude_bad_quality_from_ai"), prefix, "exclude_bad_quality_from_ai", errors)
    require_string(snapshot_pipeline.get("manual_override_topic"), prefix, "manual_override_topic", errors)


def validate_health_config(health_config: dict[str, Any], errors: list[str]) -> None:
    prefix = "health_config"
    require_positive_int(health_config.get("heartbeat_seconds"), prefix, "heartbeat_seconds", errors)
    require_positive_int(health_config.get("lag_alarm_seconds"), prefix, "lag_alarm_seconds", errors)
    require_string(health_config.get("metrics_namespace"), prefix, "metrics_namespace", errors)
    require_string(health_config.get("status_topic"), prefix, "status_topic", errors)


def validate_sensor_bindings(
    groups: list[dict[str, Any]],
    *,
    catalog_sensors: dict[str, dict[str, Any]],
    poller_profiles: dict[str, dict[str, Any]],
    connections: dict[str, dict[str, Any]],
    quality_rule_sets: dict[str, dict[str, Any]],
    publish_targets: dict[str, dict[str, Any]],
    allow_partial_coverage: bool,
    errors: list[str],
) -> tuple[int, int]:
    validate_id_duplicates(groups, "binding_group_id", "sensor_binding_groups", errors)
    coverage: Counter[str] = Counter()

    for index, group in enumerate(groups, start=1):
        prefix = f"sensor_binding_groups[{index}]"
        for field_name in (
            "binding_group_id",
            "connection_id",
            "poller_profile_id",
            "parser_id",
            "normalizer_id",
            "quality_rule_set_id",
        ):
            require_string(group.get(field_name), prefix, field_name, errors)
        require_bool(group.get("enabled"), prefix, "enabled", errors)
        sensor_ids = require_string_array(group.get("sensor_ids"), prefix, "sensor_ids", errors)
        zone_scope = require_string_array(group.get("zone_scope", []), prefix, "zone_scope", errors, allow_empty=True)
        target_ids = require_string_array(group.get("publish_targets"), prefix, "publish_targets", errors)

        connection = connections.get(group.get("connection_id"))
        profile = poller_profiles.get(group.get("poller_profile_id"))
        rule_set = quality_rule_sets.get(group.get("quality_rule_set_id"))

        if connection is None:
            errors.append(f"{prefix}: unknown connection_id {group.get('connection_id')}")
        if profile is None:
            errors.append(f"{prefix}: unknown poller_profile_id {group.get('poller_profile_id')}")
        if rule_set is None:
            errors.append(f"{prefix}: unknown quality_rule_set_id {group.get('quality_rule_set_id')}")
        if connection and profile and connection.get("protocol") != profile.get("protocol"):
            errors.append(f"{prefix}: connection protocol and poller profile protocol must match")
        for target_id in target_ids:
            if target_id not in publish_targets:
                errors.append(f"{prefix}: unknown publish target {target_id}")

        applies_to = set(rule_set.get("applies_to", [])) if rule_set else set()
        for sensor_id in sensor_ids:
            sensor = catalog_sensors.get(sensor_id)
            if sensor is None:
                errors.append(f"{prefix}: unknown sensor_id {sensor_id}")
                continue
            coverage[sensor_id] += 1
            if connection and sensor.get("protocol") != connection.get("protocol"):
                errors.append(f"{prefix}: sensor {sensor_id} protocol does not match connection protocol")
            if rule_set and sensor.get("sensor_type") not in applies_to:
                errors.append(f"{prefix}: sensor {sensor_id} type is not covered by {group.get('quality_rule_set_id')}")
            if zone_scope and sensor.get("zone_id") not in zone_scope:
                errors.append(f"{prefix}: sensor {sensor_id} zone_id is outside zone_scope")

    for sensor_id, count in sorted(coverage.items()):
        if count > 1:
            errors.append(f"sensor_binding_groups: duplicate sensor coverage {sensor_id}")

    if not allow_partial_coverage:
        for sensor_id in sorted(set(catalog_sensors) - set(coverage)):
            errors.append(f"sensor_binding_groups: missing sensor coverage {sensor_id}")

    return len(groups), len(coverage)


def validate_device_bindings(
    groups: list[dict[str, Any]],
    *,
    catalog_devices: dict[str, dict[str, Any]],
    poller_profiles: dict[str, dict[str, Any]],
    connections: dict[str, dict[str, Any]],
    publish_targets: dict[str, dict[str, Any]],
    allow_partial_coverage: bool,
    errors: list[str],
) -> tuple[int, int]:
    validate_id_duplicates(groups, "binding_group_id", "device_binding_groups", errors)
    coverage: Counter[str] = Counter()

    for index, group in enumerate(groups, start=1):
        prefix = f"device_binding_groups[{index}]"
        for field_name in (
            "binding_group_id",
            "connection_id",
            "poller_profile_id",
            "parser_id",
            "normalizer_id",
        ):
            require_string(group.get(field_name), prefix, field_name, errors)
        require_bool(group.get("enabled"), prefix, "enabled", errors)
        device_ids = require_string_array(group.get("device_ids"), prefix, "device_ids", errors)
        zone_scope = require_string_array(group.get("zone_scope", []), prefix, "zone_scope", errors, allow_empty=True)
        target_ids = require_string_array(group.get("publish_targets"), prefix, "publish_targets", errors)

        connection = connections.get(group.get("connection_id"))
        profile = poller_profiles.get(group.get("poller_profile_id"))
        if connection is None:
            errors.append(f"{prefix}: unknown connection_id {group.get('connection_id')}")
        if profile is None:
            errors.append(f"{prefix}: unknown poller_profile_id {group.get('poller_profile_id')}")
        if connection and profile and connection.get("protocol") != profile.get("protocol"):
            errors.append(f"{prefix}: connection protocol and poller profile protocol must match")
        for target_id in target_ids:
            if target_id not in publish_targets:
                errors.append(f"{prefix}: unknown publish target {target_id}")

        for device_id in device_ids:
            device = catalog_devices.get(device_id)
            if device is None:
                errors.append(f"{prefix}: unknown device_id {device_id}")
                continue
            coverage[device_id] += 1
            if connection and device.get("protocol") != connection.get("protocol"):
                errors.append(f"{prefix}: device {device_id} protocol does not match connection protocol")
            if zone_scope and device.get("zone_id") not in zone_scope:
                errors.append(f"{prefix}: device {device_id} zone_id is outside zone_scope")

    for device_id, count in sorted(coverage.items()):
        if count > 1:
            errors.append(f"device_binding_groups: duplicate device coverage {device_id}")

    if not allow_partial_coverage:
        for device_id in sorted(set(catalog_devices) - set(coverage)):
            errors.append(f"device_binding_groups: missing device coverage {device_id}")

    return len(groups), len(coverage)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--allow-partial-coverage", action="store_true")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_json(config_path)
    errors: list[str] = []

    for field_name in ("config_version", "site_id", "timezone", "catalog_ref"):
        require_string(config.get(field_name), "config", field_name, errors)

    catalog_ref = config.get("catalog_ref")
    catalog_path = resolve_catalog_path(config_path, catalog_ref) if isinstance(catalog_ref, str) else Path("")
    if not catalog_path.exists():
        errors.append(f"config: catalog_ref does not exist: {catalog_path}")
        catalog: dict[str, Any] = {"sensors": [], "devices": []}
    else:
        catalog = load_json(catalog_path)

    catalog_sensors = {item["sensor_id"]: item for item in catalog.get("sensors", []) if isinstance(item, dict) and "sensor_id" in item}
    catalog_devices = {item["device_id"]: item for item in catalog.get("devices", []) if isinstance(item, dict) and "device_id" in item}

    poller_profiles = validate_poller_profiles(as_object_list(config.get("poller_profiles"), "poller_profiles", errors), errors)
    connections = validate_connections(as_object_list(config.get("connections"), "connections", errors), errors)
    quality_rule_sets = validate_quality_rule_sets(as_object_list(config.get("quality_rule_sets"), "quality_rule_sets", errors), errors)
    publish_targets = validate_publish_targets(as_object_list(config.get("publish_targets"), "publish_targets", errors), errors)

    snapshot_pipeline = config.get("snapshot_pipeline")
    if not isinstance(snapshot_pipeline, dict):
        errors.append("config: snapshot_pipeline must be an object")
    else:
        validate_snapshot_pipeline(snapshot_pipeline, errors)

    health_config = config.get("health_config")
    if not isinstance(health_config, dict):
        errors.append("config: health_config must be an object")
    else:
        validate_health_config(health_config, errors)

    sensor_group_count, covered_sensor_count = validate_sensor_bindings(
        as_object_list(config.get("sensor_binding_groups"), "sensor_binding_groups", errors),
        catalog_sensors=catalog_sensors,
        poller_profiles=poller_profiles,
        connections=connections,
        quality_rule_sets=quality_rule_sets,
        publish_targets=publish_targets,
        allow_partial_coverage=args.allow_partial_coverage,
        errors=errors,
    )
    device_group_count, covered_device_count = validate_device_bindings(
        as_object_list(config.get("device_binding_groups"), "device_binding_groups", errors),
        catalog_devices=catalog_devices,
        poller_profiles=poller_profiles,
        connections=connections,
        publish_targets=publish_targets,
        allow_partial_coverage=args.allow_partial_coverage,
        errors=errors,
    )

    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    print(f"config_path: {config_path}")
    print(f"catalog_path: {catalog_path}")
    print(f"poller_profiles: {len(poller_profiles)}")
    print(f"connections: {len(connections)}")
    print(f"quality_rule_sets: {len(quality_rule_sets)}")
    print(f"publish_targets: {len(publish_targets)}")
    print(f"sensor_binding_groups: {sensor_group_count}")
    print(f"device_binding_groups: {device_group_count}")
    print(f"catalog_sensors: {len(catalog_sensors)}")
    print(f"catalog_devices: {len(catalog_devices)}")
    print(f"covered_sensors: {covered_sensor_count}")
    print(f"covered_devices: {covered_device_count}")
    print(f"errors: {len(errors)}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()

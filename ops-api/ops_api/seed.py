from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .bootstrap import REPO_ROOT
from .database import session_scope
from .models import DeviceRecord, PolicyRecord, SensorRecord, ZoneRecord


SENSOR_CATALOG_PATH = REPO_ROOT / "data" / "examples" / "sensor_catalog_seed.json"
DEVICE_PROFILE_PATH = REPO_ROOT / "data" / "examples" / "device_profile_registry_seed.json"
DEVICE_BINDING_PATH = REPO_ROOT / "data" / "examples" / "device_site_override_seed.json"
POLICY_RULE_PATH = REPO_ROOT / "data" / "examples" / "policy_output_validator_rules_seed.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bootstrap_reference_data(session_factory) -> None:
    catalog = _load_json(SENSOR_CATALOG_PATH)
    device_profiles = {
        entry["profile_id"]: entry
        for entry in _load_json(DEVICE_PROFILE_PATH).get("device_profiles", [])
        if isinstance(entry, dict) and entry.get("profile_id")
    }
    device_bindings = {
        entry["device_id"]: entry
        for entry in _load_json(DEVICE_BINDING_PATH).get("device_bindings", [])
        if isinstance(entry, dict) and entry.get("device_id")
    }
    policy_rules = _load_json(POLICY_RULE_PATH)

    with session_scope(session_factory) as session:
        existing_zones = {row.zone_id: row for row in session.query(ZoneRecord).all()}
        for entry in catalog.get("zones", []):
            if not isinstance(entry, dict) or not entry.get("zone_id"):
                continue
            zone_id = str(entry["zone_id"])
            record = existing_zones.get(zone_id)
            if record is None:
                record = ZoneRecord(zone_id=zone_id)
                session.add(record)
                existing_zones[zone_id] = record
            record.zone_type = str(entry.get("zone_type") or "unknown")
            record.priority = str(entry.get("priority") or "optional")
            record.description = str(entry.get("description") or "")
            record.metadata_json = json.dumps(entry, ensure_ascii=False)
        session.flush()

        existing_sensors = {row.sensor_id: row for row in session.query(SensorRecord).all()}
        for entry in catalog.get("sensors", []):
            if not isinstance(entry, dict) or not entry.get("sensor_id"):
                continue
            sensor_id = str(entry["sensor_id"])
            record = existing_sensors.get(sensor_id)
            if record is None:
                record = SensorRecord(sensor_id=sensor_id)
                session.add(record)
                existing_sensors[sensor_id] = record
            record.zone_id = str(entry.get("zone_id") or "")
            record.sensor_type = str(entry.get("sensor_type") or "unknown")
            record.measurement_fields_json = json.dumps(entry.get("measurement_fields", []), ensure_ascii=False)
            record.unit = str(entry.get("unit") or "")
            record.raw_sample_seconds = int(entry.get("raw_sample_seconds") or 0)
            record.ai_aggregation_seconds = int(entry.get("ai_aggregation_seconds") or 0)
            record.priority = str(entry.get("priority") or "optional")
            record.model_profile = str(entry.get("model_profile") or "")
            record.protocol = str(entry.get("protocol") or "")
            record.install_location = str(entry.get("install_location") or "")
            record.calibration_interval_days = int(entry.get("calibration_interval_days") or 0)
            record.redundancy_group = str(entry.get("redundancy_group") or "")
            record.quality_flags_json = json.dumps(entry.get("quality_flags", []), ensure_ascii=False)
            record.metadata_json = json.dumps(entry, ensure_ascii=False)

        existing_devices = {row.device_id: row for row in session.query(DeviceRecord).all()}
        for entry in catalog.get("devices", []):
            if not isinstance(entry, dict) or not entry.get("device_id"):
                continue
            device_id = str(entry["device_id"])
            binding = device_bindings.get(device_id, {})
            profile = device_profiles.get(str(entry.get("model_profile") or ""), {})
            record = existing_devices.get(device_id)
            if record is None:
                record = DeviceRecord(device_id=device_id)
                session.add(record)
                existing_devices[device_id] = record
            record.zone_id = str(entry.get("zone_id") or "")
            record.device_type = str(entry.get("device_type") or "unknown")
            record.priority = str(entry.get("priority") or "optional")
            record.model_profile = str(entry.get("model_profile") or "")
            record.controller_id = str(binding.get("controller_id") or "")
            record.protocol = str(binding.get("protocol") or entry.get("protocol") or "")
            record.control_mode = str(entry.get("control_mode") or profile.get("control_mode") or "")
            record.response_timeout_seconds = int(entry.get("response_timeout_seconds") or 0)
            record.write_channel_ref = str(binding.get("write_channel_ref") or "")
            record.read_channel_refs_json = json.dumps(binding.get("read_channel_refs", []), ensure_ascii=False)
            record.supported_action_types_json = json.dumps(profile.get("supported_action_types", []), ensure_ascii=False)
            record.safety_interlocks_json = json.dumps(
                entry.get("safety_interlocks") or profile.get("safety_interlocks") or [],
                ensure_ascii=False,
            )
            record.metadata_json = json.dumps(
                {
                    "catalog": entry,
                    "binding": binding,
                    "profile": profile,
                },
                ensure_ascii=False,
            )

        existing_policies = {row.policy_id: row for row in session.query(PolicyRecord).all()}
        schema_version = str(policy_rules.get("schema_version") or "unknown")
        for entry in policy_rules.get("rules", []):
            if not isinstance(entry, dict) or not entry.get("rule_id"):
                continue
            policy_id = str(entry["rule_id"])
            record = existing_policies.get(policy_id)
            if record is None:
                record = PolicyRecord(policy_id=policy_id)
                session.add(record)
                existing_policies[policy_id] = record
            record.policy_stage = str(entry.get("stage") or "unknown")
            record.severity = str(entry.get("severity") or "medium")
            record.enabled = bool(entry.get("enabled", True))
            record.description = str(entry.get("description") or "")
            record.trigger_flags_json = json.dumps(entry.get("trigger_flags", []), ensure_ascii=False)
            record.enforcement_json = json.dumps(entry.get("enforcement", {}), ensure_ascii=False)
            record.source_version = schema_version

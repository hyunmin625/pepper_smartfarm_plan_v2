from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from plc_adapter.channel_address_registry import load_channel_address_registry
from plc_adapter.device_catalog import DeviceCatalog, load_device_catalog
from plc_adapter.device_profiles import DeviceProfileRegistry, load_profile_registry
from plc_adapter.mock_adapter import MockPlcAdapter
from plc_adapter.plc_tag_modbus_tcp import PlcTagModbusTcpAdapter
from plc_adapter.resolver import DeviceCommandResolver
from plc_adapter.site_overrides import SiteOverrideRegistry, load_site_override_registry
from plc_adapter.transports import InMemoryPlcTagTransport, PlcTagTransport

from .contracts import ControlOverrideRequest, DeviceCommandRequest
from .guards import CooldownManager, DuplicateDetector, PreflightDecision, evaluate_control_override, evaluate_device_command
from .normalizer import NormalizedRequest
from .state import ControlStateStore, RuntimeFaultTracker


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False))
        handle.write("\n")


@dataclass
class DispatchAuditSink:
    path: Path

    @classmethod
    def default(cls) -> "DispatchAuditSink":
        default_path = os.getenv(
            "EXECUTION_GATEWAY_AUDIT_LOG_PATH",
            "artifacts/runtime/execution_gateway/dispatch_audit.jsonl",
        )
        return cls(Path(default_path))

    def write(self, entry: dict[str, Any]) -> None:
        append_jsonl(self.path, entry)


def build_device_adapter(
    *,
    adapter_kind: str,
    registry: DeviceProfileRegistry,
    resolver: DeviceCommandResolver,
    transport: PlcTagTransport | None = None,
):
    if adapter_kind == "mock":
        return MockPlcAdapter(registry, resolver=resolver)
    if adapter_kind == "plc_tag_modbus_tcp":
        return PlcTagModbusTcpAdapter(
            registry=registry,
            resolver=resolver,
            transport=transport or InMemoryPlcTagTransport(),
            channel_addresses=load_channel_address_registry(),
        )
    raise ValueError(f"unsupported adapter_kind {adapter_kind}")


@dataclass
class DispatchResult:
    request_id: str
    request_kind: str
    status: str
    allow_dispatch: bool
    reasons: list[str]
    normalized: dict[str, Any]
    preflight: dict[str, Any]
    policy_event: dict[str, Any] | None = None
    adapter_result: dict[str, Any] | None = None
    state_transition: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_kind": self.request_kind,
            "status": self.status,
            "allow_dispatch": self.allow_dispatch,
            "reasons": self.reasons,
            "normalized": self.normalized,
            "preflight": self.preflight,
            "policy_event": self.policy_event,
            "adapter_result": self.adapter_result,
            "state_transition": self.state_transition,
        }


class ExecutionDispatcher:
    def __init__(
        self,
        *,
        catalog: DeviceCatalog,
        registry: DeviceProfileRegistry,
        site_overrides: SiteOverrideRegistry,
        adapter_kind: str = "mock",
        transport: PlcTagTransport | None = None,
        duplicates: DuplicateDetector | None = None,
        cooldowns: CooldownManager | None = None,
        control_state: ControlStateStore | None = None,
        runtime_faults: RuntimeFaultTracker | None = None,
        audit_sink: DispatchAuditSink | None = None,
    ) -> None:
        self.catalog = catalog
        self.registry = registry
        self.site_overrides = site_overrides
        self.resolver = DeviceCommandResolver(
            catalog=catalog,
            profiles=registry,
            site_overrides=site_overrides,
        )
        self.adapter = build_device_adapter(
            adapter_kind=adapter_kind,
            registry=registry,
            resolver=self.resolver,
            transport=transport,
        )
        self.duplicates = duplicates or DuplicateDetector()
        self.cooldowns = cooldowns or CooldownManager()
        self.control_state = control_state or ControlStateStore()
        self.runtime_faults = runtime_faults or RuntimeFaultTracker()
        self.audit_sink = audit_sink or DispatchAuditSink.default()

    @classmethod
    def default(cls, *, adapter_kind: str = "mock", transport: PlcTagTransport | None = None) -> "ExecutionDispatcher":
        return cls(
            catalog=load_device_catalog(),
            registry=load_profile_registry(),
            site_overrides=load_site_override_registry(),
            adapter_kind=adapter_kind,
            transport=transport,
        )

    def dispatch_device_command(self, request: DeviceCommandRequest) -> DispatchResult:
        normalized, preflight = evaluate_device_command(
            request,
            catalog=self.catalog,
            registry=self.registry,
            duplicates=self.duplicates,
            cooldowns=self.cooldowns,
        )
        state_reasons = self.control_state.evaluate_device_block(request)
        if state_reasons:
            preflight = self._extend_preflight(preflight, state_reasons)

        adapter_result = None
        state_transition = None
        status = "rejected"
        if preflight.allow_dispatch:
            adapter_result = self.adapter.write_device_command(
                device_id=request.device_id,
                action_type=request.action_type,
                parameters=request.parameters,
            )
            state_transition = self._record_device_result(request, adapter_result)
            status = adapter_result["status"]
            if status == "acknowledged":
                self.cooldowns.activate(preflight.cooldown_key)
            else:
                preflight = self._extend_preflight(preflight, [f"adapter_{status}"])
                status = "dispatch_fault"

        result = DispatchResult(
            request_id=request.request_id,
            request_kind="device_command",
            status=status,
            allow_dispatch=preflight.allow_dispatch,
            reasons=preflight.reasons,
            normalized=normalized.__dict__,
            preflight=preflight.__dict__,
            policy_event=self._build_policy_event(preflight, request.request_id),
            adapter_result=adapter_result,
            state_transition=state_transition,
        )
        self._audit(result)
        return result

    def dispatch_control_override(self, request: ControlOverrideRequest) -> DispatchResult:
        normalized, preflight = evaluate_control_override(
            request,
            duplicates=self.duplicates,
            cooldowns=self.cooldowns,
        )

        state_transition = None
        status = "rejected"
        if preflight.allow_dispatch:
            state_transition = self.control_state.apply_override(request)
            self.cooldowns.activate(preflight.cooldown_key)
            status = "state_updated"

        result = DispatchResult(
            request_id=request.request_id,
            request_kind="control_override",
            status=status,
            allow_dispatch=preflight.allow_dispatch,
            reasons=preflight.reasons,
            normalized=normalized.__dict__,
            preflight=preflight.__dict__,
            policy_event=self._build_policy_event(preflight, request.request_id),
            state_transition=state_transition,
        )
        self._audit(result)
        return result

    def _audit(self, result: DispatchResult) -> None:
        self.audit_sink.write(
            {
                "recorded_at": utc_now(),
                **result.as_dict(),
            }
        )

    def _record_device_result(
        self,
        request: DeviceCommandRequest,
        adapter_result: dict[str, Any],
    ) -> dict[str, Any] | None:
        zone_id = request.raw.get("zone_id")
        site_id = self._infer_site_id(request)
        status = adapter_result.get("status", "unknown")
        failure_reason = adapter_result.get("failure_reason")

        transitions: list[dict[str, Any]] = []
        for scope_type, scope_id in (("zone", zone_id), ("site", site_id)):
            if not isinstance(scope_id, str) or not scope_id:
                continue
            self.runtime_faults.record(
                scope_type=scope_type,
                scope_id=scope_id,
                status=status,
                failure_reason=failure_reason,
            )
            if status in {"timeout", "fault"} and self.runtime_faults.should_enter_safe_mode(scope_type, scope_id):
                transitions.append(
                    {
                        "scope_type": scope_type,
                        "scope_id": scope_id,
                        "fault_state": self.runtime_faults.get(scope_type, scope_id).as_dict(),
                        "control_transition": self.control_state.enter_safe_mode(
                            scope_type=scope_type,
                            scope_id=scope_id,
                            reason=f"runtime_{status}",
                            request_id=request.request_id,
                        ),
                    }
                )

        if not transitions:
            return None
        return {"runtime_safe_mode_transitions": transitions}

    @staticmethod
    def _build_policy_event(preflight: PreflightDecision, request_id: str) -> dict[str, Any] | None:
        if preflight.policy_result == "pass" and not any(reason.startswith("policy_precheck:") for reason in preflight.reasons):
            return None
        event_type = "blocked" if preflight.policy_result == "blocked" else "approval_required"
        return {
            "request_id": request_id,
            "event_type": event_type,
            "policy_result": preflight.policy_result,
            "policy_ids": list(preflight.policy_ids),
            "reason_codes": [reason for reason in preflight.reasons if reason.startswith("policy_")],
        }

    @staticmethod
    def _extend_preflight(preflight: PreflightDecision, extra_reasons: list[str]) -> PreflightDecision:
        merged_reasons = list(preflight.reasons)
        for reason in extra_reasons:
            if reason not in merged_reasons:
                merged_reasons.append(reason)
        return PreflightDecision(
            status="rejected" if merged_reasons else preflight.status,
            allow_dispatch=False if merged_reasons else preflight.allow_dispatch,
            reasons=merged_reasons,
            dedupe_key=preflight.dedupe_key,
            cooldown_key=preflight.cooldown_key,
        )

    def _infer_site_id(self, request: DeviceCommandRequest) -> str | None:
        raw_site_id = self.site_overrides.site_id
        if isinstance(raw_site_id, str) and raw_site_id:
            return raw_site_id
        zone_id = request.raw.get("zone_id")
        if isinstance(zone_id, str) and zone_id:
            zone_parts = zone_id.split("-")
            if len(zone_parts) >= 2:
                return "-".join(zone_parts[:2])
            return zone_id
        device_prefix = request.device_id.split("--", 1)[0]
        if device_prefix:
            parts = device_prefix.split("-")
            if len(parts) >= 2:
                return "-".join(parts[:2])
            return device_prefix
        return None

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    purpose: str
    stage: str
    status: str
    risk_class: str
    input_fields: tuple[str, ...]
    output_fields: tuple[str, ...]
    notes: str = ""
    model_visible: bool = True

    def as_prompt_dict(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "purpose": self.purpose,
            "risk_class": self.risk_class,
            "input_fields": list(self.input_fields),
            "output_fields": list(self.output_fields),
        }
        if self.notes:
            payload["notes"] = self.notes
        return payload

    def as_catalog_dict(self) -> dict[str, Any]:
        payload = self.as_prompt_dict()
        payload.update(
            {
                "stage": self.stage,
                "status": self.status,
                "model_visible": self.model_visible,
            }
        )
        return payload


def _tool(
    *,
    name: str,
    purpose: str,
    stage: str,
    status: str,
    risk_class: str,
    input_fields: tuple[str, ...],
    output_fields: tuple[str, ...],
    notes: str = "",
    model_visible: bool = True,
) -> ToolDefinition:
    return ToolDefinition(
        name=name,
        purpose=purpose,
        stage=stage,
        status=status,
        risk_class=risk_class,
        input_fields=input_fields,
        output_fields=output_fields,
        notes=notes,
        model_visible=model_visible,
    )


@lru_cache(maxsize=1)
def load_default_tool_registry() -> tuple[ToolDefinition, ...]:
    return (
        _tool(
            name="get_zone_state",
            purpose="현재 구역 상태와 파생 feature snapshot을 조회한다.",
            stage="runtime",
            status="implemented",
            risk_class="read_only",
            input_fields=("farm_id", "zone_id", "at"),
            output_fields=("zone_state", "state_estimate", "derived_features"),
            notes="state-estimator payload와 ops-api evaluate request에서 직접 제공된다.",
        ),
        _tool(
            name="search_cultivation_knowledge",
            purpose="재배 지식과 SOP chunk를 검색해 citation 후보를 가져온다.",
            stage="runtime",
            status="implemented",
            risk_class="read_only",
            input_fields=("query", "filters", "top_k"),
            output_fields=("chunk_id", "document_id", "score", "excerpt"),
            notes="local keyword retriever가 retrieved_context로 자동 주입한다.",
        ),
        _tool(
            name="get_recent_trend",
            purpose="최근 추세와 변화율을 확인해 위험도 판단에 사용한다.",
            stage="runtime",
            status="implemented",
            risk_class="read_only",
            input_fields=("zone_id", "metric", "window_minutes"),
            output_fields=("baseline", "delta_10m", "delta_30m", "trend_summary"),
            notes="state-estimator derived_features와 trend snapshot으로 공급된다.",
        ),
        _tool(
            name="get_active_constraints",
            purpose="현재 hard block, approval, cooldown, override 상태를 조회한다.",
            stage="runtime",
            status="implemented",
            risk_class="read_only",
            input_fields=("zone_id",),
            output_fields=("manual_override", "safe_mode", "cooldown", "hard_block"),
            notes="zone_state.active_constraints와 current_state에서 직접 제공된다.",
        ),
        _tool(
            name="estimate_growth_stage",
            purpose="생육 단계를 보정해 task 판단의 기준 축을 제공한다.",
            stage="runtime",
            status="implemented",
            risk_class="derived_read_only",
            input_fields=("zone_id", "state_snapshot"),
            output_fields=("growth_stage", "confidence"),
            notes="state-estimator zone_state와 state_estimate에 이미 포함된다.",
        ),
        _tool(
            name="request_human_approval",
            purpose="중위험 이상 action을 승인 큐에 등록한다.",
            stage="runtime",
            status="implemented",
            risk_class="approval_gate",
            input_fields=("proposed_actions", "risk_level", "reason"),
            output_fields=("approval_ticket_id", "approval_status"),
            notes="ops-api approval flow와 execution-gateway 승인 라우팅에 연결된다.",
        ),
        _tool(
            name="log_decision",
            purpose="LLM 판단, validator 결과, citation을 감사 로그에 저장한다.",
            stage="runtime",
            status="implemented",
            risk_class="audit",
            input_fields=("decision_payload",),
            output_fields=("decision_id", "audit_path"),
            notes="ops-api decisions/policy_evaluations/operator_reviews 테이블에 저장된다.",
        ),
        _tool(
            name="get_device_readback",
            purpose="명령 후 장치 응답과 readback 상태를 조회한다.",
            stage="runtime",
            status="planned",
            risk_class="read_only",
            input_fields=("device_id", "window_minutes"),
            output_fields=("transport_status", "readback_state", "degraded"),
            notes="execution-gateway와 실제 PLC adapter 연결 이후 활성화한다.",
            model_visible=False,
        ),
        _tool(
            name="get_recent_operator_notes",
            purpose="작업자 메모와 수동 개입 이력을 조회한다.",
            stage="runtime",
            status="planned",
            risk_class="read_only",
            input_fields=("zone_id", "window_hours"),
            output_fields=("notes", "manual_override_events"),
            notes="operator review/history API가 축적되면 노출한다.",
            model_visible=False,
        ),
        _tool(
            name="get_harvest_candidates",
            purpose="비전 기반 수확 후보를 조회한다.",
            stage="runtime",
            status="planned",
            risk_class="read_only",
            input_fields=("zone_id", "top_k"),
            output_fields=("candidate_id", "maturity_score", "defect_score"),
            notes="vision pipeline 연계 이후 활성화한다.",
            model_visible=False,
        ),
    )


def available_tool_definitions() -> list[ToolDefinition]:
    return [
        tool
        for tool in load_default_tool_registry()
        if tool.model_visible and tool.status == "implemented"
    ]


def summarize_tool_registry(*, include_planned: bool = False) -> list[dict[str, Any]]:
    tools = load_default_tool_registry()
    if not include_planned:
        tools = tuple(tool for tool in tools if tool.status == "implemented")
    return [tool.as_catalog_dict() for tool in tools]


def prompt_tool_catalog() -> list[dict[str, Any]]:
    return [tool.as_prompt_dict() for tool in available_tool_definitions()]

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EvaluateZoneRequest(BaseModel):
    request_id: str
    zone_id: str
    task_type: str
    growth_stage: str = "unknown"
    current_state: dict[str, Any] = Field(default_factory=dict)
    history: dict[str, Any] = Field(default_factory=dict)
    sensor_quality: dict[str, Any] = Field(default_factory=dict)
    device_status: dict[str, Any] = Field(default_factory=dict)
    weather_context: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    prompt_version: str = "sft_v10"
    mode: Literal["shadow", "approval"] | None = None
    retrieval_limit: int = 5


class ApprovalRequest(BaseModel):
    decision_id: int
    actor_id: str
    reason: str = ""


class ShadowReviewRequest(BaseModel):
    decision_id: int
    actor_id: str
    agreement_status: Literal["agree", "disagree"]
    note: str = ""
    expected_risk_level: str | None = None
    expected_actions: list[str] = Field(default_factory=list)
    expected_robot_tasks: list[str] = Field(default_factory=list)


class RuntimeModeRequest(BaseModel):
    mode: Literal["shadow", "approval"]
    actor_id: str = "operator"
    reason: str = ""

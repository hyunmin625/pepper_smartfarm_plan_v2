from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ActorModel(BaseModel):
    actor_id: str
    role: str
    auth_mode: str


class ApiResponse(BaseModel):
    data: Any
    meta: dict[str, Any] = Field(default_factory=dict)
    actor: ActorModel | None = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


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
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    prompt_version: str = "sft_v10"
    mode: Literal["shadow", "approval"] | None = None
    retrieval_limit: int = 5


class ApprovalRequest(BaseModel):
    decision_id: int
    actor_id: str
    reason: str = ""


class ExecuteActionRequest(BaseModel):
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


class ShadowCaptureCaseRequest(BaseModel):
    request_id: str
    task_type: str
    context: dict[str, Any]
    output: dict[str, Any]
    metadata: dict[str, Any]
    observed: dict[str, Any]


class ShadowCaptureRequest(BaseModel):
    append: bool = True
    cases: list[ShadowCaptureCaseRequest] = Field(default_factory=list)


class RuntimeModeRequest(BaseModel):
    mode: Literal["shadow", "approval"]
    actor_id: str = "operator"
    reason: str = ""


class RobotTaskCreateRequest(BaseModel):
    zone_id: str
    actor_id: str
    task_type: str
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    reason: str
    candidate_id: str | None = None
    decision_id: int | None = None
    approval_required: bool = False
    status: Literal["pending", "approved", "done", "blocked"] = "pending"
    target: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)


class PolicyUpdateRequest(BaseModel):
    enabled: bool | None = None
    severity: str | None = None
    description: str | None = None
    trigger_flags: list[str] | None = None
    enforcement: dict[str, Any] | None = None

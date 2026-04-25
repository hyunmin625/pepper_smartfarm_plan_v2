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


class OperatorOverrideRequest(BaseModel):
    zone_id: str | None = None
    target_scope: Literal["system", "zone", "device", "robot"] = "zone"
    target_id: str = Field(default="system", min_length=1, max_length=128)
    override_type: Literal["manual_override", "safe_mode", "emergency_stop", "operator_lock"] = "manual_override"
    override_state: Literal["active", "cleared"] = "active"
    reason: str = Field(default="", max_length=500)
    payload: dict[str, Any] = Field(default_factory=dict)


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


class ChatMessageRequest(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessageRequest] = Field(default_factory=list)
    system_prompt: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


AUTOMATION_SENSOR_KEYS = {
    # 외부 기상
    "ext_air_temp_c", "ext_rh_pct", "ext_wind_dir_deg", "ext_wind_speed_m_s", "ext_rainfall_mm",
    # 내부 기상
    "air_temp_c", "rh_pct", "co2_ppm", "vpd_kpa", "par_umol_m2_s",
    # 배지 — Grodan Delta
    "substrate_delta_temp_c", "substrate_delta_moisture_pct", "substrate_delta_ph",
    # 배지 — GT Master
    "substrate_gt_master_temp_c", "substrate_gt_master_moisture_pct", "substrate_gt_master_ph",
    # 공통 근권 (양식 통합)
    "substrate_temp_c", "substrate_moisture_pct", "feed_ec_ds_m", "drain_ec_ds_m",
    "feed_ph", "drain_ph",
}

AUTOMATION_DEVICE_TYPES = {
    "roof_vent",          # 천장개폐기
    "hvac_geothermal",    # 지하수 활용 냉난방기
    "humidifier",         # 가습기
    "fertigation_mixer",  # 양액 비율 조정
    "irrigation_pump",    # 관수 펌프
    "shade_curtain",      # 차광 커튼
    "fan_circulation",    # 순환팬
    "co2_injector",       # CO2 공급기
}

AUTOMATION_OPERATORS = {"gt", "gte", "lt", "lte", "eq", "between"}
AUTOMATION_RUNTIME_MODE_GATES = {"shadow", "approval", "execute"}


class AutomationRuleRequest(BaseModel):
    rule_id: str = Field(..., min_length=1, max_length=128)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    zone_id: str | None = None
    sensor_key: Literal[
        "ext_air_temp_c", "ext_rh_pct", "ext_wind_dir_deg", "ext_wind_speed_m_s", "ext_rainfall_mm",
        "air_temp_c", "rh_pct", "co2_ppm", "vpd_kpa", "par_umol_m2_s",
        "substrate_delta_temp_c", "substrate_delta_moisture_pct", "substrate_delta_ph",
        "substrate_gt_master_temp_c", "substrate_gt_master_moisture_pct", "substrate_gt_master_ph",
        "substrate_temp_c", "substrate_moisture_pct", "feed_ec_ds_m", "drain_ec_ds_m",
        "feed_ph", "drain_ph",
    ]
    operator: Literal["gt", "gte", "lt", "lte", "eq", "between"]
    threshold_value: float | None = None
    threshold_min: float | None = None
    threshold_max: float | None = None
    hysteresis_value: float | None = None
    cooldown_minutes: int = 15
    target_device_type: Literal[
        "roof_vent", "hvac_geothermal", "humidifier",
        "fertigation_mixer", "irrigation_pump",
        "shade_curtain", "fan_circulation", "co2_injector",
    ]
    target_device_id: str | None = None
    target_action: str = Field(..., min_length=1, max_length=64)
    action_payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 100
    enabled: bool = True
    runtime_mode_gate: Literal["shadow", "approval", "execute"] = "approval"
    owner_role: Literal["viewer", "operator", "service", "admin"] = "operator"


class AutomationRuleUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    zone_id: str | None = None
    operator: Literal["gt", "gte", "lt", "lte", "eq", "between"] | None = None
    threshold_value: float | None = None
    threshold_min: float | None = None
    threshold_max: float | None = None
    hysteresis_value: float | None = None
    cooldown_minutes: int | None = None
    target_device_id: str | None = None
    target_action: str | None = Field(None, min_length=1, max_length=64)
    action_payload: dict[str, Any] | None = None
    priority: int | None = None
    enabled: bool | None = None
    runtime_mode_gate: Literal["shadow", "approval", "execute"] | None = None


class AutomationRuleToggleRequest(BaseModel):
    enabled: bool


class AutomationEvaluateRequest(BaseModel):
    """Offline sensor snapshot used to dry-run the rule engine.

    Populate only the keys you want to test. Missing keys behave as if the
    sensor has no reading, so the corresponding rules do not match.
    """

    zone_id: str | None = None
    runtime_mode_override: Literal["shadow", "approval", "execute"] | None = None
    sensor_snapshot: dict[str, float] = Field(default_factory=dict)


class AutomationTriggerReviewRequest(BaseModel):
    reason: str = Field(default="", max_length=500)

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    zone_id: Mapped[str] = mapped_column(String(128), index=True)
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    runtime_mode: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="evaluated")
    model_id: Mapped[str] = mapped_column(String(255))
    prompt_version: Mapped[str] = mapped_column(String(64))
    raw_output_json: Mapped[str] = mapped_column(Text)
    parsed_output_json: Mapped[str] = mapped_column(Text)
    validated_output_json: Mapped[str] = mapped_column(Text)
    zone_state_json: Mapped[str] = mapped_column(Text)
    citations_json: Mapped[str] = mapped_column(Text)
    retrieval_context_json: Mapped[str] = mapped_column(Text)
    audit_path: Mapped[str] = mapped_column(String(512))
    validator_reason_codes_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    approvals: Mapped[list["ApprovalRecord"]] = relationship(back_populates="decision")
    device_commands: Mapped[list["DeviceCommandRecord"]] = relationship(back_populates="decision")
    policy_evaluations: Mapped[list["PolicyEvaluationRecord"]] = relationship(back_populates="decision")
    operator_reviews: Mapped[list["OperatorReviewRecord"]] = relationship(back_populates="decision")
    alerts: Mapped[list["AlertRecord"]] = relationship(back_populates="decision")
    robot_candidates: Mapped[list["RobotCandidateRecord"]] = relationship(back_populates="decision")
    robot_tasks: Mapped[list["RobotTaskRecord"]] = relationship(back_populates="decision")
    automation_triggers: Mapped[list["AutomationRuleTriggerRecord"]] = relationship(
        back_populates="decision"
    )


class ZoneRecord(Base):
    __tablename__ = "zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    zone_type: Mapped[str] = mapped_column(String(64))
    priority: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class SensorRecord(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    zone_id: Mapped[str] = mapped_column(String(128), index=True)
    sensor_type: Mapped[str] = mapped_column(String(64))
    measurement_fields_json: Mapped[str] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(String(64))
    raw_sample_seconds: Mapped[int] = mapped_column(Integer)
    ai_aggregation_seconds: Mapped[int] = mapped_column(Integer)
    priority: Mapped[str] = mapped_column(String(32))
    model_profile: Mapped[str] = mapped_column(String(128))
    protocol: Mapped[str] = mapped_column(String(64))
    install_location: Mapped[str] = mapped_column(Text)
    calibration_interval_days: Mapped[int] = mapped_column(Integer)
    redundancy_group: Mapped[str] = mapped_column(String(128))
    quality_flags_json: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class DeviceRecord(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    zone_id: Mapped[str] = mapped_column(String(128), index=True)
    device_type: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(32))
    model_profile: Mapped[str] = mapped_column(String(128))
    controller_id: Mapped[str] = mapped_column(String(128))
    protocol: Mapped[str] = mapped_column(String(64))
    control_mode: Mapped[str] = mapped_column(String(64))
    response_timeout_seconds: Mapped[int] = mapped_column(Integer)
    write_channel_ref: Mapped[str] = mapped_column(Text)
    read_channel_refs_json: Mapped[str] = mapped_column(Text)
    supported_action_types_json: Mapped[str] = mapped_column(Text)
    safety_interlocks_json: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class PolicyRecord(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    policy_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    policy_stage: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    description: Mapped[str] = mapped_column(Text)
    trigger_flags_json: Mapped[str] = mapped_column(Text)
    enforcement_json: Mapped[str] = mapped_column(Text)
    source_version: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class ApprovalRecord(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), index=True)
    actor_id: Mapped[str] = mapped_column(String(128))
    approval_status: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    approval_payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    decision: Mapped[DecisionRecord] = relationship(back_populates="approvals")


class DeviceCommandRecord(Base):
    __tablename__ = "device_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), index=True)
    command_kind: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str] = mapped_column(String(128))
    action_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32))
    payload_json: Mapped[str] = mapped_column(Text)
    adapter_result_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    decision: Mapped[DecisionRecord] = relationship(back_populates="device_commands")


class PolicyEvaluationRecord(Base):
    __tablename__ = "policy_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), index=True)
    policy_source: Mapped[str] = mapped_column(String(64))
    policy_result: Mapped[str] = mapped_column(String(32))
    reason_codes_json: Mapped[str] = mapped_column(Text)
    evaluation_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    decision: Mapped[DecisionRecord] = relationship(back_populates="policy_evaluations")


class PolicyEventRecord(Base):
    __tablename__ = "policy_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id"), index=True, nullable=True)
    request_id: Mapped[str] = mapped_column(String(128), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    policy_result: Mapped[str] = mapped_column(String(32), index=True)
    policy_ids_json: Mapped[str] = mapped_column(Text)
    reason_codes_json: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    decision: Mapped[DecisionRecord | None] = relationship()


class OperatorReviewRecord(Base):
    __tablename__ = "operator_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), index=True)
    actor_id: Mapped[str] = mapped_column(String(128))
    review_mode: Mapped[str] = mapped_column(String(32))
    agreement_status: Mapped[str] = mapped_column(String(32))
    expected_risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    expected_actions_json: Mapped[str] = mapped_column(Text)
    expected_robot_tasks_json: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    decision: Mapped[DecisionRecord] = relationship(back_populates="operator_reviews")


class AlertRecord(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id"), index=True, nullable=True)
    zone_id: Mapped[str] = mapped_column(String(128), index=True)
    alert_type: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    summary: Mapped[str] = mapped_column(Text)
    validator_reason_codes_json: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    decision: Mapped[DecisionRecord | None] = relationship(back_populates="alerts")


class RobotCandidateRecord(Base):
    __tablename__ = "robot_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id"), index=True, nullable=True)
    zone_id: Mapped[str] = mapped_column(String(128), index=True)
    candidate_type: Mapped[str] = mapped_column(String(64))
    priority: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    decision: Mapped[DecisionRecord | None] = relationship(back_populates="robot_candidates")


class RobotTaskRecord(Base):
    __tablename__ = "robot_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id"), index=True, nullable=True)
    zone_id: Mapped[str] = mapped_column(String(128), index=True)
    candidate_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(32))
    approval_required: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(Text)
    target_json: Mapped[str] = mapped_column(Text)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    decision: Mapped[DecisionRecord | None] = relationship(back_populates="robot_tasks")


# ---------------------------------------------------------------------------
# TimescaleDB sensor time-series records.
#
# These tables are created only by
# infra/postgres/002_timescaledb_sensor_readings.sql on PostgreSQL with the
# TimescaleDB extension installed. SQLite runtime is no longer supported.
# ---------------------------------------------------------------------------


class SensorReadingRecord(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    site_id: Mapped[str] = mapped_column(String(64), index=True)
    zone_id: Mapped[str] = mapped_column(String(128), index=True)
    record_kind: Mapped[str] = mapped_column(String(16), index=True)
    source_id: Mapped[str] = mapped_column(String(128), index=True)
    source_type: Mapped[str] = mapped_column(String(64))
    metric_name: Mapped[str] = mapped_column(String(64), index=True)
    metric_value_double: Mapped[float | None] = mapped_column(Float, nullable=True)
    metric_value_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quality_flag: Mapped[str] = mapped_column(String(32), index=True)
    transport_status: Mapped[str] = mapped_column(String(32))
    binding_group_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    parser_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    calibration_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ZoneStateSnapshotRecord(Base):
    __tablename__ = "zone_state_snapshots"

    measured_at: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    zone_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    site_id: Mapped[str] = mapped_column(String(64), index=True)
    snapshot_window_seconds: Mapped[int] = mapped_column(Integer, default=60)
    air_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    rh_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    vpd_kpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    substrate_moisture_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    substrate_temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    co2_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    par_umol_m2_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    feed_ec_ds_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    drain_ec_ds_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    feed_ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    drain_ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    irrigation_event_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    drain_volume_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_quality_status: Mapped[str] = mapped_column(String(32), default="unknown")
    risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active_constraints_json: Mapped[str] = mapped_column(Text, default="[]")
    device_status_json: Mapped[str] = mapped_column(Text, default="{}")
    feature_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    source: Mapped[str] = mapped_column(String(64), default="state-estimator")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AutomationRuleRecord(Base):
    """Operator-defined "if <sensor> <op> <threshold> then <device action>" rule.

    The rule engine in ``ops_api/automation.py`` loads every enabled row and
    matches them against a sensor snapshot (``zone_state_snapshots`` columns
    plus external weather keys). Matched rules produce proposed actions that
    are handed off to the same shadow / approval / execute pipeline as LLM
    decisions, so hard-safety rules and runtime_mode still apply.

    operator ∈ {gt, gte, lt, lte, eq, between}. For ``between`` both
    ``threshold_min`` and ``threshold_max`` must be set and the match condition
    is ``threshold_min <= sensor_value <= threshold_max``.

    runtime_mode_gate is the minimum runtime mode at which the rule is
    allowed to produce an action. ``shadow`` rules always run but only log
    triggers; ``approval`` rules also write a pending_approval decision;
    ``execute`` rules additionally request dispatch. Setting a stricter
    gate prevents e.g. a newly authored heating rule from auto-executing
    before operator approval.
    """

    __tablename__ = "automation_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    zone_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    sensor_key: Mapped[str] = mapped_column(String(64), index=True)
    operator: Mapped[str] = mapped_column(String(16))
    threshold_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    hysteresis_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=15)
    target_device_type: Mapped[str] = mapped_column(String(64), index=True)
    target_device_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_action: Mapped[str] = mapped_column(String(64))
    action_payload_json: Mapped[str] = mapped_column(Text, default="{}")
    priority: Mapped[int] = mapped_column(Integer, default=100)
    enabled: Mapped[bool] = mapped_column(Integer, default=1)
    runtime_mode_gate: Mapped[str] = mapped_column(String(16), default="approval")
    owner_role: Mapped[str] = mapped_column(String(32), default="operator")
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    triggers: Mapped[list["AutomationRuleTriggerRecord"]] = relationship(
        back_populates="rule",
        cascade="all, delete-orphan",
    )


class AutomationRuleTriggerRecord(Base):
    """One match of an automation rule against a sensor snapshot.

    Stored regardless of whether the proposed action is eventually executed,
    so operators can audit how often each rule would fire under the current
    sensor conditions. ``status`` follows the runtime_mode pipeline:

    - ``shadow_logged``: runtime_mode was shadow, trigger recorded only.
    - ``approval_pending``: wrote an ApprovalRecord-compatible proposed_action.
    - ``approved``: operator approved via ``/automation/triggers/{id}/approve``.
      Phase Q ``dispatch_approved_triggers`` flushes these into the
      execution gateway on the next AutomationRunner tick.
    - ``rejected``: operator rejected via ``/automation/triggers/{id}/reject``.
    - ``dispatched``: execution_gateway accepted the command.
    - ``dispatch_fault``: dispatcher call failed (adapter error / rule
      row missing). Left as a terminal state for operator inspection.
    - ``blocked_validator``: output_validator rejected the proposed action.
    - ``blocked_guard``: execution-gateway guard rejected (worker_present etc.).
    - ``cooldown_skipped``: rule matched but was within cooldown window.
    """

    __tablename__ = "automation_rule_triggers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(
        ForeignKey("automation_rules.id", ondelete="CASCADE"), index=True
    )
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    zone_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sensor_key: Mapped[str] = mapped_column(String(64))
    matched_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_snapshot_json: Mapped[str] = mapped_column(Text, default="{}")
    proposed_action_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(32), default="shadow_logged", index=True)
    runtime_mode: Mapped[str] = mapped_column(String(16), default="shadow")
    decision_id: Mapped[int | None] = mapped_column(
        ForeignKey("decisions.id"), nullable=True
    )
    note: Mapped[str] = mapped_column(Text, default="")
    # Phase P-3 operator review fields. ``reviewed_by`` holds the actor
    # that moved the trigger out of ``approval_pending`` via
    # ``POST /automation/triggers/{id}/approve`` or ``/reject``. The
    # trigger ``status`` transitions to ``approved`` or ``rejected``
    # respectively. Dispatch itself is wired in Phase Q once automation
    # triggers get a first-class DecisionRecord FK.
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_reason: Mapped[str] = mapped_column(Text, default="")

    rule: Mapped[AutomationRuleRecord] = relationship(back_populates="triggers")
    decision: Mapped["DecisionRecord | None"] = relationship(back_populates="automation_triggers")

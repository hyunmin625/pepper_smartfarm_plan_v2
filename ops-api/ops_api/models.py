from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
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

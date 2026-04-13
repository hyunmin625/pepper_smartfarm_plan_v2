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

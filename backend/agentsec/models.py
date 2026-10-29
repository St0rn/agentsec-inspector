from __future__ import annotations

import enum
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def uid() -> str:
    return str(uuid.uuid4())


def now() -> datetime:
    return datetime.now(UTC)


class Severity(str, enum.Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class FindingStatus(str, enum.Enum):
    open = "Open"
    confirmed = "Confirmed"
    false_positive = "False Positive"
    accepted_risk = "Accepted Risk"
    remediated = "Remediated"


class AuditStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    client_name: Mapped[str] = mapped_column(String(200), index=True)
    engagement_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    authorized_scope: Mapped[str] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    targets: Mapped[list[Target]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    findings: Mapped[list[Finding]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Target(Base):
    __tablename__ = "targets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    target_type: Mapped[str] = mapped_column(String(50), index=True)
    endpoint: Mapped[str | None] = mapped_column(String(2048))
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    remote_authorized: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    project: Mapped[Project] = relationship(back_populates="targets")
    connectors: Mapped[list[Connector]] = relationship(
        back_populates="target", cascade="all, delete-orphan"
    )


class Connector(Base):
    __tablename__ = "connectors"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    target_id: Mapped[str | None] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    connector_type: Mapped[str] = mapped_column(String(50), index=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    encrypted_secret: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(default=True)
    last_status: Mapped[str] = mapped_column(String(30), default="not_tested")
    target: Mapped[Target | None] = relationship(back_populates="connectors")


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    version: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), index=True)
    prerequisites: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    procedure: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    success_criteria: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    failure_criteria: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    references: Mapped[list[str]] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(default=True)


class AuditRun(Base):
    __tablename__ = "audit_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    target_id: Mapped[str | None] = mapped_column(
        ForeignKey("targets.id", ondelete="SET NULL"), index=True
    )
    audit_type: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[AuditStatus] = mapped_column(
        Enum(AuditStatus), default=AuditStatus.queued, index=True
    )
    passive: Mapped[bool] = mapped_column(default=True)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    summary: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class TestExecution(Base):
    __tablename__ = "test_executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    audit_run_id: Mapped[str] = mapped_column(
        ForeignKey("audit_runs.id", ondelete="CASCADE"), index=True
    )
    scenario_id: Mapped[str] = mapped_column(String(100), index=True)
    scenario_version: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), index=True)
    request_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    response_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    analysis: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    audit_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("audit_runs.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    component: Mapped[str] = mapped_column(String(300))
    classification: Mapped[str] = mapped_column(String(40), default="Risk potential")
    severity: Mapped[Severity] = mapped_column(Enum(Severity), index=True)
    confidence: Mapped[str] = mapped_column(String(20))
    impact: Mapped[str] = mapped_column(Text, default="")
    exploitation_conditions: Mapped[str] = mapped_column(Text, default="")
    reproduction_steps: Mapped[str] = mapped_column(Text, default="")
    observed_result: Mapped[str] = mapped_column(Text, default="")
    expected_result: Mapped[str] = mapped_column(Text, default="")
    recommendation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus), default=FindingStatus.open, index=True
    )
    frameworks: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    project: Mapped[Project] = relationship(back_populates="findings")
    evidence: Mapped[list[Evidence]] = relationship(
        back_populates="finding", cascade="all, delete-orphan"
    )
    history: Mapped[list[FindingHistory]] = relationship(cascade="all, delete-orphan")


class FindingHistory(Base):
    __tablename__ = "finding_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), index=True
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    changed_by: Mapped[str] = mapped_column(String(100), default="local-user")
    changes: Mapped[dict[str, Any]] = mapped_column(JSON)


class Evidence(Base):
    __tablename__ = "evidence"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    finding_id: Mapped[str | None] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finding: Mapped[Finding | None] = relationship(back_populates="evidence")


class AgentEvent(Base):
    __tablename__ = "agent_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    audit_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("audit_runs.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    actor: Mapped[str] = mapped_column(String(100))
    target: Mapped[str | None] = mapped_column(String(200))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    report_type: Mapped[str] = mapped_column(String(30))
    language: Mapped[str] = mapped_column(String(5))
    format: Mapped[str] = mapped_column(String(10))
    template_name: Mapped[str] = mapped_column(String(100), default="default")
    path: Mapped[str] = mapped_column(String(2048))
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AppSetting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(150), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class RAGDocument(Base):
    __tablename__ = "rag_documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    metadata_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    is_lab_document: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RAGTrace(Base):
    __tablename__ = "rag_traces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    target_id: Mapped[str | None] = mapped_column(
        ForeignKey("targets.id", ondelete="SET NULL"), index=True
    )
    query: Mapped[str] = mapped_column(Text)
    retrieved_chunks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    llm_context: Mapped[str | None] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    expected_response: Mapped[str] = mapped_column(Text, default="")
    telemetry_available: Mapped[bool] = mapped_column(default=False)
    analysis: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


Index("ix_finding_project_severity_status", Finding.project_id, Finding.severity, Finding.status)
Index("ix_audit_project_created", AuditRun.project_id, AuditRun.created_at)

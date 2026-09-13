"""SQLAlchemy models: complaints, attachments, AI assessments, CAPA actions, audit logs."""
from datetime import datetime

from sqlalchemy import (JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    complaint_number: Mapped[str] = mapped_column(String(30), unique=True, index=True)

    # Section 1: origin & customer
    complaint_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(200))
    customer_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Section 2: product & batch
    product_name: Mapped[str] = mapped_column(String(200), index=True)
    product_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    strength_or_grade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manufacturing_date: Mapped[str | None] = mapped_column(String(20), nullable=True)  # ISO date
    expiry_date: Mapped[str | None] = mapped_column(String(20), nullable=True)        # ISO date

    # Section 3: complaint details
    complaint_type: Mapped[str] = mapped_column(String(100))
    complaint_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    received_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    quantity_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    market: Mapped[str | None] = mapped_column(String(100), nullable=True)

    patient_impact: Mapped[str | None] = mapped_column(String(500), nullable=True)
    adverse_event_reported: Mapped[bool] = mapped_column(Boolean, default=False)

    # Section 4: initial assessment
    initial_severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # AI + human outcomes
    ai_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    final_risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="New", index=True)

    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tracks which form fields were populated by the AI extraction pass
    ai_populated_fields: Mapped[list | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    attachments: Mapped[list["ComplaintAttachment"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    ai_assessments: Mapped[list["AIAssessment"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    capa_actions: Mapped[list["CapaAction"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="complaint", cascade="all, delete-orphan"
    )


class ComplaintAttachment(Base):
    __tablename__ = "complaint_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    filename: Mapped[str] = mapped_column(String(300))
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stored_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    complaint: Mapped[Complaint] = relationship(back_populates="attachments")


class AIAssessment(Base):
    __tablename__ = "ai_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)

    completeness_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_reasoning: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    root_cause_suggestions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    capa_recommendations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    duplicate_matches: Mapped[list | None] = mapped_column(JSON, nullable=True)

    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    complaint: Mapped[Complaint] = relationship(back_populates="ai_assessments")


class CapaAction(Base):
    __tablename__ = "capa_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(20))  # "Corrective" | "Preventive"
    description: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="AI")  # "AI" | "Human"
    status: Mapped[str] = mapped_column(String(30), default="Proposed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    complaint: Mapped[Complaint] = relationship(back_populates="capa_actions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    complaint_id: Mapped[int] = mapped_column(ForeignKey("complaints.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    old_value: Mapped[str | None] = mapped_column(String(300), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(300), nullable=True)
    actor: Mapped[str] = mapped_column(String(100), default="quality.user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    complaint: Mapped[Complaint] = relationship(back_populates="audit_logs")

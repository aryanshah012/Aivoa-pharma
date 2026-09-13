"""Data access layer. All SQL lives here — routes and services stay thin."""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.complaint import AIAssessment, AuditLog, CapaAction, Complaint
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate
from app.utils.complaint_number import generate_complaint_number


def _apply_filters(
    stmt: Select,
    *,
    product: Optional[str],
    risk: Optional[str],
    status: Optional[str],
    category: Optional[str],
    search: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
) -> Select:
    if product:
        stmt = stmt.where(Complaint.product_name.ilike(f"%{product}%"))
    if risk:
        stmt = stmt.where(
            or_(
                Complaint.final_risk_level == risk,
                Complaint.ai_risk_level == risk,
            )
        )
    if status:
        stmt = stmt.where(Complaint.status == status)
    if category:
        stmt = stmt.where(Complaint.complaint_type == category)
    if date_from:
        stmt = stmt.where(Complaint.received_date >= date_from)
    if date_to:
        stmt = stmt.where(Complaint.received_date <= date_to)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Complaint.complaint_number.ilike(like),
                Complaint.customer_name.ilike(like),
                Complaint.product_name.ilike(like),
                Complaint.batch_number.ilike(like),
            )
        )
    return stmt


def list_complaints(
    db: Session,
    *,
    product: Optional[str] = None,
    risk: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Complaint]:
    stmt = select(Complaint).order_by(Complaint.created_at.desc())
    stmt = _apply_filters(
        stmt,
        product=product,
        risk=risk,
        status=status,
        category=category,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    return list(db.execute(stmt.offset(skip).limit(limit)).scalars().all())


def count_complaints(db: Session, **filters: Any) -> int:
    stmt = select(func.count(Complaint.id))
    stmt = _apply_filters(
        stmt,
        product=filters.get("product"),
        risk=filters.get("risk"),
        status=filters.get("status"),
        category=filters.get("category"),
        search=filters.get("search"),
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
    )
    return int(db.execute(stmt).scalar() or 0)


def get_complaint(db: Session, complaint_id: int) -> Optional[Complaint]:
    return db.get(Complaint, complaint_id)


def get_complaint_by_number(db: Session, complaint_number: str) -> Optional[Complaint]:
    return db.execute(
        select(Complaint).where(Complaint.complaint_number == complaint_number)
    ).scalar_one_or_none()


def create_complaint(db: Session, payload: ComplaintCreate) -> Complaint:
    data = payload.model_dump()
    complaint = Complaint(
        **data,
        complaint_number=generate_complaint_number(db),
    )
    db.add(complaint)
    db.flush()
    add_audit_log(db, complaint.id, "Complaint saved", actor="quality.user")
    db.commit()
    db.refresh(complaint)
    return complaint


def update_complaint(db: Session, complaint: Complaint, payload: ComplaintUpdate) -> Complaint:
    changes = payload.model_dump(exclude_unset=True)
    tracked = ["final_risk_level", "status", "priority", "initial_severity"]
    for field, new_value in changes.items():
        old_value = getattr(complaint, field, None)
        setattr(complaint, field, new_value)
        if field == "status" and old_value != new_value:
            add_audit_log(
                db, complaint.id, "Complaint status changed",
                old_value=str(old_value), new_value=str(new_value),
            )
        elif field == "final_risk_level" and old_value != new_value:
            add_audit_log(
                db, complaint.id, "Risk manually changed",
                old_value=str(old_value), new_value=str(new_value),
            )
        elif field in tracked and old_value != new_value:
            add_audit_log(
                db, complaint.id, "Complaint edited",
                detail=f"{field} updated", old_value=str(old_value), new_value=str(new_value),
            )
    complaint.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(complaint)
    return complaint


def delete_complaint(db: Session, complaint: Complaint) -> None:
    db.delete(complaint)
    db.commit()


# ---------------- Dashboard ----------------

def dashboard_stats(db: Session) -> dict:
    total = db.execute(select(func.count(Complaint.id))).scalar() or 0
    open_count = db.execute(
        select(func.count(Complaint.id)).where(
            Complaint.status.in_(["New", "Pending Triage", "Open"])
        )
    ).scalar() or 0
    under_investigation = db.execute(
        select(func.count(Complaint.id)).where(Complaint.status == "Under Investigation")
    ).scalar() or 0
    critical_high = db.execute(
        select(func.count(Complaint.id)).where(
            or_(
                Complaint.final_risk_level.in_(["Critical", "High"]),
                Complaint.ai_risk_level.in_(["Critical", "High"]),
            )
        )
    ).scalar() or 0
    closed = db.execute(
        select(func.count(Complaint.id)).where(Complaint.status == "Closed")
    ).scalar() or 0

    resolved = db.execute(
        select(Complaint.created_at, Complaint.resolved_at).where(
            Complaint.resolved_at.isnot(None)
        )
    ).all()
    avg_days = None
    if resolved:
        deltas = [(r.resolved_at - r.created_at).days for r in resolved]
        avg_days = round(sum(deltas) / len(deltas), 1)

    return {
        "total_complaints": int(total),
        "open_complaints": int(open_count),
        "under_investigation": int(under_investigation),
        "critical_high_risk": int(critical_high),
        "closed_complaints": int(closed),
        "avg_resolution_days": avg_days,
    }


def recent_complaints(db: Session, limit: int = 8) -> list[Complaint]:
    stmt = select(Complaint).order_by(Complaint.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


# ---------------- AI assessments / CAPA / audit ----------------

def save_ai_assessment(db: Session, complaint_id: int, result: dict, model_used: str) -> AIAssessment:
    assessment = AIAssessment(
        complaint_id=complaint_id,
        completeness_score=(result.get("completeness") or {}).get("score"),
        risk_level=(result.get("risk_assessment") or {}).get("overall_risk"),
        risk_confidence=(result.get("risk_assessment") or {}).get("confidence"),
        risk_reasoning=result.get("risk_assessment"),
        root_cause_suggestions=result.get("root_cause_analysis"),
        capa_recommendations=result.get("capa_recommendations"),
        duplicate_matches=result.get("duplicate_matches"),
        model_used=model_used,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def add_capa_action(db: Session, complaint_id: int, action_type: str, description: str, source: str) -> CapaAction:
    action = CapaAction(
        complaint_id=complaint_id, action_type=action_type, description=description, source=source
    )
    db.add(action)
    add_audit_log(db, complaint_id, "CAPA added", detail=f"{action_type}: {description[:120]}")
    db.commit()
    db.refresh(action)
    return action


def add_audit_log(
    db: Session,
    complaint_id: int,
    event_type: str,
    *,
    detail: str | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
    actor: str = "quality.user",
) -> AuditLog:
    log = AuditLog(
        complaint_id=complaint_id,
        event_type=event_type,
        detail=detail,
        old_value=old_value,
        new_value=new_value,
        actor=actor,
    )
    db.add(log)
    return log

"""Deterministic complaint number generation: CC-<year>-<seq:04d>."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint


def generate_complaint_number(db: Session) -> str:
    year = datetime.now().year
    prefix = f"CC-{year}-"
    last = db.execute(
        select(func.max(Complaint.complaint_number)).where(
            Complaint.complaint_number.like(f"{prefix}%")
        )
    ).scalar()
    seq = int(last.rsplit("-", 1)[1]) + 1 if last else 1
    return f"{prefix}{seq:04d}"

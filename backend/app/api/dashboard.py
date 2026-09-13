from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import complaint_repo as repo
from app.schemas.complaint import ComplaintOut, DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db)):
    return repo.dashboard_stats(db)


@router.get("/recent", response_model=list[ComplaintOut])
def recent(db: Session = Depends(get_db)):
    return repo.recent_complaints(db, limit=8)

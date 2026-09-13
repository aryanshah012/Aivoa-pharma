"""Seed the database with 8 realistic demo complaints. Idempotent.

Run from backend/:  python seed.py
"""
import json
from pathlib import Path

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.complaint import Complaint

_HERE = Path(__file__).resolve().parent
# Works locally (backend/ → project root → sample_data) and
# in Docker (WORKDIR /app → ./sample_data copied alongside seed.py)
_CANDIDATE_LOCAL = _HERE.parent / "sample_data" / "seed" / "seed_complaints.json"
_CANDIDATE_DOCKER = _HERE / "sample_data" / "seed" / "seed_complaints.json"
SEED_PATH = _CANDIDATE_LOCAL if _CANDIDATE_LOCAL.exists() else _CANDIDATE_DOCKER


def seed() -> None:
    init_db()
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        for row in data:
            exists = db.query(Complaint).filter_by(complaint_number=row["complaint_number"]).first()
            if not exists:
                db.add(Complaint(**row))
        db.commit()
        print(f"Seed complete: {db.query(Complaint).count()} complaints in database.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

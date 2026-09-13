"""Seed the database with 8 realistic demo complaints. Idempotent.

Run from backend/:  python seed.py
"""
import json
from pathlib import Path

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.complaint import Complaint

SEED_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "seed" / "seed_complaints.json"


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

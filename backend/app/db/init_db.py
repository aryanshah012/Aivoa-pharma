"""Create all tables. Run as `python -m app.db.init_db` from backend/.

For production schema migrations use Alembic (`alembic init` + autogenerate).
The model set is intentionally stable for this project, so create_all is
used for dev/bootstrap and Alembic for production evolution.
"""
from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401  (ensures models are registered on Base.metadata)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized.")

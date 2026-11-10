"""Database session helper for OncoAgent backend."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database.models import Base, init_db


def get_engine():
    """Create and return the database engine."""
    db_url = os.getenv(
        "DATABASE_URL",
        str(__import__("pathlib").Path(__file__).parent.parent.parent / "oncoagent.db")
    )
    return create_engine(db_url, echo=False, pool_pre_ping=True)


def get_session():
    """Return a new database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def init_db_command():
    """Initialize the database (run once)."""
    engine = get_engine()
    init_db(engine)
    print(f"✅ Database initialized at engine URL")


# Auto-init if this module is imported directly
if __name__ == "__main__":
    init_db_command()
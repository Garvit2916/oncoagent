"""Database models for OncoAgent backend."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime


Base = declarative_base()


class AnalysisHistory(Base):
    """Store analysis history for patient records."""
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(64), index=True, nullable=True)
    session_id = Column(String(64), index=True, nullable=True)
    
    # Input data
    imaging_findings = Column(Text, nullable=True)  # JSON string
    symptom_findings = Column(Text, nullable=True)  # JSON string
    literature_findings = Column(Text, nullable=True)  # JSON string
    
    # Output data
    overall_risk = Column(Float, nullable=True)
    risk_level = Column(String(20), nullable=True)
    suspicion_index = Column(String(20), nullable=True)
    summary = Column(Text, nullable=True)
    critical_alerts = Column(Text, nullable=True)  # JSON string
    recommended_next_steps = Column(Text, nullable=True)  # JSON string
    doctors_to_consult = Column(Text, nullable=True)  # JSON string
    medications_info = Column(Text, nullable=True)  # JSON string
    
    # Metadata
    overall_confidence = Column(Float, nullable=True)
    agent_agreement = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# Engine and session factory
def create_db_engine():
    """Create SQLAlchemy engine."""
    db_url = "sqlite:///backend/oncoagent.db" if __import__("os").path.exists("backend/oncoagent.db") else "sqlite:///:memory:"
    return create_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
    )


def create_session_local(engine):
    """Create session local."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine=None):
    """Initialize database (create all tables)."""
    if engine is None:
        engine = create_db_engine()
    Base.metadata.create_all(bind=engine)
    return engine, create_session_local(engine)


# Convenience function
def get_db_session(db_url: str | None = None) -> Session:
    """Get a database session."""
    import os
    url = db_url or os.getenv("DATABASE_URL", "sqlite:///backend/oncoagent.db")
    engine = create_engine(url, echo=False, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
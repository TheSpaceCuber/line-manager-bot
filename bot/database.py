# bot/database.py
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ----------------------------------------------------------------
# MODELS
# ----------------------------------------------------------------

class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    poll_message_id = Column(String, nullable=True)  # Telegram poll message ID
    notes = Column(String, nullable=True)

    attendances = relationship("Attendance", back_populates="session")

    def __repr__(self):
        return f"<TrainingSession(id={self.id}, date={self.date.date()})>"


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"))
    telegram_handle = Column(String, index=True)
    present = Column(Boolean, default=True)
    source = Column(String, default="poll")  # e.g., "poll", "manual"
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("TrainingSession", back_populates="attendances")

    def __repr__(self):
        return (
            f"<Attendance(handle={self.telegram_handle}, "
            f"session={self.session_id}, present={self.present})>"
        )


# ----------------------------------------------------------------
# DB UTILITIES
# ----------------------------------------------------------------

def init_db():
    """Create all tables (idempotent)."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Provide a session context (e.g. inside a FastAPI or bot handler)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

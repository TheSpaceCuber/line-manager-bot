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
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///local.db")

engine = create_engine(DATABASE_URL, echo=False, future=True)
logger.info(f"Database engine created. Connected to: {DATABASE_URL}")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ----------------------------------------------------------------
# MODELS
# ----------------------------------------------------------------
class Absentee(Base):
    __tablename__ = "absentees"

    id = Column(Integer, primary_key=True)
    telegram_handle = Column(String, index=True)
    poll_message_id = Column(String, index=True)

    def __repr__(self):
        return (            
            f"<Absentee(telegram_handle={self.telegram_handle}, "
            f"poll_message_id={self.poll_message_id})"
        )
    
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

from datetime import datetime, timedelta

def get_or_create_sessions(db):
    """Get or create TrainingSession for next Thu and Sat."""
    today = datetime.now(timezone.utc).date()
    weekday = today.weekday()
    # Find next Thursday (weekday=3) and Saturday (weekday=5)
    days_until_thu = (3 - weekday) % 7
    days_until_sat = (5 - weekday) % 7
    thu_date = today + timedelta(days=days_until_thu)
    sat_date = today + timedelta(days=days_until_sat)

    thu_session = db.query(TrainingSession).filter(
        TrainingSession.date >= datetime(thu_date.year, thu_date.month, thu_date.day),
        TrainingSession.date < datetime(thu_date.year, thu_date.month, thu_date.day) + timedelta(days=1)
    ).first()
    if not thu_session:
        thu_session = TrainingSession(date=datetime(thu_date.year, thu_date.month, thu_date.day, 19, 30), notes="Thu 730pm @ YCK")
        db.add(thu_session)
        db.commit()
        db.refresh(thu_session)

    sat_session = db.query(TrainingSession).filter(
        TrainingSession.date >= datetime(sat_date.year, sat_date.month, sat_date.day),
        TrainingSession.date < datetime(sat_date.year, sat_date.month, sat_date.day) + timedelta(days=1)
    ).first()
    if not sat_session:
        sat_session = TrainingSession(date=datetime(sat_date.year, sat_date.month, sat_date.day, 9, 45), notes="Sat 945am")
        db.add(sat_session)
        db.commit()
        db.refresh(sat_session)

    return {"Thu": thu_session.id, "Sat": sat_session.id}

def init_db():
    """Create all tables (idempotent)."""
    Base.metadata.create_all(bind=engine)

# Call this once at startup
init_db()

def get_db():
    """Provide a session context (e.g. inside a FastAPI or bot handler)."""
    db = SessionLocal()
    logger.info("Database session started.")
    try:
        yield db
    finally:
        logger.info("Database session closed.")
        db.close()

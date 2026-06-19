import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    String,
    create_engine,
)
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.config import settings

Base = declarative_base()


class Card(Base):
    __tablename__ = "cards"

    card_id = Column(String, primary_key=True)
    person_id = Column(String, nullable=False)
    person_name = Column(String, nullable=False)
    person_type = Column(Enum("student", "staff", "guest", name="person_type"), nullable=False)
    status = Column(Enum("active", "expired", "blocked", name="card_status"), nullable=False)
    expired_at = Column(DateTime, nullable=True)


class AccessLog(Base):
    __tablename__ = "access_logs"

    event_id = Column(String, primary_key=True)
    card_id = Column(String, nullable=False)
    person_id = Column(String, nullable=True)
    person_name = Column(String, nullable=True)
    person_type = Column(String, nullable=True)
    gate_id = Column(String, nullable=False)
    direction = Column(String, nullable=False)
    access_granted = Column(Boolean, nullable=False)
    reason = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(Enum("COMPLETED", "CANCELLED", name="access_status"), nullable=False, default="COMPLETED")


class PendingEvent(Base):
    __tablename__ = "pending_events"

    id = Column(String, primary_key=True, default=lambda: uuid4().hex)
    payload = Column(String, nullable=False) # JSON encoded
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    synced = Column(Boolean, nullable=False, default=False)
    synced_at = Column(DateTime, nullable=True)


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def generate_event_id() -> str:
    now = datetime.now(timezone.utc)
    return f"acc-{now.strftime('%Y%m%d')}-{uuid4().hex[:8]}"


def seed_cards(db: Session):
    """Đọc dữ liệu từ file CSV để nạp vào whitelist."""
    import csv
    import os
    
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "AccessGate_uid_whitelist.csv")
    if not os.path.exists(csv_path):
        return

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row.get("uid")
                student_id = row.get("student_id")
                full_name = row.get("full_name")
                
                if uid and student_id:
                    # Check if exists
                    existing = db.query(Card).filter(Card.card_id == uid).first()
                    if not existing:
                        card = Card(
                            card_id=uid,
                            person_id=student_id,
                            person_name=full_name,
                            person_type="student",
                            status="active",
                            expired_at=None,
                        )
                        db.add(card)
            db.commit()
            logging.getLogger(__name__).info("Seeded cards from CSV successfully")
    except Exception as e:
        logging.getLogger(__name__).error("Error seeding cards from CSV: %s", e)

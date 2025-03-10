from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime,timezone
from app.db.base import Base

class HealthDiary(Base):
    __tablename__ = "health_diary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    symptoms = Column(String, nullable=True)
    mood = Column(String, nullable=True)
    notes = Column(String, nullable=True)

    user = relationship("User", back_populates="health_diary_entries")

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

class HealthDiary(Base):
    __tablename__ = "health_diary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    health_metrics = Column(JSON, nullable=True)  
    symptoms = Column(JSON, nullable=True)  
    mood = Column(Integer, nullable=True)  
    notes = Column(String, nullable=True)

    user = relationship("User", back_populates="health_diary_entries")

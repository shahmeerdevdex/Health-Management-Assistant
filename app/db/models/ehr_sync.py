from sqlalchemy import Column, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class EHRRecord(Base):
    __tablename__ = "ehr_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    medical_history = Column(JSON, nullable=False, default=[])
    last_synced = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="ehr_record")

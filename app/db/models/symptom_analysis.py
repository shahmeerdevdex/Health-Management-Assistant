from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class SymptomAnalysis(Base):
    __tablename__ = "symptom_analysis"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symptoms = Column(String, nullable=False)
    analysis_result = Column(String, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

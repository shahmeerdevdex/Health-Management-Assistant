from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    sent_at = Column(DateTime, default=lambda: datetime.utcnow().replace(tzinfo=None))  #  Fix: Ensure naive datetime

    user = relationship("User", back_populates="notifications")  #  Fix: Improved relationship handling

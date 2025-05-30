from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class VaccinationRecord(Base):
    __tablename__ = "vaccination_records"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    vaccine_name = Column(String, nullable=False)
    dose_number = Column(Integer, nullable=False)
    date_administered = Column(Date, nullable=False)
    healthcare_provider = Column(String, nullable=False)
    next_due_date = Column(Date, nullable=True)  # Next scheduled dose, if applicable
    user_email = Column(String, nullable=True)  # Optional: Email for reminders
    user_phone = Column(String, nullable=True)  # Optional: Phone number for SMS reminders
    reminder_sent = Column(Boolean, default=False)  # Tracks if reminder has been sent
    synced_with_national = Column(Boolean, default=False)  # Tracks if record is synced with national database

    # Relationship with User
    user = relationship("User", back_populates="vaccination_records")

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
import enum

# Enum for referral status
class ReferralStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"

# Referral table model
class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"))
    from_practitioner_id = Column(Integer, ForeignKey("practitioners.id"))
    to_practitioner_id = Column(Integer, ForeignKey("practitioners.id"))
    reason = Column(String, nullable=False)
    notes = Column(String)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("User", foreign_keys=[patient_id])
    from_practitioner = relationship("Practitioner", foreign_keys=[from_practitioner_id])
    to_practitioner = relationship("Practitioner", foreign_keys=[to_practitioner_id])

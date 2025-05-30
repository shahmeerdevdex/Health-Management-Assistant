from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base
from app.schemas.referral_system import ReferralStatus, ReferralPriority, SpecialistType

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    from_practitioner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_practitioner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    specialist_type = Column(SQLEnum(SpecialistType), nullable=False)
    reason = Column(Text, nullable=False)
    priority = Column(SQLEnum(ReferralPriority), default=ReferralPriority.ROUTINE)
    notes = Column(Text)
    status = Column(SQLEnum(ReferralStatus), default=ReferralStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    appointment_date = Column(DateTime)
    feedback = Column(Text)
    medical_history_required = Column(Boolean, default=True)
    test_results_required = Column(Boolean, default=True)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], back_populates="received_referrals")
    from_practitioner = relationship("User", foreign_keys=[from_practitioner_id], back_populates="sent_referrals")
    to_practitioner = relationship("User", foreign_keys=[to_practitioner_id], back_populates="received_referrals")
    documents = relationship("ReferralDocument", back_populates="referral", cascade="all, delete-orphan")
    history = relationship("ReferralHistory", back_populates="referral", cascade="all, delete-orphan")


class ReferralDocument(Base):
    __tablename__ = "referral_documents"

    id = Column(Integer, primary_key=True, index=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"), nullable=False)
    document_url = Column(String, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    document_type = Column(String)  # e.g., "MEDICAL_REPORT", "TEST_RESULT", "IMAGING"
    description = Column(Text)

    # Relationships
    referral = relationship("Referral", back_populates="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])


class ReferralHistory(Base):
    __tablename__ = "referral_history"

    id = Column(Integer, primary_key=True, index=True)
    referral_id = Column(Integer, ForeignKey("referrals.id"), nullable=False)
    action = Column(String, nullable=False)  # e.g., "CREATED", "STATUS_CHANGED", "DOCUMENT_ATTACHED"
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(Text)

    # Relationships
    referral = relationship("Referral", back_populates="history")
    performer = relationship("User", foreign_keys=[performed_by]) 
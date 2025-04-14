from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date
from app.db.base import Base
from sqlalchemy import Boolean, DateTime
from enum import Enum
from sqlalchemy import Enum as SqlEnum

class VerificationStatusEnum(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class InsurancePlan(Base):
    __tablename__ = "insurance_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider_name = Column(String, nullable=False)
    policy_number = Column(String, unique=True, nullable=False)
    coverage_start = Column(Date, nullable=False)
    coverage_end = Column(Date, nullable=False)
    deductible = Column(Integer, nullable=True)
    premium_amount = Column(Integer, nullable=True)
    is_verified = Column(Boolean, default=False)
    verification_status = Column(SqlEnum(VerificationStatusEnum), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="insurance_plans")

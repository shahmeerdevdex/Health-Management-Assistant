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
    out_of_pocket_costs = relationship("OutOfPocketCost", back_populates="insurance_plan", cascade="all, delete-orphan")
    medicare_claims = relationship("MedicareClaim", back_populates="insurance_plan", cascade="all, delete-orphan")
    coverage_details = relationship("InsuranceCoverageDetail", back_populates="insurance_plan", cascade="all, delete-orphan")


class OutOfPocketCost(Base):
    __tablename__ = "out_of_pocket_costs"

    id = Column(Integer, primary_key=True, index=True)
    insurance_plan_id = Column(Integer, ForeignKey("insurance_plans.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=True)

    insurance_plan = relationship("InsurancePlan", back_populates="out_of_pocket_costs")


class MedicareClaim(Base):
    __tablename__ = "medicare_claims"

    id = Column(Integer, primary_key=True, index=True)
    insurance_plan_id = Column(Integer, ForeignKey("insurance_plans.id"), nullable=False)
    claim_id = Column(String, unique=True, nullable=False)
    claim_date = Column(Date, nullable=False)
    claim_amount = Column(Integer, nullable=False)

    insurance_plan = relationship("InsurancePlan", back_populates="medicare_claims")


class InsuranceCoverageDetail(Base):
    __tablename__ = "insurance_coverage_details"

    id = Column(Integer, primary_key=True, index=True)
    insurance_plan_id = Column(Integer, ForeignKey("insurance_plans.id"), nullable=False)
    coverage_type = Column(String, nullable=False)
    benefits = Column(String, nullable=True)
    exclusions = Column(String, nullable=True)

    insurance_plan = relationship("InsurancePlan", back_populates="coverage_details")
